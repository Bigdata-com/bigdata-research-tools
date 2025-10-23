"""
Module for executing concurrent and rate-limited searches via
the Bigdata client.

This module defines a `RateLimitedSearchManager` class to manage multiple
search requests efficiently while respecting request-per-minute (RPM) limits
of the Bigdata API.
"""

import itertools
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Literal, Union, overload

from bigdata_client import Bigdata
from bigdata_client.daterange import AbsoluteDateRange, RollingDateRange
from bigdata_client.document import Document
from bigdata_client.models.advanced_search_query import QueryComponent
from bigdata_client.models.search import DocumentType, SortBy
from tqdm import tqdm

from bigdata_research_tools.client import bigdata_connection, init_bigdata_client
from bigdata_research_tools.tracing import (
    ReportSearchUsageTraceEvent,
    WorkflowStatus,
    WorkflowTraceEvent,
    send_trace,
)

INPUT_DATE_RANGE = Union[
    tuple[datetime, datetime],
    RollingDateRange,
    list[tuple[datetime, datetime] | RollingDateRange],
]
SEARCH_QUERY_RESULTS_TYPE = dict[
    tuple[QueryComponent, Union[AbsoluteDateRange, RollingDateRange]], list[Document]
]

REQUESTS_PER_MINUTE_LIMIT = 300
MAX_WORKERS = 4


class SearchManager:
    """
    Rate-limited search executor for managing concurrent searches via
    the Bigdata SDK.

    This class implements a token bucket algorithm for rate limiting and
    provides thread-safe access to the search functionality.
    """

    def __init__(
        self,
        rpm: int = REQUESTS_PER_MINUTE_LIMIT,
        bucket_size: int | None = None,
        bigdata: Bigdata | None = None,
        **kwargs,
    ):
        """
        Initialize the rate-limited search manager.

        :param rpm:
            Queries per minute limit. Defaults to 300.
        :param bucket_size:
            Size of the token bucket. Defaults to the value of `rpm`.
        :param bigdata:
            The Bigdata SDK client instance used for executing searches.
            Defaults to None (uses the library default client).
        """
        self.bigdata = bigdata or init_bigdata_client()
        self.rpm = rpm
        self.bucket_size = bucket_size or rpm
        self.tokens = self.bucket_size
        self.last_refill = time.time()
        self._lock = threading.Lock()
        self._quota_lock = threading.Lock()
        self.quota_consumed = 0

    def _refill_tokens(self):
        """
        Refill tokens based on elapsed time since the last refill.
        Tokens are replenished at a rate proportional to the RPM limit.
        """
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = int(elapsed * (self.rpm / 60.0))

        if new_tokens > 0:
            with self._lock:
                self.tokens = min(self.bucket_size, self.tokens + new_tokens)
                self.last_refill = now

    def _acquire_token(self, timeout: float | None = None) -> bool:
        """
        Attempt to acquire a token for executing a search request.

        :param timeout:
            Maximum time (in seconds) to wait for a token.
            Defaults to no timeout.
        :return:
            True if a token is acquired, False if timed out.
        """
        start = time.time()
        while True:
            self._refill_tokens()

            with self._lock:
                if self.tokens > 0:
                    self.tokens -= 1
                    return True

            if timeout and (time.time() - start) > timeout:
                return False

            time.sleep(0.1)  # Prevent tight looping

    def _search(
        self,
        query: QueryComponent,
        date_range: tuple[datetime, datetime] | RollingDateRange,
        sortby: SortBy = SortBy.RELEVANCE,
        scope: DocumentType = DocumentType.ALL,
        limit: int = 10,
        timeout: float | None = None,
        rerank_threshold: float | None = None,
        **kwargs,
    ) -> list[Document] | None:
        """
        Execute a single search with rate limiting.

        :param query:
            The search query to execute.
        :param date_range:
            A date range filter for the search results.
        :param sortby:
            The sorting criterion for the search results.
            Defaults to SortBy.RELEVANCE.
        :param scope:
            The scope of the documents to include.
            Defaults to DocumentType.ALL.
        :param limit:
            The maximum number of documents to return.
            Defaults to 10.
        :param timeout:
            The maximum time (in seconds) to wait for a token.
        :param rerank_threshold:
            Enable the cross-encoder by setting value between [0,1]
        :return:
            A list of search results.
        """
        if not self._acquire_token(timeout):
            logging.warning("Timed out attempting to acquire rate limit token")
            return None

        date_filter: AbsoluteDateRange | RollingDateRange

        if date_range and isinstance(date_range, tuple):
            date_filter = AbsoluteDateRange(
                start=date_range[0],
                end=date_range[1],
            )
        else:
            date_filter = date_range

        try:
            query_obj = self.bigdata.search.new(
                query=query,
                date_range=date_filter,
                sortby=sortby,
                scope=scope,
                rerank_threshold=rerank_threshold,
            )
            results = query_obj.run(limit=limit)
            with self._quota_lock:
                self.quota_consumed += query_obj.get_usage()
            return results
        except Exception as e:
            raise e
            logging.error(f"Search error: {e}")
            return None

    def concurrent_search(
        self,
        queries: list[QueryComponent],
        date_ranges: list[tuple[datetime, datetime] | RollingDateRange],
        sortby: SortBy = SortBy.RELEVANCE,
        scope: DocumentType = DocumentType.ALL,
        limit: int = 10,
        max_workers: int = MAX_WORKERS,
        timeout: float | None = None,
        rerank_threshold: float | None = None,
        **kwargs,
    ) -> SEARCH_QUERY_RESULTS_TYPE:
        """
        Execute multiple searches concurrently while respecting rate limits.
        The order of results is preserved based on the input queries.

        :param queries:
            A list of QueryComponent objects.
        :param date_ranges:
            Date range filter for all searches.
        :param sortby:
            The sorting criterion for the search results.
            Defaults to SortBy.RELEVANCE.
        :param scope:
            The scope of the documents to include.
            Defaults to DocumentType.ALL.
        :param limit:
            The maximum number of documents to return per query.
            Defaults to 10.
        :param max_workers:
            The maximum number of concurrent threads.
            Defaults to MAX_WORKERS.
        :param timeout:
            The maximum time (in seconds) to wait for a token
            per request.
        :param rerank_threshold:
            Enable the cross-encoder by setting value between [0,1]
        :return:
            A mapping of the tuple of search query and date range
            to the list of the corresponding search results.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._search,
                    query=query,
                    date_range=date_range,
                    sortby=sortby,
                    scope=scope,
                    limit=limit,
                    timeout=timeout,
                    rerank_threshold=rerank_threshold,
                    **kwargs,
                ): (query, date_range)
                for query, date_range in itertools.product(queries, date_ranges)
            }

            for future in tqdm(
                as_completed(futures), total=len(futures), desc="Querying Bigdata..."
            ):
                query, date_range = futures[future]
                try:
                    results[(query, date_range)] = future.result()
                except Exception as e:
                    raise e
                    logging.error(f"Error in search {query, date_range}: {e}")

        return results

    def get_quota_consumed(self) -> float:
        """
        Get the total query units consumed during searches.

        :return:
            The total query units consumed.
        """
        with self._quota_lock:
            return self.quota_consumed


def normalize_date_range(
    date_ranges: INPUT_DATE_RANGE,
) -> list[tuple[datetime, datetime] | RollingDateRange]:
    if not isinstance(date_ranges, list):
        date_ranges = [date_ranges]

    return date_ranges


RUN_SEARCH_NAME: str = "RunSearch"


@overload
def run_search(
    queries: list[QueryComponent],
    date_ranges: INPUT_DATE_RANGE,
    sortby: SortBy = SortBy.RELEVANCE,
    scope: DocumentType = DocumentType.ALL,
    limit: int = 10,
    only_results: Literal[False] = False,
    rerank_threshold: float | None = None,
    **kwargs,
) -> SEARCH_QUERY_RESULTS_TYPE: ...


@overload
def run_search(
    queries: list[QueryComponent],
    date_ranges: INPUT_DATE_RANGE,
    sortby: SortBy = SortBy.RELEVANCE,
    scope: DocumentType = DocumentType.ALL,
    limit: int = 10,
    only_results: Literal[True] = True,
    rerank_threshold: float | None = None,
    **kwargs,
) -> list[list[Document]]: ...


def run_search(
    queries: list[QueryComponent],
    date_ranges: INPUT_DATE_RANGE,
    sortby: SortBy = SortBy.RELEVANCE,
    scope: DocumentType = DocumentType.ALL,
    limit: int = 10,
    only_results: bool = True,
    rerank_threshold: float | None = None,
    workflow_name: str = RUN_SEARCH_NAME,
    **kwargs,
) -> SEARCH_QUERY_RESULTS_TYPE | list[list[Document]]:
    """
    Execute multiple searches concurrently using the Bigdata client, with rate limiting.

    Args:
        queries (list[QueryComponent]): A list of QueryComponent objects.
        date_ranges (Union[tuple[datetime, datetime], RollingDateRange, list[tuple[datetime, datetime] | RollingDateRange],]):
            Date range filter for the search results.
        sortby (SortBy): The sorting criterion for the search results. Defaults to SortBy.RELEVANCE.
        scope (DocumentType): The scope of the documents to include. Defaults to DocumentType.ALL.
        limit (int): The maximum number of documents to return per query. Defaults to 10.
        only_results (bool): If True, return only the search results.
            If False, return the queries along with the results.
            Defaults to True.
        rerank_threshold (Optional[float]): The threshold for reranking the search results.
            See https://sdk.bigdata.com/en/latest/how_to_guides/rerank_search.html.
    Returns:
        Union[Dict[Tuple[QueryComponent, Union[AbsoluteDateRange, RollingDateRange]], List[Document]], list[list[Document]], list[dict]]:
        If `only_results` is True, returns the list of search results.

        If `only_results` is False, returns a mapping of the tuple of search query and date range to
        the list of the corresponding search results.
    """
    date_ranges = normalize_date_range(date_ranges)
    date_ranges.sort(key=lambda x: x[0])

    workflow_start = datetime.now()
    workflow_status = WorkflowStatus.UNKNOWN
    manager = None
    try:
        manager = SearchManager(**kwargs)
        query_results = manager.concurrent_search(
            queries=queries,
            date_ranges=date_ranges,
            sortby=sortby,
            scope=scope,
            limit=limit,
            rerank_threshold=rerank_threshold,
            **kwargs,
        )

        workflow_status = WorkflowStatus.SUCCESS
    except BaseException:
        workflow_status = WorkflowStatus.FAILED
        raise
    finally:
        start_date = "Unknown"
        end_date = "Unknown"
        try:
            # We only know the exact start and end date if date_ranges is a list of tuples
            # With rolling date ranges we cannot determine the exact dates or if empty list
            if date_ranges and all(isinstance(dr, tuple) for dr in date_ranges):
                start_date = date_ranges[0][0]
                end_date = date_ranges[-1][1]
                if isinstance(start_date, datetime):
                    start_date = start_date.isoformat()
                if isinstance(end_date, datetime):
                    end_date = end_date.isoformat()


            if manager:
                send_trace(
                    bigdata_connection(),
                    ReportSearchUsageTraceEvent(
                        workflow_name=workflow_name,
                        document_type=scope.value,
                        start_date=start_date,
                        end_date=end_date,
                        query_units=manager.get_quota_consumed(),
                    ),
                )
        except Exception:
            # Failed to send trace event, however in a try - finally block we should not raise exceptions
            pass
        if workflow_name == RUN_SEARCH_NAME:
            send_trace(
                bigdata_connection(),
                WorkflowTraceEvent(
                    name=workflow_name,
                    start_date=workflow_start,
                    end_date=datetime.now(),
                    llm_model=None,
                    status=workflow_status,
                ),
            )

    if only_results:
        return list(query_results.values())
    return query_results

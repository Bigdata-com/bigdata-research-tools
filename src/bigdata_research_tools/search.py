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
from typing import Tuple, List, Dict, Optional, Union

from bigdata_client import Bigdata
from bigdata_client.daterange import AbsoluteDateRange, RollingDateRange
from bigdata_client.document import Document
from bigdata_client.models.advanced_search_query import QueryComponent
from bigdata_client.models.search import DocumentType, SortBy

DATE_RANGE_TYPE = Union[
    AbsoluteDateRange,
    RollingDateRange,
    List[Union[AbsoluteDateRange, RollingDateRange]]
]
SEARCH_QUERY_RESULTS_TYPE = Dict[
    Tuple[QueryComponent, Union[AbsoluteDateRange, RollingDateRange]],
    List[Document]
]

REQUESTS_PER_MINUTE_LIMIT = 300
MAX_WORKERS = 4


class RateLimitedSearchManager:
    """
    Rate-limited search executor for managing concurrent searches via
    the Bigdata SDK.

    This class implements a token bucket algorithm for rate limiting and
    provides thread-safe access to the search functionality.
    """

    def __init__(self,
                 bigdata: Bigdata,
                 rpm: int = REQUESTS_PER_MINUTE_LIMIT,
                 bucket_size: int = None):
        """
        Initialize the rate-limited search manager.

        :param bigdata:
            The Bigdata SDK client instance used for executing searches.
        :param rpm:
            Queries per minute limit. Defaults to 300.
        :param bucket_size:
            Size of the token bucket. Defaults to the value of `rpm`.
        """
        self.bigdata = bigdata
        self.rpm = rpm
        self.bucket_size = bucket_size or rpm
        self.tokens = self.bucket_size
        self.last_refill = time.time()
        self._lock = threading.Lock()

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

    def _acquire_token(self, timeout: float = None) -> bool:
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
            date_range: Union[AbsoluteDateRange, RollingDateRange] = None,
            sortby: SortBy = SortBy.RELEVANCE,
            scope: DocumentType = DocumentType.ALL,
            limit: int = 10,
            timeout: float = None
    ) -> Optional[List[Document]]:
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
        :return:
            A list of search results, or None if a rate limit timeout occurred.
        """
        if not self._acquire_token(timeout):
            logging.warning('Timed out attempting to acquire rate limit token')
            return None

        if isinstance(date_range, tuple):
            date_range = AbsoluteDateRange(*date_range)

        try:
            results = self.bigdata.search.new(
                query=query,
                date_range=date_range,
                sortby=sortby,
                scope=scope
            ).run(limit=limit)
            return results
        except Exception as e:
            logging.error(f'Search error: {e}')
            return None

    def concurrent_search(
            self,
            queries: List[QueryComponent],
            date_ranges: DATE_RANGE_TYPE = None,
            sortby: SortBy = SortBy.RELEVANCE,
            scope: DocumentType = DocumentType.ALL,
            limit: int = 10,
            max_workers: int = MAX_WORKERS,
            timeout: float = None
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
        :return:
            A mapping of the tuple of search query and date range
            to the list of the corresponding search results.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._search,
                                query=query,
                                date_range=date_range,
                                sortby=sortby,
                                scope=scope,
                                limit=limit,
                                timeout=timeout): (query, date_range)
                for query, date_range in
                itertools.product(queries, date_ranges)
            }

            for future in as_completed(futures):
                query, date_range = futures[future]
                try:
                    # Store the search results in the dictionary,
                    # Even if the search result is empty.
                    results[(query, date_range)] = future.result()
                except Exception as e:
                    logging.error(f'Error in search {query, date_range}: {e}')

        return results


def normalize_date_range(date_ranges: DATE_RANGE_TYPE) -> DATE_RANGE_TYPE:
    if not isinstance(date_ranges, list):
        date_ranges = [date_ranges]

    # Convert mutable AbsoluteDateRange into hashable objects
    for i, dr in enumerate(date_ranges):
        if isinstance(dr, AbsoluteDateRange):
            date_ranges[i] = (dr.start_dt, dr.end_dt)
    return date_ranges


def run_search(
        bigdata: Bigdata,
        queries: List[QueryComponent],
        date_ranges: DATE_RANGE_TYPE = None,
        sortby: SortBy = SortBy.RELEVANCE,
        scope: DocumentType = DocumentType.ALL,
        limit: int = 10,
) -> SEARCH_QUERY_RESULTS_TYPE:
    """
    Convenience function to execute multiple searches concurrently
    with rate limiting.
    This function creates an instance of `RateLimitedSearchManager`
    and utilizes it to run searches for all provided queries.

    :param bigdata:
        An instance of the Bigdata client used to execute the searches.
    :param queries:
        A list of QueryComponent objects.
    :param date_ranges:
        Date range filter for the search results.
    :param sortby:
        The sorting criterion for the search results.
        Defaults to SortBy.RELEVANCE.
    :param scope:
        The scope of the documents to include.
        Defaults to DocumentType.ALL.
    :param limit:
        The maximum number of documents to return per query.
        Defaults to 10.
    :return:
        A mapping of the tuple of search query and date range
        to the list of the corresponding search results.
    """
    manager = RateLimitedSearchManager(bigdata)
    date_ranges = normalize_date_range(date_ranges)
    return manager.concurrent_search(
        queries=queries,
        date_ranges=date_ranges,
        sortby=sortby,
        scope=scope,
        limit=limit,
    )

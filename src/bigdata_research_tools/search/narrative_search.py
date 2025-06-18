from itertools import chain
from logging import Logger, getLogger
from typing import List, Optional

from bigdata_client.document import Document
from bigdata_client.models.search import DocumentType, SortBy
from pandas import DataFrame
from tqdm import tqdm

from bigdata_research_tools.search.query_builder import (
    EntitiesToSearch,
    build_batched_query,
    create_date_ranges,
)
from bigdata_research_tools.search.search import run_search

logger: Logger = getLogger(__name__)


def search_narratives(
    sentences: List[str],
    start_date: str,
    end_date: str,
    scope: DocumentType,
    fiscal_year: Optional[int] = None,
    sources: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    control_entities: Optional[List[str]] = None,
    freq: str = "M",
    sort_by: SortBy = SortBy.RELEVANCE,
    rerank_threshold: Optional[float] = None,
    document_limit: int = 50,
    batch_size: int = 10,
    **kwargs,
) -> DataFrame:
    """
    Screen for documents based on the input sentences and other filters.

    Args:
        sentences (List[str]): The list of theme sentences to screen for.
        start_date (str): The start date for the search.
        end_date (str): The end date for the search.
        scope (DocumentType): The document type scope
            (e.g., `DocumentType.NEWS`, `DocumentType.TRANSCRIPTS`).
        fiscal_year (Optional[int]): The fiscal year to filter queries.
            If None, no fiscal year filter is applied.
        sources (Optional[List[str]]): List of sources to filter on. If none, we search across all sources.
        keywords (Optional[List[str]]): A list of keywords for constructing keyword queries.
            If None, no keyword queries are created.
        control_entities (Optional[List[str]]): A list of control entity IDs for creating co-mentions queries.
            If None, no control queries are created.
        freq (str): The frequency of the date ranges. Defaults to 'M'.
        sort_by (SortBy): The sorting criterion for the search results.
            Defaults to SortBy.RELEVANCE.
        rerank_threshold (Optional[float]): The threshold for reranking the search results.
            See https://sdk.bigdata.com/en/latest/how_to_guides/rerank_search.html
        document_limit (int): The maximum number of documents to return per Bigdata query.
        batch_size (int): The number of entities to include in each batched query.

    Returns:
        DataFrame: The DataFrame with the screening results. Schema:
            - Index: int
            - Columns:
                - timestamp_utc: datetime64
                - document_id: str
                - sentence_id: str
                - headline: str
    """

    # If control_entities are provided, create a control EntityConfig
    # For this example, assuming control_entities are all company entities
    control_entities_config = None
    if control_entities:
        control_entities_config = EntitiesToSearch(companies=control_entities)

    # Build batched queries
    batched_query = build_batched_query(
        sentences=sentences,
        keywords=keywords,
        sources=sources,
        control_entities=control_entities_config,
        custom_batches=None,
        entities=None,
        batch_size=batch_size,
        scope=scope,
        fiscal_year=fiscal_year,
    )

    # Create list of date ranges
    date_ranges = create_date_ranges(start_date, end_date, freq)

    no_queries = len(batched_query)
    no_dates = len(date_ranges)
    total_no = no_dates * no_queries

    logger.info(f"About to run {total_no} queries")
    logger.debug("Example Query:", batched_query[0])
    # Run concurrent search
    results = run_search(
        batched_query,
        date_ranges=date_ranges,
        limit=document_limit,
        scope=scope,
        sortby=sort_by,
        rerank_threshold=rerank_threshold,
        **kwargs,
    )

    results = list(chain.from_iterable(results))
    results = _process_narrative_search(results)

    return results


def _process_narrative_search(
    results: List[Document],
) -> DataFrame:
    """
    Build a dataframe for when no companies are specified.

    Args:
        results (List[Document]): A list of Bigdata search results.

    Returns:
        DataFrame: Screening DataFrame. Schema:
        - Index: int
        - Columns:
            - timestamp_utc: datetime64
            - document_id: str
            - sentence_id: str
            - headline: str
            - text: str
    """

    rows = []
    for result in tqdm(results, desc="Processing screening results..."):
        for chunk in result.chunks:
            # Collect all necessary information in the row
            rows.append(
                {
                    "timestamp_utc": result.timestamp,
                    "document_id": result.id,
                    "sentence_id": f"{result.id}-{chunk.chunk}",
                    "headline": result.headline,
                    "text": chunk.text,
                }
            )

    if not rows:
        raise ValueError("No rows to process")

    df = DataFrame(rows).sort_values("timestamp_utc").reset_index(drop=True)

    # Deduplicate by quote text as well
    df = df.drop_duplicates(subset=["timestamp_utc", "document_id", "text"])

    df = df.reset_index(drop=True)
    return df

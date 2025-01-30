"""
Copyright (C) 2025 RavenPack | Bigdata.com. All rights reserved.
Author: Alessandro Bouchs (abouchs@ravenpack.com), Jelena Starovic (jstarovic@ravenpack.com)
"""
from typing import List, Optional, Tuple

import pandas as pd
from bigdata_client.daterange import AbsoluteDateRange
from bigdata_client.models.advanced_search_query import QueryComponent
from bigdata_client.models.search import DocumentType
from bigdata_client.query import Keyword, Entity, Any, Similarity, FiscalYear, \
    ReportingEntity


def build_similarity_queries(sentences: List[str]) -> List[Similarity]:
    """
    Processes a list of sentences to create a list of Similarity query objects, ensuring no duplicates.

    Args:
        sentences (List[str] or str): 
            A list of sentences or a single sentence string. If a single string is provided, 
            it is converted into a list containing that string.

    Returns:
        List[Similarity]: 
            A list of Similarity query objects, one for each unique sentence in the input.
    
    Operation:
        1. Converts a single string input to a list.
        2. Deduplicates the list of sentences.
        3. Creates a Similarity query object for each unique sentence.
    """
    if isinstance(sentences, str):
        sentences = [sentences]

    sentences = list(set(sentences))  # Deduplicate
    queries = [Similarity(sentence) for sentence in sentences]
    return queries


def build_batched_query(
        sentences: Optional[List[str]],
        keywords: Optional[List[str]],
        entity_keys: List[str],
        control_entities: Optional[List[str]],
        batch_size: int = 10,
        fiscal_year: int = None,
        scope: DocumentType = DocumentType.ALL,
) -> List[QueryComponent]:
    """
    Builds a list of batched query objects based on the provided parameters. This function 
    supports multiple query types (Similarity, Keyword, Entity or ReportingEntity) and batches entity keys 
    for processing.

    Args:
        sentences (Optional[List[str]]): 
            A list of sentences for creating similarity queries. If None, no similarity queries are created.
        keywords (Optional[List[str]]): 
            A list of keywords for constructing keyword queries. If None, no keyword queries are created.
        entity_keys (List[str]): 
            A list of entity keys to batch and process.
        control_entities (Optional[List[str]]): 
            A list of control entity IDs for creating co-mentions queries. If None, no control queries are created.
        batch_size (int, optional): 
            The number of entities to include in each batch. Defaults to 10.
        fiscal_year (int, optional): 
            The fiscal year to filter queries. If None, no fiscal year filter is applied.
        scope (DocumentType, optional): 
            The document type scope (e.g., `DocumentType.ALL`, `DocumentType.TRANSCRIPTS`). Defaults to `DocumentType.ALL`.

    Returns:
        List[QueryComponent]: 
            A list of expanded and batched query components, incorporating all provided parameters.

    Operation:
        1. Constructs similarity queries if `sentences` are provided.
        2. Constructs keyword queries if `keywords` are provided.
        3. Constructs control queries if `control_entities` are provided.
        4. Batches `entity_keys` into groups of size `batch_size`.
        5. Combines all query components, including optional filters like fiscal year and scope.
        6. Returns a list of expanded queries, ensuring all combinations are considered.

    Notes:
        - If no `sentences`, `keywords`, or `control_entities` are provided, the function defaults to creating 
          queries based on batched `entity_keys` alone.
        - Fiscal year filtering is applied as an additional constraint if specified.
    """
    queries = []

    # Build similarity queries if sentences are provided
    if sentences:
        queries = build_similarity_queries(sentences)
    else:
        # If sentences are not provided, initialize a default query
        queries = []  # Default base query

    if keywords:
        keyword_query = Any([Keyword(word) for word in keywords])
    else:
        # If sentences are not provided, initialize a default query
        keyword_query = None

    if control_entities:
        control_query = Any(
            [Entity(entity_id) for entity_id in control_entities])
    else:
        # If sentences are not provided, initialize a default query
        control_query = None

        # Batch entity keys
    entity_keys_batched = [
        entity_keys[i:i + batch_size] for i in
        range(0, len(entity_keys), batch_size)] if entity_keys else [None]

    entity_type = ReportingEntity if scope in (
    DocumentType.TRANSCRIPTS, DocumentType.FILINGS) else Entity
    entity_batch_queries = [
        Any([entity_type(entity_key) for entity_key in batch]) for batch in
        entity_keys_batched if batch] if entity_keys_batched else [None]

    queries_expanded = []
    for entity_batch_query in (entity_batch_queries or [None]):
        for base_query in (queries or [None]):
            expanded_query = base_query or None
            # Add entity batch
            if entity_batch_query:
                expanded_query = expanded_query & entity_batch_query if expanded_query else entity_batch_query
                # Add keyword and control queries
            if keyword_query:
                expanded_query = expanded_query & keyword_query if expanded_query else keyword_query
            if control_query:
                expanded_query = expanded_query & control_query if expanded_query else control_query

            # Add fiscal year filter if provided
            if fiscal_year:
                expanded_query = expanded_query & FiscalYear(
                    fiscal_year) if expanded_query else None

            # Append the expanded query to the final list
            queries_expanded.append(expanded_query)

    return queries_expanded


def create_date_intervals(
        start_date: str,
        end_date: str,
        freq: str
) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Generates date intervals based on a specified frequency within a given start and end date range.

    Args:
        start_date (str): 
            The start date in 'YYYY-MM-DD' format.
        end_date (str): 
            The end date in 'YYYY-MM-DD' format.
        freq (str): 
            The frequency for intervals. Supported values:
                - 'Y': Yearly intervals.
                - 'M': Monthly intervals.
                - 'W': Weekly intervals.
                - 'D': Daily intervals.

    Returns:
        List[Tuple[pd.Timestamp, pd.Timestamp]]: 
            A list of tuples, where each tuple contains the start and end timestamp 
            of an interval. The intervals are inclusive of the start and exclusive of the next start.

    Raises:
        ValueError: If the provided frequency is invalid.

    Operation:
        1. Converts the `start_date` and `end_date` strings to `pd.Timestamp` objects.
        2. Adjusts the frequency for yearly ('Y') and monthly ('M') intervals to align with period starts:
           - 'Y' → 'AS' (Year Start).
           - 'M' → 'MS' (Month Start).
        3. Uses `pd.date_range` to generate a range of dates based on the frequency.
        4. Creates tuples representing start and end times for each interval:
           - The start time is set to midnight (00:00:00).
           - The end time is set to the last second of the interval (23:59:59).
        5. Ensures the final interval includes the specified `end_date`.

    Notes:
        - The intervals are inclusive of the start and exclusive of the next start time.
        - For invalid frequencies, a `ValueError` is raised to indicate the issue.
    """
    # Convert start and end dates to pandas Timestamps
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    # Adjust frequency for yearly and monthly to use appropriate start markers
    adjusted_freq = {'Y': 'AS', 'M': 'MS'}.get(freq,
                                               freq)  # 'AS' for year start, 'MS' for month start

    # Generate date range based on the adjusted frequency
    try:
        date_range = pd.date_range(start=start_date, end=end_date,
                                   freq=adjusted_freq)
    except ValueError:
        raise ValueError("Invalid frequency. Use 'Y', 'M', 'W', or 'D'.")

    # Create intervals
    intervals = []
    for i in range(len(date_range) - 1):
        intervals.append(
            (date_range[i].replace(hour=0, minute=0, second=0),
             (date_range[i + 1] - pd.Timedelta(seconds=1)).replace(hour=23,
                                                                   minute=59,
                                                                   second=59))
        )

    # Handle the last range to include the full end_date
    intervals.append((
        date_range[-1].replace(hour=0, minute=0, second=0),
        end_date.replace(hour=23, minute=59, second=59)
    ))

    return intervals


def create_date_ranges(
        start_date: str,
        end_date: str,
        freq: str
) -> List[AbsoluteDateRange]:
    """
    Generates a list of `AbsoluteDateRange` objects based on the specified frequency.

    Args:
        start_date (str): 
            The start date in 'YYYY-MM-DD' format.
        end_date (str): 
            The end date in 'YYYY-MM-DD' format.
        freq (str): 
            The frequency for dividing the date range. Supported values:
                - 'Y': Yearly.
                - 'M': Monthly.
                - 'W': Weekly.
                - 'D': Daily.
    
    Returns:
        List[AbsoluteDateRange]: 
            A list of `AbsoluteDateRange` objects, where each object represents 
            a time range between two dates as determined by the specified frequency.

    Operation:
        1. Calls `create_date_intervals` to generate a list of date intervals.
        2. Converts each interval (start and end tuple) into an `AbsoluteDateRange` object.
        3. Returns a list of these `AbsoluteDateRange` objects.
    """
    intervals = create_date_intervals(start_date, end_date, freq=freq)
    return [AbsoluteDateRange(start, end) for start, end in intervals]

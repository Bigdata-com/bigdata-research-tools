"""
Copyright (C) 2024, RavenPack | Bigdata.com. All rights reserved.
Author: Alessandro Bouchs (abouchs@ravenpack.com), Jelena Starovic (jstarovic@ravenpack.com)
"""
from typing import List, Optional, Union, Tuple
from bigdata_client import Bigdata
from bigdata_client.daterange import AbsoluteDateRange
from bigdata_client.models.advanced_search_query import QueryComponent
from bigdata_client.models.search import DocumentType, SortBy
from bigdata_client.query import Keyword, Entity, Any, Similarity, FiscalYear, ReportingEntity
import pandas as pd

def build_similarity_queries(sentences: List[str]) -> List[Similarity]:
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
        control_query = Any([Entity(entity_id) for entity_id in control_entities])
    else:
        # If sentences are not provided, initialize a default query
        control_query = None

        # Batch entity keys
    entity_keys_batched = [
        entity_keys[i:i + batch_size] for i in range(0, len(entity_keys), batch_size)] if entity_keys else [None]

    entity_type = ReportingEntity if scope in (DocumentType.TRANSCRIPTS, DocumentType.FILINGS) else Entity
    entity_batch_queries = [Any([entity_type(entity_key) for entity_key in batch]) for batch in entity_keys_batched if batch] if entity_keys_batched else [None]
    
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
                expanded_query = expanded_query & FiscalYear(fiscal_year) if expanded_query else None

            # Append the expanded query to the final list
            queries_expanded.append(expanded_query)

    return queries_expanded

def create_date_intervals(
    start_date: str, 
    end_date: str, 
    freq: str
) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Create date intervals for a given frequency.

    Parameters:
    - start_date (str): The start date in 'YYYY-MM-DD' format.
    - end_date (str): The end date in 'YYYY-MM-DD' format.
    - freq (str): Frequency string ('Y' for yearly, 'M' for monthly, 'W' for weekly, 'D' for daily).

    Returns:
    - List[Tuple[pd.Timestamp, pd.Timestamp]]: List of start and end date tuples.
    """
    # Convert start and end dates to pandas Timestamps
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    
    # Adjust frequency for yearly and monthly to use appropriate start markers
    adjusted_freq = {'Y': 'AS', 'M': 'MS'}.get(freq, freq)  # 'AS' for year start, 'MS' for month start
    
    # Generate date range based on the adjusted frequency
    try:
        date_range = pd.date_range(start=start_date, end=end_date, freq=adjusted_freq)
    except ValueError:
        raise ValueError("Invalid frequency. Use 'Y', 'M', 'W', or 'D'.")

    # Create intervals
    intervals = []
    for i in range(len(date_range) - 1):
        intervals.append(
            (date_range[i].replace(hour=0, minute=0, second=0), 
             (date_range[i + 1] - pd.Timedelta(seconds=1)).replace(hour=23, minute=59, second=59))
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
    Create a list of AbsoluteDateRange objects for the given frequency.

    Parameters:
    - start_date (str): The start date in 'YYYY-MM-DD' format.
    - end_date (str): The end date in 'YYYY-MM-DD' format.
    - freq (str): Frequency string ('Y' for yearly, 'M' for monthly, 'W' for weekly, 'D' for daily).

    Returns:
    - List[AbsoluteDateRange]: List of AbsoluteDateRange objects.
    """
    intervals = create_date_intervals(start_date, end_date, freq=freq)
    return [AbsoluteDateRange(start, end) for start, end in intervals]

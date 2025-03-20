from itertools import chain
from json import JSONDecodeError
from logging import Logger, getLogger
from re import findall
from time import sleep
from typing import List, Optional, Tuple

from bigdata_client.connection import RequestMaxLimitExceeds
from bigdata_client.document import Document
from bigdata_client.models.advanced_search_query import ListQueryComponent
from bigdata_client.models.entities import Company
from bigdata_client.models.search import DocumentType, SortBy
from bigdata_client.query_type import QueryType
from pandas import DataFrame
from pydantic import ValidationError
from tqdm import tqdm

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.prompts.labeler import (
    get_other_entity_placeholder,
    get_target_entity_placeholder,
)
from bigdata_research_tools.search.advanced_query_builder import (
    build_batched_query,
    create_date_ranges,
)
from bigdata_research_tools.search.search import run_search

logger: Logger = getLogger(__name__)


def search_by_companies(
    companies: List[Company],
    sentences: List[str],
    start_date: str,
    end_date: str,
    scope: DocumentType = DocumentType.ALL,
    fiscal_year: Optional[int] = None,
    sources: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    control_entities: Optional[List[str]] = None,
    freq: str = "M",
    sort_by: SortBy = SortBy.RELEVANCE,
    rerank_threshold: Optional[float] = None,
    document_limit: int = 50,
    batch_size: int = 10,
) -> DataFrame:
    """
    Screen for documents based on the input sentences and other filters.

    Args:
        companies (List[Company]): The list of companies to use.
        sentences (List[str]): The list of sentences to screen for.
        start_date (str): The start date for the search.
        end_date (str): The end date for the search.
        scope (DocumentType): The document type scope
            (e.g., `DocumentType.ALL`, `DocumentType.TRANSCRIPTS`).
        fiscal_year (int): The fiscal year to filter queries.
            If None, no fiscal year filter is applied.
        sources (Optional[List[str]]): List of sources to filter on. If none, we search across all sources.
        keywords (List[str]): A list of keywords for constructing keyword queries.
            If None, no keyword queries are created.
        control_entities (List[str]): A list of control entity IDs for creating co-mentions queries.
            If None, no control queries are created.
        freq (str): The frequency of the date ranges. Defaults to '3M'.
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
                - entity_id: str
                - entity_name: str
                - entity_sector: str
                - entity_industry: str
                - entity_country: str
                - entity_ticker: str
                - text: str
                - other_entities: str
                - entities: List[Dict[str, Any]]
                    - key: str
                    - name: str
                    - ticker: str
                    - start: int
                    - end: int
                - masked_text: str
                - other_entities_map: List[Tuple[int, str
    """
    # Extract entities for search querying
    entity_keys = [entity.id for entity in companies]

    # Build batched queries
    batched_query = build_batched_query(
        sentences=sentences,
        keywords=keywords,
        control_entities=control_entities,
        sources=sources,
        entity_keys=entity_keys,
        batch_size=batch_size,
        fiscal_year=fiscal_year,
        scope=scope,
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
    )

    results, entities = filter_search_results(results)
    df_sentences = process_screener_search(results, entities, companies)
    return df_sentences


def collect_entity_keys(results: List[Document]) -> List[str]:
    """
    Collect all entity keys from the search results.

    Args:
        results (List[Document]): A list of search results.
    Returns:
        List[str]: A list of entity keys in all the search results.
    """
    entity_keys = set(
        entity.key
        for result in results
        for chunk in result.chunks
        for entity in chunk.entities
        if entity.query_type == QueryType.ENTITY
    )
    entity_keys = list(entity_keys)
    return entity_keys


def filter_company_entities(
    entities: List[ListQueryComponent],
) -> List[ListQueryComponent]:
    """
    Filter only COMPANY entities from the list of entities.

    Args:
        entities (List[ListQueryComponent]): A list of entities to filter.
    Returns:
        List[ListQueryComponent]: A list of COMPANY entities.
    """
    return [
        entity
        for entity in entities
        if hasattr(entity, "entity_type") and getattr(entity, "entity_type") == "COMP"
    ]


def filter_search_results(
    results: List[List[Document]],
) -> Tuple[List[Document], List[ListQueryComponent]]:
    """
    Postprocess the search results to filter only COMPANY entities.

    Args:
        results (List[List[Document]]): A list of search results, as returned by
            the function `bigdata_research_tools.search.run_search` with the
            parameter `only_results` set to True
    Returns:
        Tuple[List[Document], List[ListQueryComponent]]: A tuple of the filtered
            search results and the entities.
    """
    # Flatten the list of result lists
    results = list(chain.from_iterable(results))
    # Collect all entities in the chunks
    entity_keys = collect_entity_keys(results)
    # Look up the entities using Knowledge Graph
    entities = look_up_entities_binary_search(entity_keys)

    # Filter only COMPANY Entities
    entities = filter_company_entities(entities)
    return results, entities


def look_up_entities_binary_search(
    entity_keys: List[str], max_batch_size: int = 50
) -> List[ListQueryComponent]:
    """
    Look up entities using the Bigdata Knowledge Graph in a binary search manner.

    Args:
        entity_keys (List[str]): A list of entity keys to look up.
        max_batch_size (int): The maximum batch size for each lookup.
    Returns:
        List[ListQueryComponent]: A list of entities.
    """
    bigdata = bigdata_connection()

    entities = []
    non_entities = []
    # TODO non_entities never gets used. Is that intentional?

    def depth_first_search(batch: List[str]) -> None:
        """
        Recursively lookup entities in a depth-first search manner.

        Args:
            batch (List[str]): A batch of entity keys to lookup.

        Returns:
            None. The function updates the inner `entities`
                and `non_entities` lists.
        """
        non_entity_key_pattern = r"\b[A-Z0-9]{6}(?=\.COMP\.entityType)"

        try:
            batch_lookup = bigdata.knowledge_graph.get_entities(batch)
            entities.extend(batch_lookup)
        except ValidationError as e:
            non_entities_found = findall(non_entity_key_pattern, str(e))
            non_entities.extend(non_entities_found)
            batch_refined = [key for key in batch if key not in non_entities]
            depth_first_search(batch_refined)
        except (JSONDecodeError, RequestMaxLimitExceeds):
            sleep(5)
            if len(batch) == 1:
                non_entities.extend(batch)
            else:
                mid = len(batch) // 2
                depth_first_search(batch[:mid])  # First half
                depth_first_search(batch[mid:])  # Second half
        except Exception as e:
            logger.error(
                f"Error in batch {batch}\n"
                f"{e.__class__.__module__}.{e.__class__.__name__}: "
                f"{str(e)}.\nRetrying..."
            )
            sleep(60)  # Wait for a minute
            depth_first_search(batch)

    logger.debug(f"Split into batches of {max_batch_size} entities")
    for batch_ in range(0, len(entity_keys), max_batch_size):
        depth_first_search(entity_keys[batch_ : batch_ + max_batch_size])

    # Deduplicate
    entities = list(
        {entity.id: entity for entity in entities if hasattr(entity, "id")}.values()
    )

    return entities


def process_screener_search(
    results: List[Document],
    entities: List[ListQueryComponent],
    companies: List[Company],
) -> DataFrame:
    """
    Build a DataFrame from the screening results and entities.

    Args:
        results (List[Document]): A list of Bigdata search results.
        entities (List[ListQueryComponent]): A list of entities.
        companies (List[Company]): A list of companies to filter for.
            Detected entities not in this list will be skipped.

    Returns:
        DataFrame: Screening DataFrame. Schema:
        - Index: int
        - Columns:
            - timestamp_utc: datetime64
            - document_id: str
            - sentence_id: str
            - headline: str
            - entity_id: str
            - entity_name: str
            - entity_sector: str
            - entity_industry: str
            - entity_country: str
            - entity_ticker: str
            - text: str
            - other_entities: str
            - entities: List[Dict[str, Any]]
                - key: str
                - name: str
                - ticker: str
                - start: int
                - end: int
            - masked_text: str
            - other_entities_map: List[Tuple[int, str]]
    """
    entity_key_map = {entity.id: entity for entity in entities}

    rows = []
    for result in tqdm(results, desc="Processing screening results..."):
        for chunk_index, chunk in enumerate(result.chunks):
            # Build a list of entities present in the chunk
            chunk_entities = [
                {
                    "key": entity.key,
                    "name": entity_key_map[entity.key].name,
                    "ticker": entity_key_map[entity.key].ticker,
                    "start": entity.start,
                    "end": entity.end,
                }
                for entity in chunk.entities
                if entity.key in entity_key_map
            ]

            if not chunk_entities:
                continue  # Skip if no entities are mapped

            for chunk_entity in chunk_entities:
                entity_key = entity_key_map.get(chunk_entity["key"])

                if not entity_key:
                    continue  # Skip if entity is not found

                # if entity isn't in our original watchlist, skip
                if entity_key not in companies:
                    continue

                # Exclude the entity from other entities
                other_entities = [
                    e for e in chunk_entities if e["name"] != chunk_entity["name"]
                ]

                # Collect all necessary information in the row
                rows.append(
                    {
                        "timestamp_utc": result.timestamp,
                        "document_id": result.id,
                        "sentence_id": f"{result.id}-{chunk_index}",
                        "headline": result.headline,
                        "entity_id": chunk_entity["key"],
                        "entity_name": entity_key.name,
                        "entity_sector": entity_key.sector,
                        "entity_industry": entity_key.industry,
                        "entity_country": entity_key.country,
                        "entity_ticker": entity_key.ticker,
                        "text": chunk.text,
                        "other_entities": ", ".join(e["name"] for e in other_entities),
                        "entities": chunk_entities,
                    }
                )

    if not rows:
        raise ValueError("No rows to process")

    df = DataFrame(rows).sort_values("timestamp_utc").reset_index(drop=True)

    # Deduplicate by quote text as well
    df = df.drop_duplicates(
        subset=["timestamp_utc", "document_id", "text", "entity_id"]
    )
    df = mask_sentences(
        df,
        document_type=DocumentType.NEWS,
    )
    df = df.reset_index(drop=True)
    return df


def mask_sentences(
    df: DataFrame,
    document_type: DocumentType,
) -> DataFrame:
    # TODO (cpinto, 2025-02-05) check this document_type parameter
    """
    Mask the target entity and other entities in the text.

    Args:
        df (DataFrame): The input DataFrame
        document_type (DocumentType): The document type
    Returns:
        DataFrame: The masked DataFrame
    """
    df["text"] = df["text"].str.replace("{", "", regex=False)
    df["text"] = df["text"].str.replace("}", "", regex=False)

    df = mask_entity_coordinates(
        df=df,
        document_type=document_type,
    )

    df["masked_text"] = df["masked_text"].apply(
        lambda x: x.replace("{", "").replace("}", "")
    )
    df = df[df["masked_text"] != "to_remove"]
    df["text"] = df["text"].apply(lambda x: x.replace("{", "").replace("}", ""))
    df = df[df.text != "to_remove"]
    return df


def mask_entity_coordinates(
    df: DataFrame,
    document_type: DocumentType,
) -> DataFrame:
    """
    Mask the target entity and other entities in the text.

    :param df: The input DataFrame
    TODO (cpinto, 2025-02-05) check this document_type parameter
    :param document_type: The document type
    :return: The masked DataFrame
    """

    i = 1
    entity_counter = {}
    df["masked_text"] = None
    df["other_entities_map"] = None

    # Ensure columns are compatible with string/object assignments
    df["masked_text"] = df["masked_text"].astype("object")
    df["other_entities_map"] = df["other_entities_map"].astype("object")
    # Determine entity ID field based on document type
    entity_id_field = (
        "rp_entity_id"
        if document_type in (DocumentType.TRANSCRIPTS, DocumentType.FILINGS)
        else "entity_id"
    )

    # Process each row
    for idx, row in df.iterrows():
        text = row["text"]
        entities = sorted(row["entities"], key=lambda x: x["start"], reverse=True)
        masked_text = text

        # Get target entity coordinates
        target_start = []
        target_end = []
        for entity in entities:
            if entity["key"] == row[entity_id_field]:
                target_start.append(entity["start"])
                target_end.append(entity["end"])

        # Apply masking
        other_entity_map = []
        for entity in entities:
            start, end = entity["start"], entity["end"]

            if entity["key"] == row[entity_id_field]:
                # Mask target entity
                masked_text = f"{masked_text[:start]}{get_target_entity_placeholder()}{masked_text[end:]}"

            elif start not in target_start and end not in target_end:
                # Mask other entities
                if entity["key"] not in entity_counter:
                    entity_counter[entity["key"]] = i
                    mask = f"{get_other_entity_placeholder()}_{entity_counter[entity['key']]}"
                    masked_text = f"{masked_text[:start]}{mask}{masked_text[end:]}"
                    other_entity_map.append(
                        (entity_counter[entity["key"]], entity["name"])
                    )
                    i += 1
                else:
                    mask = f"{get_other_entity_placeholder()}_{entity_counter[entity['key']]}"
                    masked_text = f"{masked_text[:start]}{mask}{masked_text[end:]}"
                    other_entity_map.append(
                        (entity_counter[entity["key"]], entity["name"])
                    )

        # Update DataFrame
        df.at[idx, "masked_text"] = masked_text
        df.at[idx, "other_entities_map"] = (
            other_entity_map if other_entity_map else None
        )

    return df

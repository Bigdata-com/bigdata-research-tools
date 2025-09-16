from itertools import chain
from json import JSONDecodeError
from logging import Logger, getLogger
from pydantic import ValidationError
from re import findall
from time import sleep
from typing import List, Tuple 
from bigdata_client.connection import RequestMaxLimitExceeds
from bigdata_client.document import Document
from bigdata_client.models.advanced_search_query import ListQueryComponent
from bigdata_client.models.document import DocumentChunk
from bigdata_client.query_type import QueryType
from bigdata_research_tools.client import bigdata_connection

logger: Logger = getLogger(__name__)

def _collect_entity_keys(results: List[Document]) -> List[str]:
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

def _look_up_entities_binary_search(
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

    def depth_first_search(batch: List[str]) -> None:
        """
        Recursively lookup entities in a depth-first search manner.

        Args:
            batch (List[str]): A batch of entity keys to lookup.

        Returns:
            None. The function updates the inner `entities`
                and `non_entities` lists.
        """
        non_entity_key_pattern = r"'key':\s*'([A-Z0-9]{6})'.+?'entityType':\s*'[A-Z]+'"

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
    entity_keys = _collect_entity_keys(results)
    # Look up the entities using Knowledge Graph
    entities = _look_up_entities_binary_search(entity_keys)

    return results, entities

def build_chunk_entities(chunk: DocumentChunk, 
                         entities: List[ListQueryComponent]
) -> List[dict]:

    entity_key_map = {entity.id: entity for entity in entities}

    chunk_entities = [
        {
            "key": entity.key,
            "name": getattr(entity_key_map[entity.key], "name", None),
            "ticker": getattr(entity_key_map[entity.key], "ticker", None),
            "country": getattr(entity_key_map[entity.key], "country", None),
            "country_code": getattr(entity_key_map[entity.key], "country_code", None),
            "entity_type": getattr(entity_key_map[entity.key], "entity_type", None),
            "start": entity.start,
            "end": entity.end,
        }
        for entity in chunk.entities
        if entity.key in entity_key_map
    ]

    return chunk_entities

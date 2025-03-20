"""
Module for managing labeling operations.

Copyright (C) 2024, RavenPack | Bigdata.com. All rights reserved.
"""

from json import dumps
from logging import Logger, getLogger
from typing import Any, Dict, List

from pandas import DataFrame

from bigdata_research_tools.labeler.labeler import Labeler, parse_labeling_response
from bigdata_research_tools.prompts.labeler import patent_prompts

logger: Logger = getLogger(__name__)


class PatentsLabeler(Labeler):
    """Patents labeler."""

    def __init__(
        self,
        llm_model: str,
        filing_prompt: str = None,
        object_prompt: str = None,
        temperature: float = 0.01,
    ):
        """
        Args:
            llm_model: Name of the LLM model to use. Expected format:
                <provider>::<model>, e.g. "openai::gpt-4o-mini"
            filing_prompt: Prompt provided by user to label the search result chunks.
                If not provided, then our default labelling prompt is used.
                See default prompts in `bigdata_research_tools.prompts.labeler.patent_prompts`.
            object_prompt: Prompt provided by user to label the search result chunks.
                If not provided, then our default labelling prompt is used.
                See default prompts in `bigdata_research_tools.prompts.labeler.patent_prompts`.
            temperature: Temperature to use in the LLM model.
        """
        super().__init__(llm_model=llm_model, temperature=temperature)
        self.filing_prompt = filing_prompt
        self.object_prompt = object_prompt

    def get_labels(
        self,
        texts: List[str],
        detect_filings: bool = True,
        extract_objects: bool = True,
        max_workers: int = 50,
    ) -> DataFrame:
        """
        Process thematic labels for texts.

        Args:
            texts: List of texts to analyze
            detect_filings: Whether to detect patent filings
            extract_objects: Whether to extract patent objects
            max_workers: Maximum number of concurrent workers

        Returns:
            DataFrame with schema:
            - index: int
            - columns:
                (if `detect_filings`)
                - Relevant: bool
                - Explanation: str
                (if `extract_objects`)
                - patent: str
        """
        if not detect_filings and not extract_objects:
            raise ValueError(
                "At least one of `detect_filings` or `extract_objects` must be True"
            )

        prompts = get_prompts_for_patents(texts)
        results = {}

        if detect_filings:
            system_prompt = self.filing_prompt or patent_prompts["filing"]
            filing_responses = self._run_labeling_prompts(
                prompts, system_prompt, max_workers=max_workers
            )
            filing_responses = [
                parse_labeling_response(response) for response in filing_responses
            ]
            filing_results = parse_patent_labels(filing_responses)
            results.update(filing_results)

        if extract_objects:
            system_prompt = self.object_prompt or patent_prompts["object"]
            object_responses = self._run_labeling_prompts(
                prompts, system_prompt, max_workers=max_workers
            )
            object_responses = [
                parse_labeling_response(response) for response in object_responses
            ]
            object_results = parse_patent_objects(object_responses)
            if results:
                # Update the dictionary with the object results
                results = {
                    k1: {**v1, **v2}
                    for (k1, v1), (k2, v2) in zip(
                        results.items(), object_results.items()
                    )
                }
            else:
                results.update(object_results)

        return DataFrame.from_dict(results, orient="index")


def get_prompts_for_patents(texts: List[str]) -> List[str]:
    """
    Generate the prompts for the labeling system.

    :param texts: texts to get the labels from.
    :return: A list of prompts for the labeling system.
    """
    return [dumps({"sentence_id": i, "text": text}) for i, text in enumerate(texts)]


def parse_patent_labels(responses: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Deserialize patent filing detection responses."""
    response_mapping = {}
    for i, response in enumerate(responses):
        if not response:
            continue

        if not isinstance(response, dict):
            continue

        try:
            response_mapping[i] = {
                "Relevant": response.get("relevant", False),
                "Explanation": response.get("explanation", ""),
            }
        except Exception as e:
            logger.error(f"Error deserializing patent label {i}: {e}")
            continue
    return response_mapping


def parse_patent_objects(responses: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Deserialize patent object extraction responses."""
    response_mapping = {}
    for i, response in enumerate(responses):
        if not response:
            continue
        try:
            response_mapping[i] = {k: v for k, v in response.items()}
        except Exception as e:
            logger.error(f"Error deserializing patent object {i}: {e}")
            continue
    return response_mapping

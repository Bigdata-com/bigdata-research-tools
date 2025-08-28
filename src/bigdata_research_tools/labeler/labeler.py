"""
Module for managing labeling operations.

Copyright (C) 2024, RavenPack | Bigdata.com. All rights reserved.
"""

import re
from itertools import zip_longest
from json import JSONDecodeError, dumps, loads
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional

from json_repair import repair_json
from pandas import DataFrame

from bigdata_research_tools.llm.base import AsyncLLMEngine, LLMEngine
from bigdata_research_tools.llm.utils import (
    run_concurrent_prompts,
    run_parallel_prompts,
)

logger: Logger = getLogger(__name__)


class Labeler:
    """Base class for labeling operations."""

    def __init__(
        self,
        llm_model: str,
        # Note that his value is also used in the prompts.
        unknown_label: str = "unclear",
        temperature: float = 0,
    ):
        """Initialize base Labeler.

        Args:
            llm_model: Name of the LLM model to use. Expected format:
                <provider>::<model>, e.g. "openai::gpt-4o-mini"
            unknown_label: Label for unclear classifications
            temperature: Temperature to use in the LLM model.
        """
        self.llm_model = llm_model
        self.temperature = temperature
        self.unknown_label = unknown_label

    def _deserialize_label_responses(
        self, responses: List[Dict[str, Any]]
    ) -> DataFrame:
        """
        Deserialize labeling responses into a DataFrame.

        Args:
            responses: List of response dictionaries from the LLM.

        Returns:
            DataFrame with schema:
            - index: sentence_id
            - columns:
                - motivation
                - label
        """
        response_mapping = {}
        for response in responses:

            if not response or not isinstance(response, dict):
                continue

            for k, v in response.items():
                try:
                    response_mapping[k] = {
                        "motivation": v.get("motivation", ""),
                        "label": v.get("label", self.unknown_label),
                        **{
                            key: value
                            for key, value in v.items()
                            if key not in ["motivation", "label"]
                        },
                    }
                    # Add any extra keys present in v
                    extra_keys = {
                        key: value
                        for key, value in v.items()
                        if key not in ["motivation", "label"]
                    }
                    response_mapping[k].update(extra_keys)
                except (KeyError, AttributeError):
                    response_mapping[k] = {
                        "motivation": "",
                        "label": self.unknown_label,
                    }

        df_labels = DataFrame.from_dict(response_mapping, orient="index")
        df_labels.index = df_labels.index.astype(int)
        return df_labels

    def _run_labeling_prompts(
        self, prompts: List[str], system_prompt: str, max_workers: int = 100
    ) -> List:
        """
        Get the labels from the prompts.

        Args:
            prompts: List of prompts to process
            system_prompt: System prompt for the LLM
            max_workers: Maximum number of concurrent workers

        Returns:
            List of responses from the LLM
        """
        llm_kwargs = {
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }

        # ADS-140
        # Currently, Bedrock does not support async calls. Its implementation uses synchronous calls.
        # In order to handle Bedrock as a provider we use a different function for running the prompts.
        # We execute parallel calls using ThreadPoolExecutor for Bedrock and async calls for other providers.
        provider, _ = self.llm_model.split("::")

        if provider == "bedrock":
            llm = LLMEngine(model=self.llm_model)
            return run_parallel_prompts(
                llm, prompts, system_prompt, max_workers, **llm_kwargs
            )
        else:
            llm = AsyncLLMEngine(model=self.llm_model)
            return run_concurrent_prompts(
                llm, prompts, system_prompt, max_workers, **llm_kwargs
            )


def get_prompts_for_labeler(
    texts: List[str],
    textsconfig: Optional[List[Dict[str, Any]]] = [],
) -> List[str]:
    """
    Generate a list of user messages for each text to be labelled by the labeling system.

    Example of generated prompts: [{"sentence_id": 0, "text": "Chunk 0 text here"},
    {"sentence_id": 1, "text": "Chunk 1 text here"}, ...]

    Args:
        texts: texts to get the labels from.
        textsconfig: Optional fields for the prompts in addition to the text.

    Returns:
        A list of prompts for the labeling system.
    """
    return [
        dumps({"sentence_id": i, **config, "text": text})
        for i, (config, text) in enumerate(
            zip_longest(textsconfig, texts, fillvalue={})
        )
    ]


def parse_labeling_response(response: str) -> Dict:
    """
    Parse the response from the LLM model used for labeling.

    Args:
        response: The response from the LLM model used for labeling,
            as a raw string.
    Returns:
        Parsed dictionary. Will be empty if the parsing fails. Keys:
            - motivation
            - label
    """
    try:
        # Improve json retrieval robustness by using a regex as first attempt
        # to extract the json object from the response.
        # If that fails, we use the json_repair library to try to fix common
        # json formatting issues.
        match = re.search('\{\s*"\d*":.*?\}\s*\}', response, re.DOTALL)

        if match:
            response = match.group(0)
        else:
            response = repair_json(response, return_objects=False)
        deserialized_response = loads(response)
    except JSONDecodeError:
        logger.error(f"Error deserializing response: {response}")
        return {}

    return deserialized_response

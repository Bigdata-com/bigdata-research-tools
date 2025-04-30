"""
Module for managing labeling operations.

Copyright (C) 2024, RavenPack | Bigdata.com. All rights reserved.
"""

from logging import Logger, getLogger
from typing import List, Optional

from pandas import DataFrame, Series

from bigdata_research_tools.labeler.labeler import (
    Labeler,
    get_prompts_for_labeler,
    parse_labeling_response,
)
from bigdata_research_tools.prompts.labeler import (
    get_other_entity_placeholder,
    get_screener_system_prompt,
    get_target_entity_placeholder,
)

logger: Logger = getLogger(__name__)


class ScreenerLabeler(Labeler):
    """Screener labeler."""

    def __init__(
        self,
        llm_model: str,
        label_prompt: Optional[str] = None,
        unknown_label: str = "unclear",
        temperature: float = 0,
    ):
        """
        Args:
            llm_model: Name of the LLM model to use. Expected format:
                <provider>::<model>, e.g. "openai::gpt-4o-mini"
            label_prompt: Prompt provided by user to label the search result chunks.
                If not provided, then our default labelling prompt is used.
            unknown_label: Label for unclear classifications.
            temperature: Temperature to use in the LLM model.
        """
        super().__init__(llm_model, unknown_label, temperature)
        self.label_prompt = label_prompt

    def get_labels(
        self,
        main_theme: str,
        labels: List[str],
        texts: List[str],
        max_workers: int = 50,
    ) -> DataFrame:
        """
        Process thematic labels for texts.

        Args:
            main_theme: The main theme to analyze.
            labels: Labels for labelling the chunks.
            texts: List of chunks to label.
            max_workers: Maximum number of concurrent workers.

        Returns:
            DataFrame with schema:
            - index: sentence_id
            - columns:
                - motivation
                - label
        """
        system_prompt = self.label_prompt or get_screener_system_prompt(
            main_theme, labels, unknown_label=self.unknown_label
        )
        prompts = get_prompts_for_labeler(texts)

        responses = self._run_labeling_prompts(
            prompts, system_prompt, max_workers=max_workers
        )
        responses = [parse_labeling_response(response) for response in responses]
        return self._deserialize_label_responses(responses)

    def post_process_dataframe(self, df: DataFrame) -> DataFrame:
        """
        Post-process the labeled DataFrame.

        Args:
            df: DataFrame to process. Schema:
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
                    - label: str
                    - motivation: str
        Returns:
            Processed DataFrame. Schema:
            - index: int
            - Columns:
                - Time Period
                - Date
                - Company
                - Sector
                - Industry
                - Country
                - Ticker
                - Document ID
                - Headline
                - Quote
                - Motivation
                - Theme
        """
        # Filter unlabeled sentences
        df = df.loc[df["label"] != self.unknown_label].copy()
        if df.empty:
            logger.warning(f"Empty dataframe: all rows labelled {self.unknown_label}")
            return df

        # Process timestamps
        df["timestamp_utc"] = df["timestamp_utc"].dt.tz_localize(None)

        # Sort and format
        sort_columns = ["entity_name", "timestamp_utc", "label"]
        df = df.sort_values(by=sort_columns).reset_index(drop=True)

        # Replace company placeholders
        df["motivation"] = df.apply(replace_company_placeholders, axis=1)

        # Add formatted columns
        df["Time Period"] = df["timestamp_utc"].dt.strftime("%b %Y")
        df["Date"] = df["timestamp_utc"].dt.strftime("%Y-%m-%d")

        df = df.rename(
            columns={
                "document_id": "Document ID",
                "entity_name": "Company",
                "entity_sector": "Sector",
                "entity_industry": "Industry",
                "entity_country": "Country",
                "entity_ticker": "Ticker",
                "headline": "Headline",
                "text": "Quote",
                "motivation": "Motivation",
                "label": "Theme",
            }
        )

        # Select and order columns
        export_columns = [
            "Time Period",
            "Date",
            "Company",
            "Sector",
            "Industry",
            "Country",
            "Ticker",
            "Document ID",
            "Headline",
            "Quote",
            "Motivation",
            "Theme",
        ]

        sort_columns = ["Date", "Time Period", "Company", "Document ID", "Headline", "Quote"]
        df = df[export_columns].sort_values(sort_columns).reset_index(drop=True)        
        
        return df


def replace_company_placeholders(row: Series) -> str:
    """
    Replace company placeholders in text.

    Args:
        row: Row of the DataFrame. Expected columns:
            - motivation: str
            - entity_name: str
            - other_entities_map: List[Tuple[int, str]]
    Returns:
        Text with placeholders replaced.
    """
    text = row["motivation"]
    text = text.replace(get_target_entity_placeholder(), row["entity_name"])
    if row.get("other_entities_map"):
        for entity_id, entity_name in row["other_entities_map"]:
            text = text.replace(
                f"{get_other_entity_placeholder()}_{entity_id}", entity_name
            )
    return text

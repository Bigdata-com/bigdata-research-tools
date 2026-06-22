from logging import Logger, getLogger
from typing import Any

from pandas import DataFrame, Series

from bigdata_research_tools.labeler.labeler import Labeler
from bigdata_research_tools.llm.base import LLMConfig
from bigdata_research_tools.prompts.labeler import (
    get_other_entity_placeholder,
    get_entity_risk_system_prompt,
    get_entity_theme_system_prompt,
    get_target_entity_placeholder,
)

logger: Logger = getLogger(__name__)

class EntityRiskLabeler(Labeler):
    def __init__(
        self,
        llm_model_config: str | LLMConfig | dict = "openai::gpt-4o-mini",
        label_prompt: str | None = None,
        # TODO (cpinto, 2025.02.07) This value is also in the prompt used.
        #  Changing it here would break the process.
        unknown_label: str = "unclear",
    ):
        """
        Args:
            llm_model: Name of the LLM model to use. Expected format:
                <provider>::<model>, e.g. "openai::gpt-4o-mini"
            label_prompt: Prompt provided by user to label the search result chunks.
                If not provided, then our default labelling prompt is used.
            unknown_label: Label for unclear classifications
        """
        super().__init__(llm_model_config, unknown_label)
        self.label_prompt = label_prompt

    def get_labels(
        self,
        main_theme: str,
        labels: list[str],
        texts: list[str],
        max_workers: int = 50,
        timeout: int | None = 55,
        textsconfig: list[dict[str, Any]] | None = None,
    ) -> DataFrame:
        """
        Process thematic labels for texts.

        Args:
            main_theme: The main theme to analyze.
            labels: Labels for labelling the chunks.
            texts: List of chunks to label.
            timeout: Timeout for each LLM request.
            max_workers: Maximum number of concurrent workers.

        Returns:
            DataFrame with schema:
            - index: sentence_id
            - columns:
                - motivation
                - label
        """
        system_prompt = (
            get_entity_risk_system_prompt(main_theme, labels)
            if self.label_prompt is None
            else self.label_prompt
        )

        logger.info(f"Using system prompt: {system_prompt}")

        prompts = self.get_prompts_for_labeler(texts, textsconfig)

        responses = self._run_labeling_prompts(
            prompts,
            system_prompt,
            max_workers=max_workers,
            timeout=timeout,
            processing_callbacks=[
                self.parse_labeling_response,
                self._deserialize_label_response,
            ],
        )

        return self._convert_to_label_df(responses)
    
    def post_process_dataframe(self, df: DataFrame, extra_fields: dict, extra_columns: list[str]) -> DataFrame:
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
                        - entity_country: str
                        - text: str
                        - other_entities: str
                        - entities: List[Dict[str, Any]]
                            - key: str
                            - name: str
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
                    - Entity
                    - Country
                    - Document ID
                    - Headline
                    - Quote
                    - Motivation
                    - Theme
                    - Sentiment
            """
            # Filter unlabeled sentences
            df = df.loc[df["label"] != "unclear"].copy()
            if df.empty:
                print(f"Empty dataframe: all rows labelled unclear")
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

            df["Document ID"] = df["document_id"] if "document_id" in df.columns else df["rp_document_id"]
            
            columns_map = {
                    "entity_name": "Entity",
                    "entity_type": "Entity Type",
                    "entity_country": "Country",
                    "headline": "Headline",
                    "text": "Quote",
                    "sentiment": "Sentiment",
                    "motivation": "Motivation",
                    "label": "Sub-Scenario",
                    "other_entities_name": "Other Entities",
                    "other_entities_id": "Other Entities IDs",
                    "other_entities_type": "Other Entities Types",
                }

            if 'entity_sentiment' in df.columns:
                columns_map.update({
                    "entity_sentiment": "Entity Sentiment",
                    "entity_text_sentiment": "Entity Text Sentiment"
                })

            if extra_fields:
                columns_map.update(extra_fields)
                if "quotes" in extra_fields.keys():
                    if "quotes" in df.columns:
                        df["quotes"] = df.apply(replace_company_placeholders, axis=1, col_name = 'quotes')
                    else:
                        print("quotes column not in df")

            df = df.rename(
                columns=columns_map
            )

            # Select and order columns
            export_columns = [
                "Time Period",
                "Date",
                "Entity",
                "Entity Type",
                "Country",
                "Document ID",
                "Headline",
                "Quote",
                "Sentiment",
                "Motivation",
                "Sub-Scenario",
                "Other Entities",
                "Other Entities IDs",
                "Other Entities Types"
            ]

            if extra_columns:
                export_columns += extra_columns

            return df[export_columns]
    
class EntityScreenerLabeler(Labeler):
    def __init__(
        self,
        llm_model_config: str | LLMConfig | dict = "openai::gpt-4o-mini",
        label_prompt: str | None = None,
        # TODO (cpinto, 2025.02.07) This value is also in the prompt used.
        #  Changing it here would break the process.
        unknown_label: str = "unclear",
    ):
        """
        Args:
            llm_model: Name of the LLM model to use. Expected format:
                <provider>::<model>, e.g. "openai::gpt-4o-mini"
            label_prompt: Prompt provided by user to label the search result chunks.
                If not provided, then our default labelling prompt is used.
            unknown_label: Label for unclear classifications
        """
        super().__init__(llm_model_config, unknown_label)
        self.label_prompt = label_prompt

    def get_labels(
        self,
        main_theme: str,
        labels: list[str],
        texts: list[str],
        max_workers: int = 50,
        timeout: int | None = 55,
        textsconfig: list[dict[str, Any]] | None = None,
    ) -> DataFrame:
        """
        Process thematic labels for texts.

        Args:
            main_theme: The main theme to analyze.
            labels: Labels for labelling the chunks.
            texts: List of chunks to label.
            timeout: Timeout for each LLM request.
            max_workers: Maximum number of concurrent workers.

        Returns:
            DataFrame with schema:
            - index: sentence_id
            - columns:
                - motivation
                - label
        """
        system_prompt = (
            get_entity_theme_system_prompt(main_theme, labels)
            if self.label_prompt is None
            else self.label_prompt
        )

        prompts = self.get_prompts_for_labeler(texts, textsconfig)

        responses = self._run_labeling_prompts(
            prompts,
            system_prompt,
            max_workers=max_workers,
            timeout=timeout,
            processing_callbacks=[
                self.parse_labeling_response,
                self._deserialize_label_response,
            ],
        )

        return self._convert_to_label_df(responses)
    
    def post_process_dataframe(self, df: DataFrame, extra_fields: dict, extra_columns: list[str]) -> DataFrame:
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
                        - entity_country: str
                        - text: str
                        - other_entities: str
                        - entities: List[Dict[str, Any]]
                            - key: str
                            - name: str
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
                    - Entity
                    - Country
                    - Document ID
                    - Headline
                    - Quote
                    - Motivation
                    - Theme
                    - Sentiment
            """
            # Filter unlabeled sentences
            df = df.loc[df["label"] != "unclear"].copy()
            if df.empty:
                print(f"Empty dataframe: all rows labelled unclear")
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

            df["Document ID"] = df["document_id"] if "document_id" in df.columns else df["rp_document_id"]
            
            columns_map = {
                    "entity_name": "Entity",
                    "entity_type": "Entity Type",
                    "entity_country": "Country",
                    "headline": "Headline",
                    "text": "Quote",
                    "sentiment": "Sentiment",
                    "motivation": "Motivation",
                    "label": "Theme",
                    "other_entities_name": "Other Entities",
                    "other_entities_id": "Other Entities IDs",
                    "other_entities_type": "Other Entities Types",
                }

            if extra_fields:
                columns_map.update(extra_fields)
                if "quotes" in extra_fields.keys():
                    if "quotes" in df.columns:
                        df["quotes"] = df.apply(replace_company_placeholders, axis=1, col_name = 'quotes')
                    else:
                        print("quotes column not in df")

            df = df.rename(
                columns=columns_map
            )

            # Select and order columns
            export_columns = [
                "Time Period",
                "Date",
                "Entity",
                "Entity Type",
                "Country",
                "Document ID",
                "Headline",
                "Quote",
                "Sentiment",
                "Motivation",
                "Theme",
                "Other Entities",
                "Other Entities IDs",
                "Other Entities Types"
            ]

            if extra_columns:
                export_columns += extra_columns

            return df[export_columns]

def replace_company_placeholders(
    row: Series, col_name: str = "motivation"
) -> str | list[str]:
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
    text = row[col_name]
    entity_type = row.get("entity_type", "COMP")
    if isinstance(text, str):
        text = text.replace(get_target_entity_placeholder(entity_type), row["entity_name"])
        if row.get("other_entities_map"):
            for entity_id, entity_name in row["other_entities_map"]:
                text = text.replace(
                    f"{get_other_entity_placeholder(entity_type)}_{entity_id}", entity_name
                )

    elif isinstance(text, list):
        text = [
            t.replace(get_target_entity_placeholder(entity_type), row["entity_name"]) for t in text
        ]
        if row.get("other_entities_map"):
            for entity_id, entity_name in row["other_entities_map"]:
                text = [
                    t.replace(
                        f"{get_other_entity_placeholder(entity_type)}_{entity_id}", entity_name
                    )
                    for t in text
                ]

    return text
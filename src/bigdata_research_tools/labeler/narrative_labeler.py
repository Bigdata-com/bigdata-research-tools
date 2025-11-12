from logging import Logger, getLogger

from pandas import DataFrame

from bigdata_research_tools.labeler.labeler import Labeler
from bigdata_research_tools.llm.base import LLMConfig
from bigdata_research_tools.prompts.labeler import get_narrative_system_prompt

logger: Logger = getLogger(__name__)


class NarrativeLabeler(Labeler):
    """Narrative labeler."""

    def __init__(
        self,
        label_prompt: str | None = None,
        unknown_label: str = "unclear",
        llm_model_config: str | LLMConfig | dict = "openai::gpt-4o-mini",
    ):
        """Initialize narrative labeler.

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
        theme_labels: list[str],
        texts: list[str],
        max_workers: int = 50,
        timeout: int | None = 55,
    ) -> DataFrame:
        """
        Process thematic labels for texts.

        Args:
            theme_labels: The main theme to analyze.
            texts: List of texts to label.
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
            get_narrative_system_prompt(theme_labels)
            if self.label_prompt is None
            else self.label_prompt
        )
        prompts = self.get_prompts_for_labeler(texts)

        responses = self._run_labeling_prompts(
            prompts, system_prompt, max_workers=max_workers, timeout=timeout, callback=[self.parse_labeling_response, self._deserialize_label_response]
        )
        #responses = [self.parse_labeling_response(response) for response in responses]
        # return self._deserialize_label_responses(responses)

        return self._convert_to_label_df(responses)


    def post_process_dataframe(
        self,
        df: DataFrame,
        extra_fields: dict | None = None,
        extra_columns: list[str] | None = None,
    ) -> DataFrame:
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
                    - text: str
                    - label: str
                    - motivation: str
        Returns:
            Processed DataFrame. Schema:
            - index: int
            - Columns:
                - Time Period
                - Date
                - Document ID
                - Headline
                - Chunk Text
                - Motivation
                - Label
                - Entity
                - Entity ID
                - Entity Ticker
                - Country Code
                - Entity Type
        """
        # Filter unlabeled sentences
        df = df.loc[df["label"] != self.unknown_label].copy()
        if df.empty:
            logger.warning(f"Empty dataframe: all rows labelled {self.unknown_label}")
            return df

        # Process timestamps
        df["timestamp_utc"] = df["timestamp_utc"].dt.tz_localize(None)

        # Sort and format
        sort_columns = ["timestamp_utc", "label"]
        df = df.sort_values(by=sort_columns).reset_index(drop=True)

        columns_map = {
            "document_id": "Document ID",
            "sentence_id": "Sentence ID",
            "headline": "Headline",
            "text": "Chunk Text",
            "motivation": "Motivation",
            "label": "Label",
            "entity": "Entity",
            "country_code": "Country Code",
            "entity_type": "Entity Type",
            "entity_id": "Entity ID",
            "entity_ticker": "Entity Ticker",
        }

        optional_fields = ["topics", "source_name", "source_rank", "url"]
        for field in optional_fields:
            if field in df.columns:
                columns_map[field] = field.replace("_", " ").title()

        if extra_fields:
            columns_map.update(extra_fields)

        # Select and order columns
        export_columns = [
            "Time Period",
            "Date",
            "Document ID",
            "Sentence ID",
            "Headline",
            "Chunk Text",
            "Motivation",
            "Label",
            "Entity",
            "Entity ID",
            "Entity Ticker",
            "Country Code",
            "Entity Type",
        ]

        if extra_columns:
            export_columns += extra_columns

        for field in optional_fields:
            if field in df.columns:
                export_columns += [field.replace("_", " ").title()]

        df = df.rename(columns=columns_map)

        # Add formatted columns
        df["Time Period"] = df["timestamp_utc"].dt.strftime("%b %Y")
        df["Date"] = df["timestamp_utc"].dt.strftime("%Y-%m-%d")

        df = df.explode(["Entity", "Entity Type", "Country Code"], ignore_index=True)

        sort_columns = ["Date", "Time Period", "Document ID", "Headline", "Chunk Text"]
        df = df[export_columns].sort_values(sort_columns).reset_index(drop=True)

        return df

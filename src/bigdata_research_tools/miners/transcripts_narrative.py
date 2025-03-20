from logging import Logger, getLogger
from typing import List, Optional

from bigdata_client.models.search import DocumentType
from pandas import DataFrame, merge

from bigdata_research_tools.excel import ExcelManager, check_excel_dependencies
from bigdata_research_tools.labeler.narrative_labeler import NarrativeLabeler
from bigdata_research_tools.search.narrative_search import search_narratives

logger: Logger = getLogger(__name__)


class TranscriptsNarrativeMiner:
    def __init__(
        self,
        theme_labels: List[str],
        start_date: str,
        end_date: str,
        llm_model: str,
        fiscal_year: int,  # TODO (cpinto, 2025-03-06): Make this optional?
        sources: Optional[List[str]] = None,
        rerank_threshold: Optional[float] = None,
    ):
        """
        This class will track narratives in transcripts.

        Args:
            theme_labels: List of strings which define the taxonomy of the theme.
                These will be used in both the search and the labelling of the search result chunks.
            start_date:   The start date for searching relevant documents (format: YYYY-MM-DD)
            end_date:     The end date for searching relevant documents (format: YYYY-MM-DD)
            llm_model:    Specifies the LLM to be used in text processing and analysis.
            fiscal_year:  The fiscal year for which executive transcripts should be analyzed.
            sources:      Used to filter search results by the sources of the documents.
                If not provided, the search is run across all available sources.
            rerank_threshold:  Enable the cross-encoder by setting the value between [0,1].
        """
        self.theme_labels = theme_labels
        self.start_date = start_date
        self.end_date = end_date
        self.sources = sources
        self.llm_model = llm_model
        self.fiscal_year = fiscal_year
        self.rerank_threshold = rerank_threshold
        self.df_labeled = None

    def save_to_excel(self, file_path: str) -> None:
        """
        Save the analysis results to an Excel file.

        Args:
            file_path: Path where the Excel file should be saved
        """
        if not check_excel_dependencies():
            logger.error(
                "`excel` optional dependencies are not installed. "
                "You can run `pip install bigdata_research_tools[excel]` to install them."
            )
            return

        excel_manager = ExcelManager()
        excel_args = [
            (self.df_labeled, "Semantic Labels", (0, 0)),
        ]

        excel_manager.save_workbook(excel_args, file_path)
        excel_manager.beautify_workbook(file_path)

    # TODO (cpinto, 2025-03-08): Rename to `get_narratives`?
    def mine_narratives(
        self,
        document_limit: int = 10,
        batch_size: int = 10,
        freq: str = "3M",
        export_to_path: Optional[str] = None,
    ) -> Optional[DataFrame]:
        """
        Mine narratives by searching against transcripts

        Args:
            document_limit: Maximum number of documents to analyze
            batch_size: Size of batches for processing
            freq: Frequency for analysis ('M' for monthly)
            export_to_path: Optional path to export results to Excel

        Returns:
            DataFrame with schema:
            - index: int
            - Columns:
                - Time Period
                - Date
                - Document ID
                - Headline
                - Quote
                - Motivation
                - Label
            If no relevant content is found, returns None.
        """

        # Run a search via BigData API with our mining parameters
        df_sentences = search_narratives(
            sentences=self.theme_labels,
            sources=self.sources,
            rerank_threshold=self.rerank_threshold,
            start_date=self.start_date,
            end_date=self.end_date,
            freq=freq,
            document_limit=document_limit,
            batch_size=batch_size,
            fiscal_year=self.fiscal_year,
            scope=DocumentType.TRANSCRIPTS,
        )

        # Label the search results with our theme labels
        labeler = NarrativeLabeler(llm_model=self.llm_model)
        df_labels = labeler.get_labels(
            self.theme_labels,
            texts=df_sentences["text"].tolist(),
        )

        # TODO (cpinto, 2025-03-05) df_labeled does not go to self.
        #   We have to remove the `save_to_excel` method as well
        # Merge and process results
        self.df_labeled = merge(
            df_sentences, df_labels, left_index=True, right_index=True
        )
        self.df_labeled = labeler.post_process_dataframe(self.df_labeled)

        if self.df_labeled.empty:
            logger.warning("Empty dataframe: no relevant content")
            return None

        # Export to Excel if path provided
        if export_to_path:
            self.save_to_excel(export_to_path)

        return self.df_labeled

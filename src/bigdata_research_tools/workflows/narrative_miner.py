from datetime import datetime
from logging import Logger, getLogger

from bigdata_client.models.search import DocumentType
from pandas import merge

from bigdata_research_tools.client import init_bigdata_client
from bigdata_research_tools.excel import check_excel_dependencies, save_to_excel
from bigdata_research_tools.labeler.narrative_labeler import NarrativeLabeler
from bigdata_research_tools.search import search_narratives
from bigdata_research_tools.tracing import (
    WorkflowStatus,
    WorkflowTraceEvent,
    send_trace,
)
from bigdata_research_tools.workflows.base import Workflow
from bigdata_research_tools.llm.base import LLMConfig

logger: Logger = getLogger(__name__)


class NarrativeMiner(Workflow):
    name: str = "NarrativeMiner"

    def __init__(
        self,
        narrative_sentences: list[str],
        start_date: str,
        end_date: str,
        llm_model_config: str | LLMConfig | dict,
        document_type: DocumentType,
        fiscal_year: int | list[int] | None = None,
        sources: list[str] | None = None,
        rerank_threshold: float | None = None,
    ):
        """
        This class will track a set of user-defined narratives (specified in narrative_sentences) over
        news, transcripts, or filings (specified in document_scope).

        Args:
            narrative_sentences:      List of strings which define the set of narrative sentences to track.
                               These will be used in both the search and the labelling of the search result chunks.
            start_date:        The start date for searching relevant documents (format: YYYY-MM-DD).
            end_date:          The end date for searching relevant documents (format: YYYY-MM-DD).
            llm_model:         Specifies the LLM to be used in text processing and analysis.
            document_type:     Specifies the type of documents to search over.
            fiscal_year:       The fiscal year for which filings or transcripts should be analyzed.
            sources:           Used to filter search results by the sources of the documents.
                               If not provided, the search is run across all available sources.
            rerank_threshold:  Enable the cross-encoder by setting the value between [0, 1].
        """
        super().__init__()
        self.narrative_sentences = narrative_sentences
        self.sources = sources
        self.fiscal_year = fiscal_year
        self.document_type = document_type
        self.start_date = start_date
        self.end_date = end_date
        self.rerank_threshold = rerank_threshold

        if isinstance(llm_model_config, dict):
            self.llm_model_config = LLMConfig(**llm_model_config)
        elif isinstance(llm_model_config, str):
            self.llm_model_config = llm_model_config
        elif isinstance(llm_model_config, LLMConfig):
            self.llm_model_config = llm_model_config

    def mine_narratives(
        self,
        document_limit: int = 10,
        batch_size: int = 10,
        frequency: str = "3M",
        export_path: str | None = None,
    ) -> dict:
        """
        Mine narratives

        Args:
            document_limit: Maximum number of documents to analyze.
            batch_size: Size of batches for processing.
            frequency: Frequency for analysis ('M' for monthly).
            export_path: Optional path to export results to an Excel file.

        Returns:
            Dictionary containing analysis results.
        """

        if export_path and not check_excel_dependencies():
            logger.error(
                "`excel` optional dependencies are not installed. "
                "You can run `pip install bigdata_research_tools[excel]` to install them. "
                "Consider installing them to save the Narrative Miner result into the "
                f"path `{export_path}`."
            )
        bigdata_client = init_bigdata_client()
        workflow_start = datetime.now()
        workflow_status = WorkflowStatus.UNKNOWN

        try:
            # Run a search via BigData API with our mining parameters
            self.notify_observers("Searching documents for relevant content")
            df_sentences = search_narratives(
                sentences=self.narrative_sentences,
                sources=self.sources,
                rerank_threshold=self.rerank_threshold,
                start_date=self.start_date,
                end_date=self.end_date,
                frequency=frequency,
                document_limit=document_limit,
                batch_size=batch_size,
                scope=self.document_type,
                bigdata_client=bigdata_client,
                fiscal_year=self.fiscal_year,
                workflow_name=NarrativeMiner.name,
            )
            self.notify_observers(
                f"Search completed. {len(df_sentences)} chunks found."
            )
            self.notify_observers("Labelling search results")
            # Label the search results with our narrative sentences
            labeler = NarrativeLabeler(llm_model_config=self.llm_model_config)
            df_labels = labeler.get_labels(
                self.narrative_sentences,
                texts=df_sentences["text"].tolist(),
            )
            self.notify_observers(
                f"Labelling completed. {len(df_labels)} labels generated."
            )
            self.notify_observers("Post-processing results")
            # Merge and process results
            df_labeled = merge(
                df_sentences, df_labels, left_index=True, right_index=True
            )
            df_labeled = labeler.post_process_dataframe(df_labeled)

            self.notify_observers("Results post-processed")
            if df_labeled.empty:
                logger.warning("Empty dataframe: no relevant content")
                # Return an empty dictionary
                return {}
            # Export to Excel if path provided
            if export_path:
                self.notify_observers("Exporting results to excel")
                save_to_excel(
                    export_path, tables={"Semantic Labels": (df_labeled, (0, 0))}
                )
                self.notify_observers("Results exported")

            workflow_status = WorkflowStatus.SUCCESS
        except BaseException:
            workflow_status = WorkflowStatus.FAILED
            raise
        finally:
            send_trace(
                bigdata_client,
                WorkflowTraceEvent(
                    name=NarrativeMiner.name,
                    start_date=workflow_start,
                    end_date=datetime.now(),
                    llm_model=self.llm_model_config.model if isinstance(self.llm_model_config, LLMConfig) else str(self.llm_model_config),
                    status=workflow_status,
                ),
            )

        return {"df_labeled": df_labeled}

from logging import Logger, getLogger
from typing import Dict, List, Optional

from bigdata_client.models.search import DocumentType
from bigdata_research_tools.client import init_bigdata_client
from pandas import merge
from bigdata_research_tools.tracing import Trace, TraceEventNames, send_trace

from bigdata_research_tools.excel import check_excel_dependencies
from bigdata_research_tools.labeler.narrative_labeler import NarrativeLabeler
from bigdata_research_tools.search import search_narratives
from bigdata_research_tools.workflows.utils import save_to_excel

logger: Logger = getLogger(__name__)


class NarrativeMiner:
    def __init__(
        self,
        narrative_sentences: List[str],
        start_date: str,
        end_date: str,
        llm_model: str,
        document_type: DocumentType,
        fiscal_year: Optional[int],
        sources: Optional[List[str]] = None,
        rerank_threshold: Optional[float] = None,
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
        
        self.llm_model = llm_model
        self.narrative_sentences = narrative_sentences
        self.sources = sources
        self.fiscal_year = fiscal_year
        self.document_type = document_type
        self.start_date = start_date
        self.end_date = end_date
        self.rerank_threshold = rerank_threshold

    def mine_narratives(
        self,
        document_limit: int = 10,
        batch_size: int = 10,
        freq: str = "3M",
        export_path: Optional[str] = None,
    ) -> Dict:
        """
        Mine narratives

        Args:
            document_limit: Maximum number of documents to analyze.
            batch_size: Size of batches for processing.
            freq: Frequency for analysis ('M' for monthly).
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
        current_trace = Trace(
            event_name=TraceEventNames.NARRATIVE_MINER,
            document_type=self.document_type,
            start_date=self.start_date,
            end_date=self.end_date,
            rerank_threshold=self.rerank_threshold,
            llm_model=self.llm_model,
            frequency=freq,
            workflow_start_date=Trace.get_time_now(),
        )
        try:
            # Run a search via BigData API with our mining parameters
            df_sentences = search_narratives(
                sentences=self.narrative_sentences,
                sources=self.sources,
                rerank_threshold=self.rerank_threshold,
                start_date=self.start_date,
                end_date=self.end_date,
                freq=freq,
                document_limit=document_limit,
                batch_size=batch_size,
                scope=self.document_type,
                current_trace=current_trace,
                bigdata_client=bigdata_client,
                fiscal_year=self.fiscal_year,
            )

            # Label the search results with our narrative sentences
            labeler = NarrativeLabeler(llm_model=self.llm_model)
            df_labels = labeler.get_labels(
                self.narrative_sentences,
                texts=df_sentences["text"].tolist(),
            )

            # Merge and process results
            df_labeled = merge(
                df_sentences, df_labels, left_index=True, right_index=True
            )
            df_labeled = labeler.post_process_dataframe(df_labeled)

            if df_labeled.empty:
                logger.warning("Empty dataframe: no relevant content")
                # Return an empty dictionary
                return {}

            # Export to Excel if path provided
            if export_path:
                save_to_excel(
                    export_path, tables={"Semantic Labels": (df_labeled, (0, 0))}
                )

        except Exception:
            execution_result = "error"
            raise
        else:
            execution_result = "success"
        finally:
            current_trace.workflow_end_date = Trace.get_time_now()
            current_trace.result = execution_result  # noqa
            send_trace(bigdata_client, current_trace)

        return {"df_labeled": df_labeled}

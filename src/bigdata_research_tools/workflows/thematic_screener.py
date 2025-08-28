from logging import Logger, getLogger
from typing import Dict, List, Optional, Tuple

from bigdata_client.models.entities import Company
from bigdata_client.models.search import DocumentType
from pandas import DataFrame, merge

from bigdata_research_tools.client import init_bigdata_client
from bigdata_research_tools.excel import check_excel_dependencies
from bigdata_research_tools.labeler.screener_labeler import ScreenerLabeler
from bigdata_research_tools.portfolio.motivation import Motivation
from bigdata_research_tools.search.screener_search import search_by_companies
from bigdata_research_tools.themes import generate_theme_tree
from bigdata_research_tools.tracing import Trace, TraceEventNames, send_trace
from bigdata_research_tools.workflows.utils import get_scored_df, save_to_excel

logger: Logger = getLogger(__name__)


class ThematicScreener:

    def __init__(
        self,
        llm_model: str,
        main_theme: str,
        companies: List[Company],
        start_date: str,
        end_date: str,
        document_type: DocumentType,
        fiscal_year: Optional[int] = None,
        sources: Optional[List[str]] = None,
        rerank_threshold: Optional[float] = None,
        focus: str = "",
    ):
        """
        This class will screen a universe's (specified in 'companies') exposure to a given theme ('main_theme').

        Args:
            llm_model (str): LLM <provider::model> to be used in text processing and analysis.
                For example, "openai::gpt-4o-mini".
            main_theme (str): The main theme to screen for in the companies received.
                A list of sub-themes will be generated based on this main theme.
            companies (List[Company]): List of companies to analyze.
            start_date (str): The start date for searching relevant documents.
                Format: YYYY-MM-DD.
            end_date (str): The end date for searching relevant documents.
                Format: YYYY-MM-DD.
            document_type (DocumentType): Specifies the type of documents to search over
            fiscal_year (int): The fiscal year that will be analyzed.
            sources (Optional[List[str]]): Used to filter search results by the sources of the documents.
                If not provided, the search is run across all available sources.
            rerank_threshold (Optional[float]): The threshold for reranking the search results.
                See https://sdk.bigdata.com/en/latest/how_to_guides/rerank_search.html.
            focus (Optional[str]): The focus of the analysis. No value by default.
                If used, generated sub-themes will be based on this.
        """

        self.llm_model = llm_model
        self.main_theme = main_theme
        self.companies = companies
        self.start_date = start_date
        self.end_date = end_date
        self.fiscal_year = fiscal_year
        self.document_type = document_type
        self.sources = sources
        self.rerank_threshold = rerank_threshold
        self.focus = focus

    def screen_companies(
        self,
        document_limit: int = 10,
        batch_size: int = 10,
        frequency: str = "3M",
        word_range: Tuple[int, int] = (50, 100),
        export_path: str = None,
    ) -> Dict:
        """
        Screen companies for the Executive Narrative Factor.

        Args:
            document_limit (int): The maximum number of documents to return per Bigdata query.
            batch_size (int): The number of entities to include in each batched query.
            frequency (str): The frequency of the date ranges. Supported values:
                - 'Y': Yearly intervals.
                - 'M': Monthly intervals.
                - 'W': Weekly intervals.
                - 'D': Daily intervals.
                Defaults to '3M'.
            export_path: Optional path to export results to an Excel file.

        Returns:
            dict:
            - df_labeled: The DataFrame with the labeled search results.
            - df_company: The DataFrame with the output by company.
            - df_industry: The DataFrame with the output by industry.
            - df_motivation: The DataFrame with the motivation by company
            - theme_tree: The ThemeTree created for the screening.
        """

        if export_path and not check_excel_dependencies():
            logger.error(
                "`excel` optional dependencies are not installed. "
                "You can run `pip install bigdata_research_tools[excel]` to install them. "
                "Consider installing them to save the Thematic Screener result into the "
                f"path `{export_path}`."
            )
        bigdata_client = init_bigdata_client()
        current_trace = Trace(
            event_name=TraceEventNames.THEMATIC_SCREENER,
            document_type=self.document_type,
            start_date=self.start_date,
            end_date=self.end_date,
            rerank_threshold=self.rerank_threshold,
            llm_model=self.llm_model,
            frequency=frequency,
            workflow_start_date=Trace.get_time_now(),
        )

        try:
            self.provider, self.model = self.llm_model.split("::")
            theme_tree = generate_theme_tree(
                main_theme=self.main_theme,
                focus=self.focus,
                llm_model_config={"provider": self.provider, "model": self.model},
            )

            theme_summaries = theme_tree.get_terminal_summaries()
            terminal_labels = theme_tree.get_terminal_labels()

            df_sentences = search_by_companies(
                companies=self.companies,
                sentences=theme_summaries,
                start_date=self.start_date,
                end_date=self.end_date,
                scope=self.document_type,
                fiscal_year=self.fiscal_year,
                sources=self.sources,
                rerank_threshold=self.rerank_threshold,
                freq=frequency,
                document_limit=document_limit,
                batch_size=batch_size,
                current_trace=current_trace,
                bigdata_client=bigdata_client,
            )

            # Label the search results with our theme labels
            labeler = ScreenerLabeler(llm_model=self.llm_model)
            df_labels = labeler.get_labels(
                main_theme=self.main_theme,
                labels=terminal_labels,
                texts=df_sentences["masked_text"].tolist(),
            )

            # Merge and process results
            df = merge(df_sentences, df_labels, left_index=True, right_index=True)
            df = labeler.post_process_dataframe(df)

            if df.empty:
                logger.warning("Empty dataframe: no relevant content")
                return {
                    "df_labeled": df,
                    "df_company": DataFrame(),
                    "df_industry": DataFrame(),
                    "df_motivation": DataFrame(),
                    "theme_tree": theme_tree,
                }

            df_company = get_scored_df(
                df,
                index_columns=["Company", "Ticker", "Industry"],
                pivot_column="Theme",
            )
            df_industry = get_scored_df(
                df, index_columns=["Industry"], pivot_column="Theme"
            )

            motivation_generator = Motivation(model=self.llm_model)
            motivation_df = motivation_generator.generate_company_motivations(
                df=df, theme_name=self.main_theme, word_range=word_range
            )

            # Export to Excel if path provided
            if export_path:
                save_to_excel(
                    file_path=export_path,
                    tables={
                        "Semantic Labels": (df, (0, 0)),
                        "By Company": (df_company, (2, 4)),
                        "By Industry": (df_industry, (2, 2)),
                        "Motivations": (motivation_df, (0, 0)),
                    },
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

        return {
            "df_labeled": df,
            "df_company": df_company,
            "df_industry": df_industry,
            "df_motivation": motivation_df,
            "theme_tree": theme_tree,
        }

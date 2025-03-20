from logging import Logger, getLogger
from typing import Dict, List, Optional

from bigdata_client.models.entities import Company
from bigdata_client.models.search import DocumentType, SortBy
from numpy import vstack
from pandas import DataFrame, merge
from tqdm import tqdm

from bigdata_research_tools.embeddings import EmbeddingsEngine
from bigdata_research_tools.excel import check_excel_dependencies
from bigdata_research_tools.labeler.patents_labeler import PatentsLabeler
from bigdata_research_tools.labeler.screener_labeler import ScreenerLabeler
from bigdata_research_tools.screeners.utils import get_scored_df, save_factor_to_excel
from bigdata_research_tools.search.screener_search import search_by_companies
from bigdata_research_tools.themes import (
    SourceType,
    generate_theme_tree,
    stringify_label_summaries,
)

logger: Logger = getLogger(__name__)


class PatentsBuzzFactor:

    def __init__(
        self,
        llm_model: str,
        embeddings_model: str,
        main_theme: str,
        companies: List[Company],
        start_date: str,
        end_date: str,
        sources: Optional[List[str]] = None,
        rerank_threshold: Optional[float] = None,
        focus: str = "",
    ):
        self.llm_model = llm_model
        self.embeddings_model = embeddings_model
        self.main_theme = main_theme
        self.companies = companies
        self.start_date = start_date
        self.end_date = end_date
        self.sources = sources
        self.rerank_threshold = rerank_threshold
        self.focus = focus

    def screen_companies(
        self,
        document_limit: int = 50,
        batch_size: int = 10,
        frequency: str = "3M",
        export_path: str = None,
    ) -> Dict:
        """
        Screen companies for the patents buzz factor.
        Args:
            document_limit: The maximum number of documents to return per Bigdata query.
            batch_size: The number of entities to include in each batched query.
            frequency: The frequency of the date ranges.
            export_path: Optional path to export results to an Excel file.

        Returns: Dictionary with keys:
            - df_labeled: The DataFrame with the labeled search results.
            - df_company: The DataFrame with the output by company.
            - df_industry: The DataFrame with the output by industry.
            - theme_tree: The theme tree created for the screening.
        """

        try:
            from hdbscan import HDBSCAN
        except ImportError:
            logger.error(
                "Optional dependency `hdbscan` is not installed.\n"
                "You can run `pip install bigdata_research_tools[patents_buzz]` to install it."
            )
            raise

        if export_path and not check_excel_dependencies():
            logger.error(
                "`excel` optional dependencies are not installed. "
                "You can run `pip install bigdata_research_tools[excel]` to install them. "
                "Consider installing them to save the `executive_narrative` factor into the "
                f"path `{export_path}`."
            )

        # Generate a ThemeTree
        theme_tree = generate_theme_tree(
            main_theme=self.main_theme,
            dataset=SourceType.PATENTS,
            focus=self.focus,
        )
        terminal_label_summaries = theme_tree.get_terminal_label_summaries()
        summaries = stringify_label_summaries(terminal_label_summaries)

        # Screen companies
        df_sentences = search_by_companies(
            companies=self.companies,
            sentences=summaries,
            start_date=self.start_date,
            end_date=self.end_date,
            scope=DocumentType.TRANSCRIPTS,
            sources=self.sources,
            keywords=["patent"],
            rerank_threshold=self.rerank_threshold,
            freq=frequency,
            document_limit=document_limit,
            batch_size=batch_size,
        )

        # Add patent labels
        patents_labeler = PatentsLabeler(llm_model=self.llm_model)
        df_patent = patents_labeler.get_labels(
            texts=df_sentences["masked_text"].tolist(),
            detect_filings=True,
            extract_objects=True,
        )

        # Add thematic labels
        labeler = ScreenerLabeler(llm_model=self.llm_model)
        df_labels = labeler.get_labels(
            main_theme=self.main_theme,
            summaries=summaries,
            texts=df_sentences["masked_text"].tolist(),
        )

        # Join results
        df = merge(df_sentences, df_patent, left_index=True, right_index=True)
        df = merge(df, df_labels, left_index=True, right_index=True)

        # Filter and deduplicate (Patents labeler post-processing)
        df = df.loc[df["Relevant"]].reset_index(drop=True)

        df_company, df_industry = DataFrame(), DataFrame()
        if df.empty:
            logger.warning("Empty dataframe: no relevant content")
            return {
                "df_labeled": df,
                "df_company": df_company,
                "df_industry": df_industry,
                "theme_tree": theme_tree,
            }

        # Create embeddings
        embeddings_engine = EmbeddingsEngine(model=self.embeddings_model)

        tqdm.pandas(desc="Getting embeddings...")
        df["embedding"] = df["patent"].progress_apply(
            lambda x: embeddings_engine.get_embeddings(x.lower())
        )

        # Cluster similar patents
        df["cluster_labels"] = df.groupby(["entity_id"])["embedding"].transform(
            lambda x: (
                HDBSCAN(min_cluster_size=2).fit_predict(vstack(x)) if len(x) > 1 else -1
            )
        )

        # Take first instance of each cluster
        df = df.groupby(["entity_id", "cluster_labels", "label"]).first().reset_index()

        df = labeler.post_process_dataframe(df)
        # TODO (cpinto, 2025-03-08) This check can be done after executing
        #  the ScreenerLabeler
        if df.empty:
            logger.warning("Empty dataframe: no relevant content")
            return {
                "df_labeled": df,
                "df_company": df_company,
                "df_industry": df_industry,
                "theme_tree": theme_tree,
            }

        df_company = get_scored_df(
            df, index_columns=["Company", "Ticker", "Industry"], pivot_column="Theme"
        )
        df_industry = get_scored_df(
            df, index_columns=["Industry"], pivot_column="Theme"
        )

        save_factor_to_excel(
            file_path=export_path,
            df_company=df_company,
            df_industry=df_industry,
            df_semantic_labels=df,
        )

        return {
            "df_labeled": df,
            "df_company": df_company,
            "df_industry": df_industry,
            "theme_tree": theme_tree,
        }

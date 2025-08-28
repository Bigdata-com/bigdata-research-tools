from logging import Logger, getLogger
from typing import Dict, List, Optional, Tuple

from bigdata_client.models.entities import Company
from bigdata_client.models.search import DocumentType
from pandas import DataFrame, merge

from bigdata_research_tools.client import init_bigdata_client
from bigdata_research_tools.excel import check_excel_dependencies
from bigdata_research_tools.labeler.risk_labeler import RiskLabeler, map_risk_category
from bigdata_research_tools.portfolio.motivation import Motivation
from bigdata_research_tools.search.screener_search import search_by_companies
from bigdata_research_tools.themes import ThemeTree, generate_risk_tree
from bigdata_research_tools.tracing import Trace, TraceEventNames, send_trace
from bigdata_research_tools.workflows.utils import get_scored_df, save_to_excel

logger: Logger = getLogger(__name__)


class RiskAnalyzer:

    def __init__(
        self,
        llm_model: str,
        main_theme: str,
        companies: List[Company],
        start_date: str,
        end_date: str,
        document_type: DocumentType,
        keywords: Optional[List[str]] = None,
        control_entities: Optional[Dict[str, List[str]]] = None,
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
        self.keywords = keywords
        self.control_entities = control_entities
        self.sources = sources
        self.rerank_threshold = rerank_threshold
        self.focus = focus

    def create_taxonomy(self):
        """Create a risk taxonomy based on the main theme and focus.
        Returns:
            ThemeTree: The generated risk tree.
            List[str]: A list of risk summaries for the terminal nodes.
            List[str]: A list of terminal labels for the risk categories.
        """

        self.provider, self.model = self.llm_model.split("::")
        risk_tree = generate_risk_tree(
            main_theme=self.main_theme,
            focus=self.focus,
            llm_model_config={"provider": self.provider, "model": self.model},
        )

        risk_summaries = risk_tree.get_terminal_summaries()
        terminal_labels = risk_tree.get_terminal_labels()

        return risk_tree, risk_summaries, terminal_labels

    def retrieve_results(
        self,
        sentences: List[str],
        freq: str = "3M",
        document_limit: int = 10,
        batch_size: int = 10,
    ) -> DataFrame:
        """Retrieve search results based on the provided sentences and parameters.
        Args:
            sentences (List[str]): List of sentences to search for.
            freq (str): The frequency of the date ranges. Supported values:
                - 'Y': Yearly intervals.
                - 'M': Monthly intervals.
                - 'W': Weekly intervals.
                - 'D': Daily intervals.
                Defaults to '3M'.
            document_limit (int): The maximum number of documents to return per Bigdata query.
            batch_size (int): The number of entities to include in each batched query.
        Returns:
            DataFrame: A DataFrame containing the search results with relevant information.
        """

        ## To Do: import the search class and make search_by_companies a class method
        df_sentences = search_by_companies(
            companies=self.companies,
            sentences=sentences,
            start_date=self.start_date,
            end_date=self.end_date,
            scope=self.document_type,
            keywords=self.keywords,
            control_entities=self.control_entities,
            fiscal_year=self.fiscal_year,
            sources=self.sources,
            rerank_threshold=self.rerank_threshold,
            freq=freq,
            document_limit=document_limit,
            batch_size=batch_size,
        )

        return df_sentences

    def _add_prompt_fields(
        self, df_sentences: DataFrame, additional_prompt_fields: Optional[List] = None
    ) -> List[Dict]:
        """
        Add additional fields from the DataFrame for the labeling prompt.

        Args:
            df_sentences (DataFrame): The DataFrame containing the search results.
            additional_prompt_fields (Optional[List]): Additional fields to be used in the labeling prompt.

        Returns:
            List[Dict]: A list of dictionaries with the additional fields for each row in the DataFrame.
        """
        if additional_prompt_fields:
            missing = set(additional_prompt_fields) - set(df_sentences.columns)
            if missing:
                raise ValueError(f"Columns not found in DataFrame: {missing}")
            else:
                return df_sentences[additional_prompt_fields].to_dict(orient="records")
        else:
            return []

    def label_search_results(
        self,
        df_sentences,
        terminal_labels,
        risk_tree: ThemeTree,
        additional_prompt_fields: Optional[List] = None,
    ):
        """
        Label the search results with our theme labels.

        Args:
            df_sentences (DataFrame): The DataFrame containing the search results.
            terminal_labels (List[str]): The terminal labels for the risk categories.
            risk_tree (ThemeTree): The ThemeTree object containing the risk taxonomy.
            prompt_fields (Dict): Additional fields to be used in the labeling prompt.

        Returns:
            DataFrame: The port-processed DataFrame with labeled search results.
        """

        prompt_fields = self._add_prompt_fields(df_sentences, additional_prompt_fields)

        # Label the search results with our theme labels
        ## To Do: generalize the labeler or pass it as an argument
        # to allow for different labelers to be used.
        labeler = RiskLabeler(llm_model=self.llm_model)
        df_labels = labeler.get_labels(
            main_theme=self.main_theme,
            labels=terminal_labels,
            texts=df_sentences["masked_text"].tolist(),
            textsconfig=prompt_fields,
        )

        # Merge and process results
        df = merge(df_sentences, df_labels, left_index=True, right_index=True)

        # Create the reverse mapping
        label_to_parent = risk_tree.get_label_to_parent_mapping()

        ## to do: generalize the mapping function to allow for different risk categories and assign it to a class variable

        ## to do: generalize the extra fields generation logic to allow for different fields to be added

        df["risk_factor"] = df["label"].apply(
            lambda x: map_risk_category(x, label_to_parent)
        )

        df = df.loc[
            df.risk_factor.notnull() | df.risk_factor.ne("Not Applicable")
        ].copy()

        df["channel"] = df.apply(
            lambda row: row["risk_factor"] + "/" + row["label"], axis=1
        )

        df["theme"] = self.main_theme

        df_clean = labeler.post_process_dataframe(
            df,
            extra_fields={
                "channel": "Risk Channel",
                "risk_factor": "Risk Factor",
                "quotes": "Highlights",
            },
            extra_columns=["Risk Channel", "Risk Factor", "Highlights"],
        )

        return df, df_clean

    def generate_results(
        self, df_labeled: DataFrame, word_range: Tuple[int, int] = (50, 100)
    ):
        """Generate the Pivot Tables with factor Scores for companies and industries."""

        df_company, df_industry = DataFrame(), DataFrame()
        if df_labeled.empty:
            logger.warning("Empty dataframe: no relevant content")
            return df_company, df_industry

        df_company = get_scored_df(
            df_labeled,
            index_columns=["Company", "Ticker", "Sector", "Industry"],
            pivot_column="Sub-Scenario",
        )
        df_industry = get_scored_df(
            df_labeled, index_columns=["Industry"], pivot_column="Sub-Scenario"
        )
        motivation_generator = Motivation(model=self.llm_model)
        motivation_df = motivation_generator.generate_company_motivations(
            df=df_labeled.rename(columns={"Sub-Scenario": "Theme"}),
            theme_name=self.main_theme,
            word_range=word_range,
        )

        return df_company, df_industry, motivation_df

    def save_results(
        self,
        df_labeled: DataFrame,
        df_company: DataFrame,
        df_industry: DataFrame,
        motivation_df: DataFrame,
        risk_tree: ThemeTree,
        export_path: str,
    ):
        """
        Save the results to Excel files if export_path is provided.

        Args:
            df_labeled (DataFrame): The DataFrame with the labeled search results.
            df_company (DataFrame): The DataFrame with the output by company.
            df_industry (DataFrame): The DataFrame with the output by industry.
            export_path (str): The path to export the results to.
        """
        if export_path:
            save_to_excel(
                file_path=export_path,
                tables={
                    "Semantic Labels": (df_labeled, (0, 0)),
                    "By Company": (df_company, (2, 5)),
                    "By Industry": (df_industry, (2, 2)),
                    "Motivations": (motivation_df, (0, 0)),
                },
            )
            ## Save risk tree to json
            risk_tree.save_json(export_path.replace(".xlsx", "_mindmap.json"))
        else:
            logger.warning("No export path provided. Results will not be saved.")

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
            - risk_tree: The ThemeTree created for the screening.
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
            event_name=TraceEventNames.RISK_ANALYZER,
            document_type=self.document_type,
            start_date=self.start_date,
            end_date=self.end_date,
            rerank_threshold=self.rerank_threshold,
            llm_model=self.llm_model,
            frequency=frequency,
            workflow_start_date=Trace.get_time_now(),
        )

        try:
            risk_tree, risk_summaries, terminal_labels = self.create_taxonomy()

            df_sentences = self.retrieve_results(
                sentences=risk_summaries,
                freq=frequency,
                document_limit=document_limit,
                batch_size=batch_size,
            )

            df, df_labeled = self.label_search_results(
                df_sentences=df_sentences,
                terminal_labels=terminal_labels,
                risk_tree=risk_tree,
                additional_prompt_fields=[
                    "entity_sector",
                    "entity_industry",
                    "headline",
                ],
            )

            df_company, df_industry, df_motivation = self.generate_results(
                df_labeled, word_range
            )

            # Export to Excel if path provided
            if export_path:
                self.save_results(
                    df_labeled,
                    df_company,
                    df_industry,
                    df_motivation,
                    risk_tree,
                    export_path=export_path,
                )

        except Exception as e:
            execution_result = "error"
            raise e
        else:
            execution_result = "success"
        finally:
            current_trace.workflow_end_date = Trace.get_time_now()
            current_trace.result = execution_result  # noqa
            send_trace(bigdata_client, current_trace)
        return {
            "df_labeled": df_labeled,
            "df_company": df_company,
            "df_industry": df_industry,
            "df_motivation": df_motivation,
            "risk_tree": risk_tree,
        }

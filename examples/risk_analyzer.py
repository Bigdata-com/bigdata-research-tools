from pathlib import Path

from bigdata_client.models.search import DocumentType

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.llm.base import LLMConfig
from bigdata_research_tools.utils.observer import OberserverNotification, Observer
from bigdata_research_tools.workflows.risk_analyzer import RiskAnalyzer


def risk_analyzer_example(
    risk_scenario: str,
    llm_model_config: str | LLMConfig | dict,
    keywords: list = ["Tariffs"],
    control_entities: dict = {"place": ["Canada", "Mexico"]},
    focus: str = "",
    export_path: str = "risk_analyzer_results.xlsx",
) -> dict:
    GRID_watchlist_ID = "44118802-9104-4265-b97a-2e6d88d74893"

    bigdata = bigdata_connection()
    # Retrieve the watchlist object
    watchlist_grid = bigdata.watchlists.get(GRID_watchlist_ID)
    # Access the items within the watchlist
    companies = bigdata.knowledge_graph.get_entities(watchlist_grid.items)

    analyzer = RiskAnalyzer(
        main_theme=risk_scenario,
        companies=companies,
        start_date="2025-01-01",
        end_date="2025-01-31",
        keywords=keywords,
        document_type=DocumentType.NEWS,
        control_entities=control_entities,
        focus=focus,  # Optional focus to narrow the theme,
        llm_model_config=llm_model_config,
        ground_mindmap=False,
    )

    class PrintObserver(Observer):
        def update(self, message: OberserverNotification):
            print(f"Notification received: {message}")

    analyzer.register_observer(PrintObserver())

    return analyzer.screen_companies(export_path=export_path)


if __name__ == "__main__":
    import logging

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    # Set the logging configuration to show the logs of the library
    logging.basicConfig()
    logging.getLogger("bigdata_research_tools").setLevel(logging.INFO)

    output_path = Path("outputs/risk_analyzer_results.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    x = risk_analyzer_example(
        "US Import Tariffs against Canada and Mexico",
        focus="Provide a detailed taxonomy of risks describing how new American import tariffs against Canada and Mexico will impact US companies, their operations and strategy. Cover trade-relations risks, foreign market access risks, supply chain risks, US market sales and revenue risks (including price impacts), and intellectual property risks, provide at least 4 sub-scenarios for each risk factor.",
        export_path=str(output_path),
        llm_model_config=LLMConfig(
            model="openai::gpt-5-mini",
            reasoning_effort="medium",
        ),
    )
    # custom_config = {
    #     'company_column': 'Company',
    #     'heatmap_colorscale': 'Plasma',
    #     'dashboard_height': 1800,
    #     'top_themes_count': 5,
    #     'main_title': 'Custom Thematic Analysis Dashboard'
    # }
    df = x["df_company"]
    # fig, industry_fig = create_thematic_exposure_dashboard(df, n_companies=15, config=custom_config)
    # fig.show(renderer="browser")           # Shows the main dashboard
    # industry_fig.show(renderer="browser")  # Shows the industry analysis
    print(df.head(10))  # Display the first 10 rows of the DataFrame

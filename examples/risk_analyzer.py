from typing import Dict

from bigdata_client.models.search import DocumentType

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.visuals import create_risk_exposure_dashboard
from bigdata_research_tools.workflows.risk_analyzer import RiskAnalyzer


def risk_analyzer_example(
    risk_scenario: str,
    llm_model: str = "openai::gpt-4o-mini",
    keywords: list = ["Tariffs"],
    control_entities: dict = {"place": ["Canada", "Mexico"]},
    focus: str = "",
    export_path: str = "risk_analyzer_results.xlsx",
) -> Dict:

    GRID_watchlist_ID = "44118802-9104-4265-b97a-2e6d88d74893"

    bigdata = bigdata_connection()
    # Retrieve the watchlist object
    watchlist_grid = bigdata.watchlists.get(GRID_watchlist_ID)
    # Access the items within the watchlist
    companies = bigdata.knowledge_graph.get_entities(watchlist_grid.items)

    analyzer = RiskAnalyzer(
        llm_model=llm_model,
        main_theme=risk_scenario,
        companies=companies,
        start_date="2025-01-01",
        end_date="2025-01-31",
        keywords=keywords,
        document_type=DocumentType.NEWS,
        control_entities=control_entities,
        focus=focus,  # Optional focus to narrow the theme,
    ).screen_companies(export_path=export_path)

    return analyzer


if __name__ == "__main__":

    import logging

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    # Set the logging configuration to show the logs of the library
    logging.basicConfig()
    logging.getLogger("bigdata_research_tools").setLevel(logging.INFO)

    x = risk_analyzer_example(
        "US Import Tariffs against Canada and Mexico",
        focus="Provide a detailed taxonomy of risks describing how new American import tariffs against Canada and Mexico will impact US companies, their operations and strategy. Cover trade-relations risks, foreign market access risks, supply chain risks, US market sales and revenue risks (including price impacts), and intellectual property risks, provide at least 4 sub-scenarios for each risk factor.",
    )

    df = x["df_company"]
    fig, industry_fig = create_risk_exposure_dashboard(df, n_companies=15)
    fig.show(renderer="browser")  # Shows the main dashboard
    industry_fig.show(renderer="browser")  # Shows the industry analysis
    print(df.head(10))  # Display the first 10 rows of the DataFrame

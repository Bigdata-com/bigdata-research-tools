from pathlib import Path

from bigdata_client.models.search import DocumentType

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.llm.base import LLMConfig
from bigdata_research_tools.utils.observer import OberserverNotification, Observer
from bigdata_research_tools.visuals import create_thematic_exposure_dashboard
from bigdata_research_tools.workflows import ThematicScreener


def thematic_screener_example(
    theme_name: str,
    llm_model_config: str | LLMConfig | dict = "openai::gpt-4o-mini",
    export_path: str = "thematic_screener_results.xlsx",
) -> dict:
    GRID_watchlist_ID = "814d0944-a2c1-44f6-8b42-a70c0795428e"

    bigdata = bigdata_connection()
    # Retrieve the watchlist object
    watchlist_grid = bigdata.watchlists.get(GRID_watchlist_ID)
    # Access the items within the watchlist
    companies = bigdata.knowledge_graph.get_entities(watchlist_grid.items)

    thematic_screener = ThematicScreener(
        llm_model_config=llm_model_config,
        main_theme=theme_name,
        companies=companies,
        start_date="2024-01-01",
        end_date="2024-02-28",
        document_type=DocumentType.TRANSCRIPTS,
        fiscal_year=2024,
        ground_mindmap=True,
    )

    class PrintObserver(Observer):
        def update(self, message: OberserverNotification):
            print(f"Notification received: {message}")

    thematic_screener.register_observer(PrintObserver())

    return thematic_screener.screen_companies(export_path=export_path)


if __name__ == "__main__":
    import logging

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    # Set the logging configuration to show the logs of the library
    logging.basicConfig()
    logging.getLogger("bigdata_research_tools").setLevel(logging.INFO)

    output_path = Path("outputs/thematic_screener_results.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    x = thematic_screener_example(
        "Chip Manufacturers",
        export_path=str(output_path),
        llm_model_config="openai::gpt-4o-mini",
    )
    custom_config = {
        "company_column": "Company",
        "heatmap_colorscale": "Plasma",
        "dashboard_height": 1800,
        "top_themes_count": 5,
        "main_title": "Custom Thematic Analysis Dashboard",
    }
    df = x["df_company"]
    fig, industry_fig = create_thematic_exposure_dashboard(
        df, n_companies=15, config=custom_config
    )
    fig.show(renderer="browser")  # Shows the main dashboard
    industry_fig.show(renderer="browser")  # Shows the industry analysis

from typing import Dict

from bigdata_client.models.search import DocumentType

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.workflows import ThematicScreener
from bigdata_research_tools.visuals import create_thematic_exposure_dashboard

def thematic_screener_example(
    theme_name: str, 
    llm_model: str = "openai::gpt-4o-mini",
    export_path: str = "thematic_screener_results.xlsx",
) -> Dict:

    GRID_watchlist_ID = "a60c351a-1822-4a88-8c45-a4e78abd979a"

    bigdata = bigdata_connection()
    # Retrieve the watchlist object
    watchlist_grid = bigdata.watchlists.get(GRID_watchlist_ID)
    # Access the items within the watchlist
    companies = bigdata.knowledge_graph.get_entities(watchlist_grid.items)

    thematic_screener = ThematicScreener(
        llm_model=llm_model,
        main_theme=theme_name,
        companies=companies,
        start_date="2024-01-01",
        end_date="2024-11-15",
        document_type=DocumentType.TRANSCRIPTS,
        fiscal_year=2024
    ).screen_companies(export_path=export_path)

    return thematic_screener


if __name__ == "__main__":

    import logging

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    # Set the logging configuration to show the logs of the library
    logging.basicConfig()
    logging.getLogger("bigdata_research_tools").setLevel(logging.INFO)

    x = thematic_screener_example("Chip Manufacturers")
    custom_config = {
        'company_column': 'Company',
        'heatmap_colorscale': 'Plasma',
        'dashboard_height': 1800,
        'top_themes_count': 5,
        'main_title': 'Custom Thematic Analysis Dashboard'
    }
    df = x["df_company"]
    fig, industry_fig = create_thematic_exposure_dashboard(df, n_companies=15, config=custom_config)
    fig.show(renderer="browser")           # Shows the main dashboard
    industry_fig.show(renderer="browser")  # Shows the industry analysis
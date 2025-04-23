from typing import Dict

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.workflows import ThematicScreener
from bigdata_client.models.search import DocumentType

def thematic_screener_example() -> Dict:

    GRID_watchlist_ID = "a60c351a-1822-4a88-8c45-a4e78abd979a"

    bigdata = bigdata_connection()
    # Retrieve the watchlist object
    watchlist_grid = bigdata.watchlists.get(GRID_watchlist_ID)
    # Access the items within the watchlist
    companies = bigdata.knowledge_graph.get_entities(watchlist_grid.items)

    thematic_screener = ThematicScreener(
        llm_model="openai::gpt-4o-mini",
        main_theme="Chips manufacturers",
        companies=companies,
        start_date="2024-01-01",
        end_date="2024-11-15",
        document_type=DocumentType.TRANSCRIPTS,
        fiscal_year=2024,
    ).screen_companies(export_path="thematic_screener_results.xlsx")
    return thematic_screener


if __name__ == "__main__":

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    thematic_screener_example()

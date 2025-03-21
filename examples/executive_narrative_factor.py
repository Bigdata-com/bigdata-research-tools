from typing import Dict

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.screeners import ExecutiveNarrativeFactor


def executive_narrative_example() -> Dict:

    GRID_watchlist_ID = "a60c351a-1822-4a88-8c45-a4e78abd979a"

    bigdata = bigdata_connection()
    # Retrieve the watchlist object
    watchlist_grid = bigdata.watchlists.get(GRID_watchlist_ID)
    # Access the items within the watchlist
    companies = bigdata.knowledge_graph.get_entities(watchlist_grid.items)

    executive_narrative_factor = ExecutiveNarrativeFactor(
        llm_model="openai::gpt-4o-mini",
        main_theme="Chips manufacturers",
        companies=companies,
        start_date="2024-11-01",
        end_date="2024-11-15",
        fiscal_year=2024,
    ).screen_companies(export_path="executive_narrative.xlsx")
    return executive_narrative_factor


if __name__ == "__main__":

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    executive_narrative_example()

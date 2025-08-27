#!/usr/bin/env python3
"""
Basic search_by_companies Example

This example demonstrates how to use search_by_companies to find documents
mentioning specific companies and topics.

Prerequisites:
- Set BIGDATA_USERNAME and BIGDATA_PASSWORD environment variables
- Install: uv pip install -e ".[excel,plotly,openai]" && uv pip install bigdata-client
"""

import logging
from dotenv import load_dotenv
from bigdata_client.models.search import DocumentType

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.search.screener_search import search_by_companies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Basic example of search_by_companies usage."""
    
    # Load environment variables
    print(f"Environment variables loaded: {load_dotenv()}")
    
    # Connect to Bigdata API
    bigdata = bigdata_connection()
    
    # Get some companies to search for using tickers (more reliable)
    tickers = ["AAPL", "MSFT", "TSLA"]
    companies = []

    sentences = ["AI is transforming business", "Cloud adoption is accelerating"]

    logger.info("Finding companies using tickers...")
    for ticker in tickers:
        results = bigdata.knowledge_graph.autosuggest(ticker, limit=1)
        if results:
            companies.extend(results)
            logger.info(f"Found: {results[0].name} ({ticker})")
    
    if not companies:
        logger.error("No companies found. Check ticker symbols.")
        return
    
    logger.info(f"Searching for recent news across {len(companies)} companies...")
    
    # Search for documents mentioning these companies (using working pattern)
    try:
        results_df = search_by_companies(
            companies=companies,
            sentences=sentences,                   
            start_date="2024-01-01",
            end_date="2024-06-30",            # Use a shorter, more recent range
            scope=DocumentType.NEWS,           # Search news articles
            document_limit=20,                 # More documents per query
            batch_size=5                       # Process 5 companies at a time
        )
    except ValueError as e:
        if "No rows to process" in str(e):
            logger.warning("No documents found matching the search criteria.")
            logger.info("Try:")
            logger.info("  - Different date range (e.g., more recent dates)")
            logger.info("  - Different ticker symbols (e.g., 'NVDA', 'GOOGL')")
            logger.info("  - Adding specific sentences or keywords")
            return
        else:
            raise
    
    # Display results
    if not results_df.empty:
        logger.info(f"Found {len(results_df)} relevant documents")
        
        # Show breakdown by company
        company_counts = results_df['entity_name'].value_counts()
        logger.info("Documents by company:")
        for company, count in company_counts.items():
            logger.info(f"  {company}: {count} documents")
        
        # Show some sample headlines
        logger.info("Sample headlines:")
        for headline in results_df['headline'].head(3):
            logger.info(f"  - {headline}")
        
        # Export to Excel (fix timezone issues)
        output_file = "search_by_companies_results.xlsx"
        
        # Create a copy for Excel export with timezone-naive timestamps
        excel_df = results_df.copy()
        
        # Convert any timezone-aware datetime columns to timezone-naive for Excel compatibility
        for col in excel_df.columns:
            if excel_df[col].dtype.name.startswith('datetime'):
                if excel_df[col].dt.tz is not None:
                    excel_df[col] = excel_df[col].dt.tz_localize(None)
        
        excel_df.to_excel(output_file, index=False)
        logger.info(f"Results exported to {output_file}")
        
    else:
        logger.warning("No documents found. Try different search terms or date range.")


if __name__ == "__main__":
    main()

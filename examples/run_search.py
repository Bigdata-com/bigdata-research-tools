#!/usr/bin/env python3
"""
Basic run_search Example

This example demonstrates how to use run_search with custom queries
to find documents based on specific criteria.

Prerequisites:
- Set BIGDATA_USERNAME and BIGDATA_PASSWORD environment variables
- Install: uv pip install -e ".[excel,plotly,openai]" && uv pip install bigdata-client
"""

import logging

import pandas as pd
from bigdata_client.models.search import DocumentType
from dotenv import load_dotenv

from bigdata_research_tools.search.query_builder import (
    EntitiesToSearch,
    build_batched_query,
    create_date_ranges,
)
from bigdata_research_tools.search.search import run_search

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Basic example of run_search usage."""

    # Load environment variables
    print(f"Environment variables loaded: {load_dotenv()}")

    # Define what entities we want to search for
    entities = EntitiesToSearch(
        companies=["Apple Inc", "Google", "Microsoft Corp"],
        topic=["earnings", "financial results"],
        concepts=["revenue growth", "profit margins"],
    )

    # Define search sentences
    sentences = ["quarterly earnings performance", "revenue growth and profitability"]

    logger.info("Building search queries...")

    # Build queries using the query builder
    queries = build_batched_query(
        sentences=sentences,
        keywords=["earnings", "revenue", "profit"],
        entities=entities,
        control_entities=None,
        sources=None,
        batch_size=5,
        fiscal_year=None,  # Not needed for news
        scope=DocumentType.NEWS,
        custom_batches=None,  # Use automatic batching
    )

    logger.info(f"Generated {len(queries)} search queries")

    # Create date ranges for the search
    date_ranges = create_date_ranges("2024-10-01", "2024-12-31", "M")  # Monthly
    logger.info(f"Searching across {len(date_ranges)} time periods")

    # Execute the search
    logger.info("Executing search...")

    search_results = run_search(
        queries=queries,
        date_ranges=date_ranges,
        scope=DocumentType.NEWS,
        limit=8,  # 8 documents per query
        only_results=True,  # Just return the documents
    )

    # Process the results
    all_documents = []

    for result_batch in search_results:
        for doc in result_batch:
            # Convert timezone-aware datetime to timezone-naive for Excel compatibility
            timestamp_naive = (
                doc.timestamp.replace(tzinfo=None) if doc.timestamp else None
            )

            doc_data = {
                "timestamp": timestamp_naive,
                "headline": doc.headline,
                "source": doc.source.name if doc.source else "Unknown",
                "doc_id": doc.id if hasattr(doc, "id") else "N/A",
            }
            all_documents.append(doc_data)

    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(all_documents)

    # Display results
    if not results_df.empty:
        logger.info(f"Found {len(results_df)} documents total")

        # Show source distribution
        source_counts = results_df["source"].value_counts()
        logger.info("Documents by source:")
        for source, count in source_counts.head(5).items():
            logger.info(f"  {source}: {count} documents")

        # Show some sample headlines
        logger.info("Sample headlines:")
        for headline in results_df["headline"].head(3):
            logger.info(f"  - {headline}")

        # Export to Excel
        output_file = "run_search_results.xlsx"
        results_df.to_excel(output_file, index=False)
        logger.info(f"Results exported to {output_file}")

    else:
        logger.warning("No documents found. Try different search criteria.")


if __name__ == "__main__":
    main()

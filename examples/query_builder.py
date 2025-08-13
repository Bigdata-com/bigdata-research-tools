import logging

from bigdata_client.models.search import DocumentType
from bigdata_research_tools.search.query_builder import (
    EntitiesToSearch,
    build_batched_query,
)
from bigdata_client import Bigdata
bigdata = Bigdata()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_entity_config():
    """Test basic EntityConfig functionality with auto-batching."""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic EntityConfig with Auto-batching")
    logger.info("=" * 60)
    
    # Create entity configuration
    entities = EntitiesToSearch(
        people=["Donald Trump"],
        companies=["Apple Inc", "Microsoft Corp", "Google"],
        concepts=["artificial intelligence", "machine learning"]
    )
    
    sentences = ["AI technology advances", "Machine learning innovations"]
    keywords = ["technology", "innovation"]
    
    # Build queries with auto-batching (batch_size=2)
    queries = build_batched_query(
        sentences=sentences,
        keywords=keywords,
        entities=entities,
        control_entities=None,  
        sources=None,           
        batch_size=2,
        fiscal_year=2024,
        scope=DocumentType.TRANSCRIPTS,
        custom_batches=None     
    )
    
    logger.info("Generated %d query components", len(queries))
    logger.info("Sample query structure: %s", queries)
    if queries:
        logger.info("First query type: %s", type(queries[0]))
        results = bigdata.search.new(
            queries[0],
            scope=DocumentType.TRANSCRIPTS,
            ).run(limit=2
        )
        logger.info("Sample results: %s", results)
    logger.info("")


def test_control_entities():
    """Test control entities functionality."""
    logger.info("=" * 60)
    logger.info("TEST 2: Control Entities")
    logger.info("=" * 60)
    
    # Main entities to search for
    entities = EntitiesToSearch(
        companies=["Tesla", "Ford Motor Company"],
        topic=["electric vehicles"]
    )
    
    # Control entities for co-mention analysis
    control_entities = EntitiesToSearch(
        people=["Elon Musk", "Jim Farley"],
        companies=["General Motors"],
        topic=["sustainability", "climate change"]
    )
    
    queries = build_batched_query(
        sentences=["Electric vehicle market growth"],
        keywords=None,           
        entities=entities,
        control_entities=control_entities,
        sources=None,            
        batch_size=5,
        fiscal_year=None,        
        scope=DocumentType.TRANSCRIPTS,
        custom_batches=None      
    )
    
    logger.info("Generated %d query components with control entities", len(queries))
    logger.info("Sample query structure: %s", queries)
    results = bigdata.search.new(
            queries[0],
            scope=DocumentType.TRANSCRIPTS,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results)
    logger.info("")


def test_custom_batches():
    """Test custom batch configuration."""
    logger.info("=" * 60)
    logger.info("TEST 3: Custom Batch Configuration")
    logger.info("=" * 60)
    
    # Define custom batches - each inner list is one batch
    custom_batches = [
        # Batch 1: Tech giants
        EntitiesToSearch(
            companies=["Apple Inc", "Microsoft Corp"],
            people=["Tim Cook", "Satya Nadella"],
            concepts=["technology", "innovation"]
        ),
        # Batch 2: Auto companies
        EntitiesToSearch(
            companies=["Tesla", "Ford Motor Company"],
            people=["Elon Musk", "Jim Farley"],
            concepts=["electric vehicles", "autonomous driving"]
        ),
        # Batch 3: Banks
        EntitiesToSearch(
            companies=["JPMorgan Chase", "Bank of America"],
            people=["Jamie Dimon", "Brian Moynihan"],
            concepts=["banking", "financial services"]
        )
    ]
    
    queries = build_batched_query(
        sentences=["Industry leadership and innovation"],
        keywords=["CEO", "leadership", "strategy"],
        entities=None,          
        control_entities=None,  
        sources=None,           
        batch_size=10,          
        fiscal_year=2024,       
        scope=DocumentType.FILINGS,
        custom_batches=custom_batches
    )
    
    logger.info("Query results: %s", queries)
    logger.info("Generated %d query components from custom batches", len(queries))
    results = bigdata.search.new(
            queries[0],
            scope=DocumentType.FILINGS,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results)
    logger.info("")


def test_mixed_configuration():
    """Test mixed configuration with all parameters."""
    logger.info("=" * 60)
    logger.info("TEST 4: Mixed Configuration (All Parameters)")
    logger.info("=" * 60)
    
    entities = EntitiesToSearch(
        companies=["Netflix", "Disney", "Warner Bros"],
        people=["Reed Hastings", "Bob Chapek"],
        concepts=["streaming", "entertainment", "content creation"],
        place=["Hollywood", "Los Angeles", "New York"]
    )
    
    control_entities = EntitiesToSearch(
        companies=["Hulu"],
        product=["Amazon Prime Video"],
        topic=["competition", "market share"]
    )
    
    queries = build_batched_query(
        sentences=[
            "Streaming wars and content competition",
            "Entertainment industry consolidation"
        ],
        keywords=["streaming", "content", "subscription", "audience"],
        entities=entities,
        control_entities=control_entities,
        sources=["Bloomberg", "Variety", "Hollywood Reporter"],
        batch_size=2,
        scope=DocumentType.NEWS,
        fiscal_year=None,
        custom_batches=None      
    )
    
    logger.info("Query results: %s", queries)
    logger.info("Generated %d comprehensive query components", len(queries))
    logger.info("Includes: sentences, keywords, entities, control entities, sources, fiscal year")
    results = bigdata.search.new(
            queries[0],
            scope=DocumentType.NEWS,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results)
    logger.info("")


def test_edge_cases():
    """Test edge cases and minimal configurations."""
    logger.info("=" * 60)
    logger.info("TEST 5: Edge Cases")
    logger.info("=" * 60)
    
    # Test 1: Only sentences
    queries1 = build_batched_query(
        sentences=["Market analysis report"],
        keywords=None,           
        entities=None,           
        control_entities=None,   
        sources=None,            
        batch_size=10,           
        fiscal_year=None,        
        scope=DocumentType.ALL,  
        custom_batches=None      
    )
    logger.info("Sentences only: %d queries", len(queries1))
    results1 = bigdata.search.new(
            queries1[0],
            scope=DocumentType.ALL,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results1)
    
    # Test 2: Only keywords
    queries2 = build_batched_query(
        sentences=[],
        keywords=["finance", "technology"],
        entities=None,           
        control_entities=None,   
        sources=None,            
        batch_size=10,           
        fiscal_year=None,       
        scope=DocumentType.ALL,  
        custom_batches=None      
    )
    logger.info("Keywords only: %d queries", len(queries2))
    results2 = bigdata.search.new(
            queries2[0],
            scope=DocumentType.ALL,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results2)
    
    # Test 3: Empty EntityConfig
    empty_entities = EntitiesToSearch()
    queries3 = build_batched_query(
        sentences=["Test query"],
        keywords=None,           
        entities=empty_entities,
        control_entities=None,   
        sources=None,            
        batch_size=10,           
        fiscal_year=None,        
        scope=DocumentType.ALL,  
        custom_batches=None      
    )
    logger.info("Empty entities: %d queries", len(queries3))
    results3 = bigdata.search.new(
            queries3[0],
            scope=DocumentType.ALL,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results3)
    
    # Test 4: Single entity type
    single_type = EntitiesToSearch(companies=["Apple Inc"])
    queries4 = build_batched_query(
        sentences=["Apple earnings"],
        keywords=None,           
        entities=single_type,
        control_entities=None,   
        sources=None,            
        batch_size=1,
        fiscal_year=None,        
        scope=DocumentType.ALL,  
        custom_batches=None      
    )
    logger.info("Single entity type: %d queries", len(queries4))
    results4 = bigdata.search.new(
            queries4[0],
            scope=DocumentType.ALL,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results4)
    logger.info("")


def test_reporting_entities():
    """Show reporting entities are set for companies."""
    logger.info("=" * 60)
    logger.info("TEST 6: Reporting Entities")
    logger.info("=" * 60)
    
    entities = EntitiesToSearch(
        companies=["Netflix", "Disney", "Warner Bros"],
        people=["Reed Hastings", "Bob Chapek"],
        concepts=["streaming", "entertainment", "content creation"],
        place=["Hollywood", "Los Angeles", "New York"]
    )
    
    queries = build_batched_query(
        sentences=[
            "Streaming wars and content competition",
            "Entertainment industry consolidation"
        ],
        keywords=["streaming", "content", "subscription", "audience"],
        entities=entities,
        control_entities=None,
        batch_size=2,
        fiscal_year=2024,
        sources=None,
        scope=DocumentType.TRANSCRIPTS,
        custom_batches=None      
    )
    
    logger.info("Query results: %s", queries)
    logger.info("Generated %d comprehensive query components", len(queries))
    logger.info("Includes: sentences, keywords, entities, fiscal year")
    results = bigdata.search.new(
            queries[0],
            scope=DocumentType.TRANSCRIPTS,
            ).run(limit=2
        )
    logger.info("Sample results: %s", results)
    logger.info("")

def main():
    """Run all tests."""
    logger.info("Testing Refactored build_batched_query Function")
    logger.info("=" * 60)
    
    try:
        test_basic_entity_config()
        test_control_entities()
        test_custom_batches()
        test_mixed_configuration()
        test_edge_cases()
        test_reporting_entities()
        
        logger.info("=" * 60)
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error("Error during testing: %s", e)
        raise


if __name__ == "__main__":
    main()
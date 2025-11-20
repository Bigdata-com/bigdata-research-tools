import logging

from dotenv import load_dotenv

from bigdata_research_tools.lexicon import LexiconGenerator

# Load environment variables for authentication
print(f"Environment variables loaded: {load_dotenv()}")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_keyword_generation(
    main_theme,
    llm_base_config: str = "openai::gpt-4o-mini",
):
    
    logger.info("=" * 60)
    logger.info("TEST 1: Keyword Generation with LLM")
    logger.info("=" * 60)
    lexicon_generator = LexiconGenerator(
        main_theme=main_theme,
        llm_model_config=llm_base_config,
        mode = 'keywords',
    )

    results = lexicon_generator.generate_lexicon(
    )
    
    logger.info("Results: %s", results)

def test_sentence_generation(
    main_theme,
    llm_base_config: str = "openai::o3-mini",
):
    logger.info("=" * 60)
    logger.info("TEST 2: Test Sentence Generation with LLM")
    logger.info("=" * 60)
    lexicon_generator = LexiconGenerator(
        main_theme=main_theme,
        llm_model_config=llm_base_config,
        mode = 'sentences',
    )

    results = lexicon_generator.generate_lexicon(
    )
    
    logger.info("Results: %s", results)

def main(
    main_theme="Crude Oil Market",):
    """Run all tests."""
    logger.info("Testing Lexicon Generation")
    logger.info("=" * 60)

    try:
        
        test_keyword_generation(main_theme)

        test_sentence_generation(main_theme)

        logger.info("=" * 60)
        logger.info("All tests completed successfully")

    except Exception as e:
        logger.error("Error during testing: %s", e)
        raise


if __name__ == "__main__":
    main()
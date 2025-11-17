import logging

from bigdata_client import Bigdata
from bigdata_client.models.search import DocumentType
from dotenv import load_dotenv
from traitlets import Any

from bigdata_research_tools.mindmap.mindmap import MindMap
from bigdata_research_tools.mindmap.mindmap_generator import MindMapGenerator

# Load environment variables for authentication
print(f"Environment variables loaded: {load_dotenv()}")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_one_shot_mindmap(main_theme, focus, map_type, instructions, llm_base_config: str = "openai::gpt-4o-mini") -> MindMap:
    """Test one-shot mind map generation with base LLM."""
    logger.info("=" * 60)
    logger.info("TEST 1: One-Shot Mind Map Generation with Base LLM")
    logger.info("=" * 60)
    mindmap_generator = MindMapGenerator(llm_model_config_base=llm_base_config,)
    mindmap = mindmap_generator.generate_one_shot(
    instructions=instructions,
    focus=focus,
    main_theme=main_theme,
    map_type = map_type,
    allow_grounding=False,
)
    logger.info("Results: %s", mindmap['mindmap_text'])
    return mindmap["mindmap_json"]
    
    
def test_refined_mindmap(main_theme, focus, map_type, instructions, base_mindmap: str, llm_base_config: str = "openai::o3-mini") -> MindMap:
    """Test refined mindmap generation with reasoning LLM sent in the base config."""
    logger.info("=" * 60)
    logger.info("TEST 2: Refined MindMap Generation with Reasoning LLM in Base Config")
    logger.info("=" * 60)
    mindmap_generator = MindMapGenerator(llm_model_config_base=llm_base_config,)
    mindmap = mindmap_generator.generate_refined(focus = focus,
                                                 main_theme = main_theme,
                                                 initial_mindmap = base_mindmap,
                                                 grounding_method = "tool_call",
                                                 output_dir = "./refined_mindmaps",
                                                 filename = "refined_mindmap.json",
                                                 map_type = map_type,
                                                 instructions = instructions,
                                                 )
    logger.info("Results: %s", mindmap['mindmap_text'])

def test_refined_mindmap2(main_theme, focus, map_type, instructions, base_mindmap: str, llm_base_config: str | None = None, llm_reasoning_config: str = "openai::o3-mini") -> MindMap:
    """Test refined mindmap generation with reasoning LLM sent in the reasoning config."""
    logger.info("=" * 60)
    logger.info("TEST 3: Refined MindMap Generation with Reasoning LLM in Reasoning Config")
    logger.info("=" * 60)
    mindmap_generator = MindMapGenerator(llm_model_config_base=llm_base_config, llm_model_config_reasoning=llm_reasoning_config)
    mindmap = mindmap_generator.generate_refined(focus = focus,
                                                 main_theme = main_theme,
                                                 initial_mindmap = base_mindmap,
                                                 grounding_method = "tool_call",
                                                 output_dir = "./refined_mindmaps",
                                                 filename = "refined_mindmap.json",
                                                 map_type = map_type,
                                                 instructions = instructions,
                                                 )
    logger.info("Results: %s", mindmap['mindmap_text'])

def test_dynamic_mindmap(main_theme, focus, map_type, instructions, llm_base_config: str = "openai::gpt-4o-mini", llm_reasoning_config: str = "openai::o3-mini") -> MindMap:
    """Test dynamic mindmap generation with two LLMs."""
    logger.info("=" * 60)
    logger.info("TEST 4: Dynamic MindMap Generation with Two LLMs")
    logger.info("=" * 60)
    mindmap_generator = MindMapGenerator(llm_model_config_base=llm_base_config, llm_model_config_reasoning=llm_reasoning_config)
    mindmap = mindmap_generator.generate_dynamic(
        instructions = instructions,
        focus = focus,
        main_theme = main_theme,
        month_intervals = [["2025-10-01", "2025-10-31"], ["2025-11-01", "2025-11-30"], ["2025-12-01", "2025-12-31"]],
        month_names = ['October_2025', 'November_2025', 'December_2025'],)
    logger.info("Results: %s", mindmap['base_mindmap'])
    logger.info("Results: %s", mindmap['October_2025'])
    logger.info("")

def main(MAIN_THEME = "Political Change in Japan.",
         INSTRUCTIONS = 'Create a mindmap according to a given risk scenario. Map by risk type for any industry and assess short term impact only.',
         FOCUS = "Provide a detailed taxonomy of risks related to changes in the Japanese political landscape. Evaluate how the resignation of the Prime Minister and the pre-election of Sanae Takaichi will affect companies, their strategy and operations. Take into consideration their increased conservative stance on immigration, energy, and trade. Add any other risk areas that may arise from these political changes. The mind map should be as comprehensive as possible and cover all major risk areas.",
         map_type = 'risk'):
    """Run all tests."""
    logger.info("Testing Grounded MindMap Generation")
    logger.info("=" * 60)

    try:
        base_mindmap = test_one_shot_mindmap(MAIN_THEME, FOCUS, map_type, INSTRUCTIONS, llm_base_config="openai::gpt-4o-mini")
        test_refined_mindmap(MAIN_THEME, FOCUS, map_type, INSTRUCTIONS, base_mindmap, llm_base_config="openai::o3-mini")
        test_refined_mindmap2(MAIN_THEME, FOCUS, map_type, INSTRUCTIONS, base_mindmap, llm_base_config="openai::o3-mini")
        test_dynamic_mindmap(MAIN_THEME, FOCUS, map_type, INSTRUCTIONS, llm_base_config="openai::gpt-4o-mini", llm_reasoning_config="openai::o3-mini")

        logger.info("=" * 60)
        logger.info("All tests completed successfully")

    except Exception as e:
        logger.error("Error during testing: %s", e)
        raise

if __name__ == "__main__":
    main()

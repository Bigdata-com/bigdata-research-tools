from pathlib import Path

from bigdata_client.models.search import DocumentType

from bigdata_research_tools.llm.base import LLMConfig
from bigdata_research_tools.utils.observer import OberserverNotification, Observer
from bigdata_research_tools.workflows import NarrativeMiner


def narrative_miner_example(
    llm_model_config: str | LLMConfig | dict = "openai::gpt-4o-mini",
    export_path: str = "narrative_miner_sample.xlsx",
) -> dict:
    narrative_miner = NarrativeMiner(
        narrative_sentences=[
            "Supervised Learning Techniques",
            "Unsupervised Learning Approaches",
            "Reinforcement Learning Systems",
            "Text Analysis and Sentiment Detection",
            "Speech Recognition Technologies",
            "Chatbot and Conversational AI",
            "Image Recognition Systems",
            "Facial Recognition Innovations",
            "Augmented Reality Applications",
            "Autonomous Navigation Systems",
            "Collaborative Robots (Cobots)",
            "Industrial Automation Solutions",
            "Bias Detection and Mitigation",
            "Transparency and Explainability Tools",
            "Data Privacy Solutions",
        ],
        sources=None,
        llm_model_config=llm_model_config,
        start_date="2024-11-01",
        end_date="2024-11-15",
        rerank_threshold=None,
        document_type=DocumentType.TRANSCRIPTS,
        fiscal_year=2024,
    )

    class PrintObserver(Observer):
        def update(self, message: OberserverNotification):
            print(f"Notification received: {message}")

    narrative_miner.register_observer(PrintObserver())

    return narrative_miner.mine_narratives(export_path=export_path)


if __name__ == "__main__":
    import logging

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    # Set the logging configuration to show the logs of the library
    logging.basicConfig()
    logging.getLogger("bigdata_research_tools").setLevel(logging.INFO)

    output_path = Path("outputs/narrative_miner_sample.xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    narrative_miner_example(
        export_path=str(output_path),
        llm_model_config={"model": "openai::gpt-5-mini", "temperature": 0},
    )

from typing import Dict

from bigdata_client.models.search import DocumentType

from bigdata_research_tools.workflows import NarrativeMiner


def narrative_miner_example(export_path: str = "narrative_miner_sample.xlsx") -> Dict:

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
        llm_model="openai::gpt-4o-mini",
        start_date="2024-11-01",
        end_date="2024-11-15",
        rerank_threshold=None,
        document_type=DocumentType.TRANSCRIPTS,
        fiscal_year=2024,
    )

    return narrative_miner.mine_narratives(export_path=export_path)


if __name__ == "__main__":

    import logging

    from dotenv import load_dotenv

    # Load environment variables for authentication
    print(f"Environment variables loaded: {load_dotenv()}")

    # Set the logging configuration to show the logs of the library
    logging.basicConfig()
    logging.getLogger("bigdata_research_tools").setLevel(logging.INFO)

    narrative_miner_example()

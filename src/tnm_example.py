from typing import Dict

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.miners.transcripts_narrative_miner import TranscriptsNarrativeMiner

def example(output_file_str: str = "transcripts_narrative_scores.xlsx") -> Dict:

    bigdata = bigdata_connection()

    transcripts_miner = TranscriptsNarrativeMiner(
        theme_labels=[
            'Supervised Learning Techniques',
            'Unsupervised Learning Approaches',
            'Reinforcement Learning Systems',
            'Text Analysis and Sentiment Detection',
            'Speech Recognition Technologies',
            'Chatbot and Conversational AI',
            'Image Recognition Systems',
            'Facial Recognition Innovations',
            'Augmented Reality Applications',
            'Autonomous Navigation Systems',
            'Collaborative Robots (Cobots)',
            'Industrial Automation Solutions',
            'Bias Detection and Mitigation',
            'Transparency and Explainability Tools',
            'Data Privacy Solutions'
        ],
        sources=None, 
        fiscal_year=2024,
        llm_model="openai::gpt-4o-mini",
        start_date="2024-01-01",
        end_date="2024-12-31",
        rerank_threshold=None
    )

    return transcripts_miner.mine_narratives(export_to_path=output_file_str)


if __name__ == '__main__':

    from dotenv import load_dotenv

    # Load environment variables for authentication
    load_dotenv()
    example()

from typing import Dict

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.miners.news_narrative_miner import NewsNarrativeMiner

def example(watchlist_id: str, 
            output_file_str: str = "news_narrative_scores.xlsx") -> Dict:

    bigdata = bigdata_connection()
    # Retrieve the watchlist object
    GRID_watchlist = bigdata.watchlists.get(watchlist_id)

    news_miner = NewsNarrativeMiner(
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
        llm_model="openai::gpt-4o-mini",
        start_date="2024-11-01",
        end_date="2024-11-15",
        rerank_threshold=None
    )

    return news_miner.mine_narratives(export_to_path=output_file_str)


if __name__ == '__main__':

    from dotenv import load_dotenv

    # Load environment variables for authentication
    load_dotenv()
    watchlist_id = 'a60c351a-1822-4a88-8c45-a4e78abd979a'  # Input your watchlist ID here
    if not watchlist_id:
        raise ValueError("Please replace watchlist_id with a watchlist id you own")
    
    example(watchlist_id)

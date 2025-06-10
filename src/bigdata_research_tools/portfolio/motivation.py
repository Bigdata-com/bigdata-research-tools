import pandas as pd
from collections import defaultdict
from typing import Tuple, Dict, Any
from tqdm import tqdm 

from bigdata_research_tools.prompts.motivation import get_motivation_prompt
from bigdata_research_tools.llm.base import LLMEngine


class Motivation:
    """
    A class for generating motivation statements for companies based on thematic analysis.
    """
    
    def __init__(self, model: str = None, model_config: Dict[str, Any] = None):
        """
        Initialize the Motivation class.
        
        Parameters:
        - model: Model string in format "provider::model" (e.g., "openai::gpt-4o-mini")
        - model_config: Configuration for the LLM model
        """
        self.model_config = model_config or self._get_default_model_config()
        self.llm_engine = LLMEngine(model=model)
    
    @staticmethod
    def _get_default_model_config() -> Dict[str, Any]:
        """Get default LLM model configuration."""
        return {
            "temperature": 0,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "max_tokens": 300,
            "seed": 42,
        }
    
    def group_quotes_by_company(self, filtered_df: pd.DataFrame) -> Dict:
        """
        Group quotes and labels by company.
        
        Parameters:
        - filtered_df: DataFrame filtered by theme
        
        Returns:
        - Dictionary with company data
        
        Raises:
        - ValueError: If required columns are missing from the DataFrame
        """
        # Check for required columns
        required_columns = ['Company', 'Quote', 'Theme']
        missing_columns = [col for col in required_columns if col not in filtered_df.columns]
        
        if missing_columns:
            available_columns = list(filtered_df.columns)
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Available columns are: {available_columns}"
            )
        
        # Check if DataFrame is empty
        if filtered_df.empty:
            print("Warning: DataFrame is empty. Returning empty dictionary.")
            return {}
        
        company_data = defaultdict(lambda: {'quotes_and_labels': []})
        
        # Use .get() with default values as additional safety
        for _, row in filtered_df.iterrows():
            company = row.get('Company', 'Unknown Company')
            quote = row.get('Quote', '')
            theme = row.get('Theme', 'Unknown Theme')
            
            # Skip rows with missing essential data
            if not company or not quote:
                continue
                
            company_data[company]['quotes_and_labels'].append({
                'quote': quote,
                'label': theme
            })
        
        print(f"Found {len(company_data)} unique companies with quotes")
        
        # Count label occurrences for each company
        for company, data in company_data.items():
            label_counts = {}
            for item in data['quotes_and_labels']:
                label = item['label']
                label_counts[label] = label_counts.get(label, 0) + 1
            
            # Sort labels by frequency (highest first)
            sorted_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
            company_data[company]['label_counts'] = sorted_labels
            company_data[company]['total_quotes'] = len(data['quotes_and_labels'])
        
        return company_data
    
    def query_llm_for_motivation(self, prompt: str) -> str:
        """
        Generate motivation statement using LLM Engine.
        
        Parameters:
        - prompt (str): Formatted prompt string
        
        Returns:
        - Generated motivation statement
        """
        chat_history = [{"role": "user", "content": prompt}]
        
        motivation = self.llm_engine.get_response(
            chat_history=chat_history,
            **self.model_config
        )
        
        return motivation.strip()
    
    def generate_company_motivations(self, 
                                df: pd.DataFrame, 
                                theme_name: str, 
                                word_range: Tuple[int, int]) -> pd.DataFrame:
        """
        Generates motivation statement with specified verbosity for companies in a thematic watchlist.
        
        Parameters:
        - df (pd.DataFrame): DataFrame with columns: Company, Quote, Label, Theme
        - theme_name (str): Name of the theme to filter by
        - word_range (Tuple[int, int]): Tuple (min_words, max_words) defining motivation length
        
        Returns:
        - DataFrame with company motivations in multiple lengths
        """
        company_data = self.group_quotes_by_company(df)
        
        # Generate motivations for each company
        results = []
        
        # Use tqdm for progress tracking
        for company, data in tqdm(company_data.items(), 
                                desc=f"Generating motivations for {len(company_data)} companies",
                                unit="company"):
            
            # Create prompt for this word range
            prompt = get_motivation_prompt(company, data, theme_name, word_range[0], word_range[1])
                
            # Generate motivation with this word range
            motivation = self.query_llm_for_motivation(prompt)
            
            results.append({
                'Company': company,
                'Motivation': motivation,
                'Composite Score': data['total_quotes']
            })
        
        # Create and return sorted DataFrame
        return (pd.DataFrame(results)
                .sort_values("Composite Score", ascending=False)
                .reset_index(drop=True))
    
    def update_model_config(self, config: Dict[str, Any]):
        """Update the model configuration."""
        self.model_config.update(config)

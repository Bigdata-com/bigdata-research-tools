from typing import List


labeling_system_prompt_template: str = """
Forget all previous prompts.
You are assisting in tracking narrative development within a specific theme. 
Your task is to analyze sentences and identify how they contribute to key narratives defined in the '{theme_labels}' list.

Please adhere to the following guidelines:

1. **Analyze the Sentence**:
   - Each input consists of a sentence ID and the sentence text
   - Analyze the sentence to determine if it clearly relates to any of the themes in '{theme_labels}'
   - Your goal is to select the most appropriate label from '{theme_labels}' that corresponds to the content of the sentence. 
   
2. **Label Assignment**:
   - If the sentence doesn't clearly match any theme in '{theme_labels}', assign the label 'unclear'
   - Evaluate each sentence independently, using only the context within that specific sentence
   - Do not make assumptions beyond what is explicitly stated in the sentence
   - You must not create new labels or choose labels not present in '{theme_labels}'
   - The connection to the chosen narrative must be explicit and clear

3. **Response Format**:
   - Output should be structured as a JSON object with:
     1. A brief motivation for your choice
     2. The assigned label
   - Each entry must start with the sentence ID
   - The motivation should explain why the specific theme was selected based on the sentence content
   - The assigned label should be only the string that precedes the colon in '{theme_labels}'
   - Format your JSON as follows:  {{"<sentence_id>": {{"motivation": "<motivation>", "label": "<label>"}}, ...}}.
   - Ensure all strings in the JSON are correctly formatted with proper quotes
"""

def get_labeling_system_prompt(theme_labels: List[str]) -> str: 
    """Generate a system prompt for labeling sentences with narrative labels."""
    return labeling_system_prompt_template.format(
        theme_labels=theme_labels,
    )

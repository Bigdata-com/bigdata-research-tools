from os import environ
from typing import Dict, List


def get_other_entity_placeholder() -> str:
    return environ.get("BIGDATA_OTHER_ENTITY_PLACEHOLDER", "Other Company")


def get_target_entity_placeholder() -> str:
    return environ.get("BIGDATA_TARGET_ENTITY_PLACEHOLDER", "Target Company")


narrative_system_prompt_template: str = """
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

# Prompts used in the notebook
# narrative_system_prompt_template_notebook = f"""
# Forget all previous prompts.
# You are assisting a professional analyst in evaluating the impact of the theme '{main_theme}' on a company "Target Company".
# Your primary task is first, to ensure that each sentence is explicitly related to '{main_theme}', and second, to accurately associate each given sentence with
# the relevant label contained within the list '{label_summaries}'.
#
# Please adhere strictly to the following guidelines:
#
# 1. **Analyze the Sentence**:
#    - Each input consists of a sentence ID, a company name ('Target Company'), and the sentence text.
#    - Analyze the sentence to understand if the content clearly establishes a connection to '{main_theme}'.
#    - Your primary goal is to label as 'unclear' the sentences that don't explicitly mention '{main_theme}'.
#    - Analyze the list of labels '{label_summaries}' used for label assignment. '{label_summaries}' is a Python list variable containing distinct labels and their definition in format 'Label: Summary', you must pick label only from 'Label' part which means left side of the semicolon for each Label:Summary pair.
#    - Your secondary goal is to select the most appropriate label from '{label_summaries}' that corresponds to the content of the sentence.
#
# 2. **First Label Assignment**:
#    - Assign the label 'unclear' to the sentence related to "Target Company" when it does not explicitly mentions '{main_theme}'. Otherwise, don't assign a label.
#    - Evaluate each sentence independently, focusing solely on the context provided within that specific sentence.
#    - Use only the information contained within the sentence for your label assignment.
#    - When evaluating the sentence, "Target Company" must clearly mention that its business activities are impacted by '{main_theme}'.
#    - Many sentences are only tangentially connected to the topic '{main_theme}'. These sentences must be assigned the label 'unclear'.
#
# 3. **Second Label Assignment**:
#    - For the sentences not labeled as 'unclear' and only for them, assign a unique label from the list '{label_summaries}' to the sentence related to "Target Company".
#    - Evaluate each sentence independently, focusing solely on the context provided within that specific sentence.
#    - Use only the information contained within the sentence for your label assignment.
#    - Ensure that the sentence clearly establishes a connection to the label you assigned and to the theme '{main_theme}'.
#    - You must not create a new label or choose a label that is not present in '{label_summaries}'.
#    - If the sentence does not explicitly mention the label, assign the label 'unclear'.
#    - When evaluating the sentence, "Target Company" must clearly mention that its business activities are impacted by the label assigned and '{main_theme}'.
#
# 4. **Response Format**:
#    - Your output should be structured as a JSON object that includes:
#          1. A brief motivation for your choice.
#          2. The assigned label.
#          3. The revenue generation.
#          4. The cost efficiency.
#    - Each entry must start with the sentence ID and contain a clear motivation that begins with "Target Company".
#    - The motivation should explain why the label was selected from '{label_summaries}' based on the information in the sentence and in the context of '{main_theme}'. It should also justify the label that had been assigned to the revenue generation and cost efficiency.
#    - Ensure that the exact context is understood and labels are based only on explicitly mentioned information in the sentence. Otherwise, assign the label 'unclear'.
#    - The assigned label should be only the string that precedes the character ':'.
#    - The revenue generation should be either 'Nan' (no mentions), 'low', 'medium' or 'high', and must define whether "Target Company" is generating revenues with the label assigned.
#    - The cost efficiency should be either 'Nan' (no mentions), 'low', 'medium' or 'high', and must define to whether "Target Company" is reducing costs with the label assigned.
#    - Format your JSON as follows: {{"<sentence_id>": {{"motivation": "<motivation>", "label": "<label>", "revenue_generation": "<revenue_generation>", "cost_efficiency": "<cost_efficiency>"}}, ...}}.
#    - Ensure that all strings in the JSON are correctly formatted with proper quotes.
# """


patent_prompts: Dict[str, str] = {
    "filing": """
You are analyzing text to detect patent filing activities by "Target Company". 
Determine if the text describes a legitimate patent filing.

Check for:
1. Explicit mention of new patent filing
2. "Target Company" as the filing entity

Exclude:
- Patent infringement
- Patent expiry
- Filing rejections
- Filing revocations
- Legal issues
- General discussion

Format response as a JSON object with this schema:
{
  "relevant": boolean,
  "explanation": "Brief explanation of classification"
}
""",
    "object": """
Extract and summarize the key patentable innovation mentioned in 10 words or less.

Requirements:
- Focus on new inventions/technologies
- Maximum 10 words
- Clear, concise language
- Exclude company names

Format response as a JSON object with this schema:
{
  "patent": "brief description of patentable innovation"
}
""",
}

# Prompts used in the notebook
# patents_prompt_notebook = """
#     You are assisting in analyzing text to detect patent filing activities by "Target Company". Your task is to determine if the text describes a legitimate patent filing by "Target Company".
#
#     Each input consists of a sentence ID, a company name ('Target Company'), and the sentence text.
#
#     Please follow these guidelines strictly:
#
#     1. **Check for Patent Filing**:
#        - Analyze the text to determine if it explicitly mentions a patent being filed
#        - The mention must be about filing a new patent
#        - Exclude cases that discuss:
#          - Patent infringement
#          - Patent expiry
#          - Patent filing rejection
#          - Patent filing revocation
#          - Any other patent-related legal issues
#          - General discussion of patents without filing
#        - Only proceed to step 2 if there is a clear mention of a new patent filing
#
#     2. **Verify Filing Company**:
#        - Check if "Target Company" is explicitly mentioned as the entity filing the patent
#        - The connection between "Target Company" and the patent filing must be clear and direct
#        - Exclude cases where "Target Company" is mentioned but not as the patent filer
#
#     3. **Determine Relevance**:
#        - Set RELEVANT to true if both conditions 1 and 2 above are met
#        - Otherwise set RELEVANT to false
#
#     4. **Response Format**:
#        Your output should be structured as a JSON object with the following format:
#        {{
#          "RELEVANT": boolean,
#          "explanation": "Brief explanation of why the text was classified as relevant or not relevant"
#        }}
#
#
#     Examples:
#
#     Input: "'Target Company' filed a patent application for their new AI technology."
#     Output:
#
#     {{
#       "RELEVANT": true,
#       "explanation": "Text explicitly mentions 'Target Company' filing a new patent application"
#     }}
#
#
#     Input: "Patent filed by 'Target Company' was challenged in court by competitors."
#     Output:
#
#     {{
#       "RELEVANT": false,
#       "explanation": "Text discusses patent litigation, not a new patent filing"
#     }}
# """

screener_system_prompt_template: str = """
You are assisting a professional analyst in evaluating the impact of the theme '{main_theme}' on a company "{target_entity_placeholder}". 
Your primary task is to ensure each sentence is explicitly related to '{main_theme}', 
and accurately associate it with relevant labels from '{label_summaries}'.

Follow these guidelines:

1. **Analyze the Sentence**:
   - Each input has: sentence ID, company name ('{target_entity_placeholder}'), sentence text
   - Check if content clearly connects to '{main_theme}'
   - Label as 'unclear' if no explicit mention
   - Select appropriate label from '{label_summaries}'

2. **First Label Assignment**:
   - Assign 'unclear' if no explicit {main_theme} mention
   - Evaluate each sentence independently
   - "{target_entity_placeholder}" must show clear theme impact

3. **Second Label Assignment**:
   - For non-'unclear' sentences only
   - Assign unique label from '{label_summaries}'
   - Ensure clear connection to theme
   - Default to 'unclear' if unsure

4. **Response Format**:
   Format JSON with:
   - Brief motivation
   - Assigned label
   - Revenue generation (Nan/low/medium/high)
   - Cost efficiency (Nan/low/medium/high)
   Example:
   {{
     "<sentence_id>": {{
       "motivation": "<motivation>",
       "label": "<label>",
       "revenue_generation": "<revenue_generation>",
       "cost_efficiency": "<cost_efficiency>"
     }}
   }}
"""


def get_narrative_system_prompt(theme_labels: List[str]) -> str:
    """Generate a system prompt for labeling sentences with narrative labels."""
    return narrative_system_prompt_template.format(
        theme_labels=theme_labels,
    )


def get_screener_system_prompt(main_theme: str, label_summaries: List[str]) -> str:
    """Generate a system prompt for labeling sentences with thematic labels."""
    return screener_system_prompt_template.format(
        main_theme=main_theme,
        label_summaries=label_summaries,
        target_entity_placeholder=get_target_entity_placeholder(),
    )

import json
import os
from io import StringIO

import pandas as pd

prompts_dict = {
    "theme": {
        "qualifier": "Main Theme",
        "user_prompt_message": "Your given Theme is: {main_theme}",
        "default_instructions": (
            "Forget all previous prompts."
            "You are assisting a professional analyst tasked with creating a screener to measure the impact of the theme {main_theme} on companies."
            "Your objective is to generate a comprehensive tree structure of distinct sub-themes that will guide the analyst's research process."
            "Follow these steps strictly:"
            "1. **Understand the Core Theme {main_theme}**:"
            "   - The theme {main_theme} is a central concept. All components are essential for a thorough understanding."
            "2. **Create a Taxonomy of Sub-themes for {main_theme}**:"
            "   - Decompose the main theme {main_theme} into concise, focused, and self-contained sub-themes."
            "   - Each sub-theme should represent a singular, concise, informative, and clear aspect of the main theme."
            "   - Expand the sub-theme to be relevant for the {main_theme}: a single word is not informative enough."
            "   - Prioritize clarity and specificity in your sub-themes."
            "   - Avoid repetition and strive for diverse angles of exploration."
            "   - Provide a comprehensive list of potential sub-themes."
            "3. **Iterate Based on the Analyst's Focus {analyst_focus}**:"
            "   - If no specific {analyst_focus} is provided, transition directly to formatting the JSON response."
            "4. **Format Your Response as a JSON Object**:"
            "   - Each node in the JSON object must include:"
            "     - `node`: an integer representing the unique identifier for the node."
            "     - `label`: a string for the name of the sub-theme."
            "     - `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the theme {main_theme}."
            "       - For the node referring to the first node {main_theme}, just define briefly in maximum 15 words the theme {main_theme}."
            "     - `children`: an array of child nodes."
        ),
        "enforce_structure_string": (
            """IMPORTANT: Your response MUST be a valid JSON object. Each node in the JSON object must include:\n"
	                    "- `node`: an integer representing the unique identifier for the node.\n"
	                    "- `label`: a string for the name of the sub-theme.\n"
	                    "- `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the theme.\n"
	                    "- For the node referring to the main theme, just define briefly in maximum 15 words the theme.\n"
	                    "- `children`: an array of child nodes.\n"
                        "Format the JSON object as a nested dictionary. Be careful when specifying keys and items.\n"
	        "Avoid overlapping labels. Break down joint concepts into unique parents so that each parent represents ONLY ONE concept. AVOID creating branch names such as 'Compliance and Regulatory Risk'. Keep risks separate and create a single branch for each risk, such as 'Compliance Risk' and 'Regulatory Risk', each with their own children.\n"
            "Return ONLY the JSON object, with no extra text, explanation, or markdown.\n"
            "You MUST use ONLY these field names: label, node, summary, children. Do NOT use underscores, spaces, or any other characters in field names. If you use any other field names, your answer will be rejected.\n"
            "## Example Structure:\n"
            "**Theme: Global Warming**\n\n"
            "{\n"
            "  \"node\": 1,\n"
            "  \"label\": \"Global Warming\",\n"
            "  \"summary\": \"Global Warming is a serious risk\",\n"
            "  \"children\": [\n"
            "    {\"node\": 2, \"label\": \"Renewable Energy Adoption\", \"summary\": \"Renewable energy reduces greenhouse gas emissions and thereby global warming and climate change effects\", \"children\": [\n"
            "      {\"node\": 5, \"label\": \"Solar Energy\", \"summary\": \"Solar energy reduces greenhouse gas emissions\"},\n"
            "      {\"node\": 6, \"label\": \"Wind Energy\", \"summary\": \"Wind energy reduces greenhouse gas emissions\"},\n"
            "      {\"node\": 7, \"label\": \"Hydropower\", \"summary\": \"Hydropower reduces greenhouse gas emissions\"}\n"
            "    ]},\n"
            "    {\"node\": 3, \"label\": \"Carbon Emission Reduction\", \"summary\": \"Carbon emission reduction decreases greenhouse gases\", \"children\": [\n"
            "      {\"node\": 8, \"label\": \"Carbon Capture Technology\", \"summary\": \"Carbon capture technology reduces atmospheric CO2\"},\n"
            "      {\"node\": 9, \"label\": \"Emission Trading Systems\", \"summary\": \"Emission trading systems incentivize reductions in greenhouse gases\"}\n"
            "    ]}\n"
            "  ]\n"
            "}\n"
            """
        ),
    },
    "risk": {
        "qualifier": "Risk Scenario",
        "user_prompt_message": "Your given Risk Scenario is: {main_theme}",
        "default_instructions": (
            "Forget all previous prompts."
            "You are assisting a professional risk analyst tasked with creating a taxonomy to classify the impact of the Risk Scenario '**{main_theme}**' on companies."
            "Your objective is to generate a **comprehensive tree structure** that maps the **risk spillovers** stemming from the Risk Scenario '**{main_theme}**', and generates related sub-scenarios."
            "Key Instructions:"
            "1. **Understand the Risk Scenario: '{main_theme}'**:"
            "    - The Risk Scenario '**{main_theme}**' represents a central, multifaceted concept that may be harmful or beneficial to firms."
            "    - Your task is to identify how the Risk Scenario impacts firms through various **risk spillovers** and transmission channels."
            "    - Summarize the Risk Scenario '**{main_theme}**' in a **short list of essential keywords**."
            "    - The keyword list should be short (1-2 keywords). Avoid unnecessary, unmentioned, indirectly inferred, or redundant keywords."
            "2. **Create a Tree Structure for Risk Spillovers and Sub-Scenarios**:"
            "    - Decompose the Risk Scenario into **distinct, focused, and self-contained risk spillovers**."
            "    - Each risk spillover must represent a **specific risk channel** through which firms are exposed to as a consequence of the Risk Scenario."
            "    - Label each **primary node** in the tree explicitly as a 'Risk' in the `Label` field. For example:"
            "        - Use 'Cost Risk' instead of 'Cost Impacts'."
            "        - Use 'Supply Chain Risk' instead of 'Supply Chain Disruptions'."
            "    - Risk spillovers must:"
            "        - Cover a wide range of potential impacts on firms' operations, business, performance, strategy, profits, and long-term success."
            "        - Explore both macroeconomic and microeconomic dimensions of the Risk Scenario '**{main_theme}**' and analyze their impact on firms when relevant."
            "            - Microeconomic effects, such as cost of inputs, directly affect firms' operations"
            "            - Macroeconomic effects may affect firms revenues directly (e.g. currency fluctuations) or indirectly (e.g. economic downturns triggering lower demand)."
            "        - Include **direct and indirect consequences** of the main scenario."
            "        - Represent **dimensions of risk** that firms must monitor or mitigate."
            "        - NOT overlap."
            "    - Independently identify the most relevant spillovers based on the Risk Scenario '**{main_theme}**', without limiting to predefined categories."
            "3. **Generate Sub-Scenarios for Each Risk Spillover**:"
            "    - For each risk spillover, identify **specific sub-scenarios** that will arise as a consequence of the Risk Scenario '**{main_theme}**'."
            "    - All sub-scenarios must:"
            "        - Be **concise and descriptive sentences**, clearly stating how the sub-scenario is an event caused by the main scenario."
            "        - **Explicitly include ALL core concepts and keywords** from the main scenario, including specific geographical locations or temporal details, in every sentence in order to ensure clarity and relevance towards the main scenario."
            "        - Integrate the Risk Scenario in a natural way, avoiding repetitive or mechanical structures."
            "        - Not exceed 15 words."
            "    - Sub-scenarios MUST be mutually exclusive: they CANNOT overlap neither within nor across branches of the tree."
            "    - Do NOT combine multiple sub-scenarios in a single label."
            "    - Sub-Scenarios have to be consistent with the parent Risk Spillover (e.g. Market Access related sub-scenarios have to belong to the Market Access Risk node)."
            "    - Generate 3 OR MORE sub-scenarios for each risk spillover."
            "    - Generate a short label for each subscenario."
            "4. **Iterate Based on the Analyst's Focus: '{analyst_focus}'**:"
            "    - After generating the initial tree structure, use the analyst's focus ('{analyst_focus}') to:"
            "        - Identify **missing branches** or underexplored areas of the tree."
            "        - Add new risk spillovers or sub-scenarios that align with the analyst's focus."
            "        - Ensure that sub-scenarios ALWAYS include ALL core components of the Risk Scenario and are formulated as natural sentences."
            "        - Ensure that sub-scenarios DO NOT overlap within and across risk spillovers."
            "        - Ensure that sub-scenarios belong to the correct Risk Spillover."
            "    - If the analyst focus is empty, skip this step."
            "    - If you don't understand the analyst focus ('{analyst_focus}'), ask an open-ended question to the analyst."
            "5. **Review and Expand the Tree for Missing Risks**:"
            "    - After incorporating the analyst's focus, review the tree structure to ensure it includes a **broad range of risks** and sub-scenarios."
            "    - Add any missing risks or sub-scenarios to the tree."
        ),
        "enforce_structure_string": (
            """IMPORTANT: Your response MUST be a valid JSON object. Each node in the JSON object must include:\n"
            "    - `node`: an integer representing the unique identifier for the node.\n"
            "    - `label`: a string for the name of the sub-theme.\n"
            "    - `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the main theme or risk.\n"
            "    - `children`: an array of child nodes.\n"
            "Format the JSON object as a nested dictionary. Be careful when specifying keys and items.\n"
            "Avoid overlapping labels. Break down joint concepts into unique parents so that each parent represents ONLY ONE concept. AVOID creating branch names such as 'Compliance and Regulatory Risk'. Keep risks separate and create a single branch for each risk, such as 'Compliance Risk' and 'Regulatory Risk', each with their own children.\n"
            "Return ONLY the JSON object, with no extra text, explanation, or markdown.\n"
            "You MUST use ONLY these field names: label, node, summary, children. Do NOT use underscores, spaces, or any other characters in field names. If you use any other field names, your answer will be rejected.\n"
            "## Example Structure:\n"
            "**Theme: Global Warming**\n\n"
            "{\n"
            "  \"node\": 1,\n"
            "  \"label\": \"Global Warming\",\n"
            "  \"summary\": \"Global Warming is a serious risk\",\n"
            "  \"children\": [\n"
            "    {\"node\": 2, \"label\": \"Renewable Energy Adoption\", \"summary\": \"Renewable energy reduces greenhouse gas emissions and thereby global warming and climate change effects\", \"children\": [\n"
            "      {\"node\": 5, \"label\": \"Solar Energy\", \"summary\": \"Solar energy reduces greenhouse gas emissions\"},\n"
            "      {\"node\": 6, \"label\": \"Wind Energy\", \"summary\": \"Wind energy reduces greenhouse gas emissions\"},\n"
            "      {\"node\": 7, \"label\": \"Hydropower\", \"summary\": \"Hydropower reduces greenhouse gas emissions\"}\n"
            "    ]},\n"
            "    {\"node\": 3, \"label\": \"Carbon Emission Reduction\", \"summary\": \"Carbon emission reduction decreases greenhouse gases\", \"children\": [\n"
            "      {\"node\": 8, \"label\": \"Carbon Capture Technology\", \"summary\": \"Carbon capture technology reduces atmospheric CO2\"},\n"
            "      {\"node\": 9, \"label\": \"Emission Trading Systems\", \"summary\": \"Emission trading systems incentivize reductions in greenhouse gases\"}\n"
            "    ]}\n"
            "  ]\n"
            "}\n"
            """
        ),
    },
}


def format_mindmap_to_dataframe(mindmap_text):
    """
    Parse a mind map in pipe-delimited table format into a cleaned pandas DataFrame.
    Strips whitespace and removes unnamed columns.

    Args:
        mindmap_text (str): The mind map content as a string in pipe-delimited format.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the cleaned data from the mind map.

    Raises:
        ValueError: If the resulting DataFrame does not contain the required columns.
    """
    try:
        df = pd.read_csv(
            StringIO(mindmap_text.strip()), sep="|", engine="python", skiprows=[1]
        )
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    except Exception:
        try:
            df = pd.read_csv(
                StringIO(mindmap_text.strip()),
                sep="|",
                engine="python",
                skiprows=[1],
                on_bad_lines="skip",
            )
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        except Exception as e2:
            raise ValueError(f"Failed to parse mindmap text to DataFrame: {e2}")
    required_columns = {"Main Branches", "Sub-Branches", "Description"}
    if not required_columns.issubset(set(df.columns)):
        raise ValueError(f"Missing required columns in mindmap table: {df.columns}")
    return df


def save_results_to_file(results, output_dir, filename):
    """
    Save the results to a JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, filename)

    with open(output_file, "w") as f:
        json.dump(results, f, default=str, indent=2)


def load_results_from_file(output_dir, filename):
    """
    Load the results from a JSON file.
    """
    input_file = os.path.join(output_dir, filename)
    with open(input_file, "r") as f:
        return json.load(f)

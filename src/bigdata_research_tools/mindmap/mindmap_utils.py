import json
import os
from io import StringIO

import pandas as pd

prompts_dict = {
    "theme": {
        "qualifier": "Main Theme",
        "user_prompt_message": "Your given Theme is: {main_theme}",
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

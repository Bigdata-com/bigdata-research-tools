def compose_themes_system_prompt_onestep(
    main_theme: str, analyst_focus: str = ""
) -> str:
    prompt = f"""
	Forget all previous prompts. 
	You are assisting a professional analyst tasked with creating a screener to measure the impact of the theme {main_theme} on companies. 
	Your objective is to generate a comprehensive tree structure of distinct sub-themes that will guide the analyst's research process.
	
	Follow these steps strictly:
	
	1. **Understand the Core Theme {main_theme}**:
	   - The theme {main_theme} is a central concept. All components are essential for a thorough understanding.
	
	2. **Create a Taxonomy of Sub-themes for {main_theme}**:
	   - Decompose the main theme {main_theme} into concise, focused, and self-contained sub-themes.
	   - Each sub-theme should represent a singular, concise, informative, and clear aspect of the main theme.
	   - Expand the sub-theme to be relevant for the {main_theme}: a single word is not informative enough.    
	   - Prioritize clarity and specificity in your sub-themes.
	   - Avoid repetition and strive for diverse angles of exploration.
	   - Provide a comprehensive list of potential sub-themes.
	  
	3. **Iterate Based on the Analyst's Focus {analyst_focus}**:
	   - If no specific {analyst_focus} is provided, transition directly to formatting the JSON response.
	
	4. **Format Your Response as a JSON Object**:
	   - Each node in the JSON object must include:
	     - `node`: an integer representing the unique identifier for the node.
	     - `label`: a string for the name of the sub-theme.
	     - `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the theme {main_theme}.
	       - For the node referring to the first node {main_theme}, just define briefly in maximum 15 words the theme {main_theme}.
	     - `children`: an array of child nodes.
	
	## Example Structure:
	**Theme: Global Warming**
	
	{{
	    "node": 1,
	    "label": "Global Warming",
	    "children": [
	        {{
	            "node": 2,
	            "label": "Renewable Energy Adoption",
	            "summary": "Renewable energy reduces greenhouse gas emissions and thereby global warming and climate change effects",
	            "children": [
	                {{"node": 5, "label": "Solar Energy", "summary": "Solar energy reduces greenhouse gas emissions"}},
	                {{"node": 6, "label": "Wind Energy", "summary": "Wind energy reduces greenhouse gas emissions"}},
	                {{"node": 7, "label": "Hydropower", "summary": "Hydropower reduces greenhouse gas emissions"}}
	            ]
	        }},
	        {{
	            "node": 3,
	            "label": "Carbon Emission Reduction",
	            "summary": "Carbon emission reduction decreases greenhouse gases",
	            "children": [
	                {{"node": 8, "label": "Carbon Capture Technology", "summary": "Carbon capture technology reduces atmospheric CO2"}},
	                {{"node": 9, "label": "Emission Trading Systems", "summary": "Emission trading systems incentivize reductions in greenhouse gases"}}
	            ]
	        }},
	        {{
	            "node": 4,
	            "label": "Climate Resilience and Adaptation",
	            "summary": "Climate resilience adapts to global warming impacts, reducing vulnerability",
	            "children": [
	                {{"node": 10, "label": "Sustainable Agriculture", "summary": "Sustainable agriculture reduces emissions, enhancing food security amid climate change"}},
	                {{"node": 11, "label": "Infrastructure Upgrades", "summary": "Infrastructure upgrades enhance resilience and reduce emissions against climate change"}}
	            ]
	        }},
	        {{
	            "node": 12,
	            "label": "Biodiversity Conservation",
	            "summary": "Biodiversity conservation supports ecosystems",
	            "children": [
	                {{"node": 13, "label": "Protected Areas", "summary": "Protected areas preserve ecosystems, aiding climate resilience and mitigation"}},
	                {{"node": 14, "label": "Restoration Projects", "summary": "Restoration projects sequester carbon"}}
	            ]
	        }},
	        {{
	            "node": 15,
	            "label": "Climate Policy and Governance",
	            "summary": "Climate policy governs emissions, guiding efforts to combat global warming",
	            "children": [
	                {{"node": 16, "label": "International Agreements", "summary": "International agreements coordinate global efforts to reduce greenhouse gas emissions"}},
	                {{"node": 17, "label": "National Legislation", "summary": "National legislation enforces policies that reduce greenhouse gas emissions"}}
	            ]
	        }}
	    ]
	}}
    """
    return prompt.strip()


def compose_themes_system_prompt_base(main_theme: str) -> str:
    prompt = f"""
        You are assisting a professional analyst tasked with creating a screener to measure the impact of the theme {main_theme} on companies. 
        Your objective is to generate a concise yet comprehensive tree structure of distinct sub-themes that will guide the analyst's research process.
        
        Follow these steps strictly:
        
        1. **Understand the Core Theme {main_theme}**:
           - The theme {main_theme} is a central concept. All components are essential for a thorough understanding.
        
        2. **Create a Focused Taxonomy of Sub-themes for {main_theme}**:
           - Decompose the main theme {main_theme} into concise, focused, and self-contained sub-themes.
           - Each sub-theme should represent a distinct, fundamental aspect of the main theme.
           - Ensure sub-themes are conceptually independent from each other and collectively comprehensive.
           - Use clear, specific labels that communicate the essence of each concept.
           - Avoid single-word labels; instead, use descriptive phrases that capture the full meaning.
           - Aim for a total of 4-6 main sub-themes under the root theme.
        
        3. **Format Your Response as a JSON Object**:
           - Each node in the JSON object must include:
             - `node`: an integer representing the unique identifier for the node.
             - `label`: a string for the name of the sub-theme.
             - `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the theme {main_theme}.
               - For the node referring to the first node {main_theme}, just define briefly in maximum 15 words the theme {main_theme}.
             - `children`: an array of child nodes (limit to 2-3 children per parent node).
           - The entire tree structure should contain no more than 10-15 nodes total.

        ### Example Structure (Main Theme Only):
        **Theme: Consumer Spending**
        {{
            "node": 1,
            "label": "Consumer Spending",
            "children": [
                {{
                    "node": 2,
                    "label": "Retail Expenditure",
                    "summary": "Retail spending plays a significant role in overall consumer expenditures.",
                    "children": [
                        {{"node": 5, "label": "E-commerce", "summary": "Online shopping is a key part of consumer spending, affecting traditional retail."}},
                        {{"node": 6, "label": "In-Store Purchases", "summary": "In-store purchases continue to represent a substantial portion of consumer spending."}}
                    ]
                }},
                {{
                    "node": 3,
                    "label": "Housing and Real Estate",
                    "summary": "A significant portion of consumer spending is directed toward housing and real estate markets.",
                    "children": [
                        {{"node": 7, "label": "Home Purchases", "summary": "Home purchases are an essential part of long-term consumer spending."}},
                        {{"node": 8, "label": "Renting", "summary": "Renting is an important category of consumer spending in the housing sector."}}
                    ]
                }},
                {{
                    "node": 4,
                    "label": "Travel and Leisure",
                    "summary": "Consumer spending in travel and leisure reflects discretionary spending behaviors.",
                    "children": [
                        {{"node": 9, "label": "Domestic Travel", "summary": "Domestic travel represents a key category in overall travel spending."}},
                        {{"node": 10, "label": "International Travel", "summary": "International travel contributes significantly to global consumer spending in the leisure sector."}}
                    ]
                }}
            ]
        }}
    """
    return prompt.strip()


def compose_themes_system_prompt_focus(main_theme: str, analyst_focus: str) -> str:
    prompt = f"""
        You are assisting a professional analyst in refining a previously created taxonomy `initial_tree_str` for the theme {main_theme}. The analyst now wants to focus on a specific aspect {analyst_focus} to enhance the taxonomy.
    
        Follow these steps strictly:
        
        1. **Understand the Core Theme {main_theme} and the Provided Tree Structure**:
           - Review the JSON tree structure provided by the analyst.
           - Identify how the {analyst_focus} relates to the existing taxonomy.
        
        2. **Integrate the Analyst's Focus {analyst_focus} Naturally**:
           - Instead of adding the term {analyst_focus} directly to node labels, focus on the ways that the core theme {main_theme} is impacted by or intersects with the {analyst_focus}.
           - The labels should still be focused on {main_theme}, but the added complexity from {analyst_focus} should subtly guide the refinement.
           - Ensure the breakdown of the tree provides valuable and actionable insights to the analyst, demonstrating the nuanced impact of the {analyst_focus}.
        
        3. **Format Your Response as a JSON Object**:
           - Transform the structure to reflect the integrated perspective:
             - `node`: an integer representing the unique identifier for the node.
             - `label`: a string for the name of the sub-theme (naturally incorporating the focus area).
             - `summary`: a string to explain briefly in maximum 15 words how this aspect relates to the main theme.
             - `children`: an array of child nodes (limit to 2-3 children per parent).
        
        ### Example Structure (Main Theme with Analyst Focus):
        **Theme: Consumer Spending**  
        **Analyst Focus: Remote Work Technologies**
        {{
            "node": 1,
            "label": "Consumer Spending",
            "children": [
                {{
                    "node": 2,
                    "label": "E-commerce Trends",
                    "summary": "E-commerce plays a significant role in consumer spending, with transactions occurring increasingly online.",
                    "children": [
                        {{"node": 5, "label": "Subscription Services", "summary": "Consumers allocate spending to subscription models for digital services and goods."}},
                        {{"node": 6, "label": "Digital Payment Solutions", "summary": "Digital payments are an integral part of consumer spending in online transactions."}}
                    ]
                }},
                {{
                    "node": 3,
                    "label": "Housing Demand Shifts",
                    "summary": "Consumer spending in housing reflects preferences for various housing types and real estate markets.",
                    "children": [
                        {{"node": 7, "label": "Suburban Housing Preferences", "summary": "Spending in suburban housing reflects consumer choices influenced by various factors."}},
                        {{"node": 8, "label": "Home Office Equipment Spending", "summary": "Consumers allocate spending to home office equipment, reflecting the importance of remote work setups."}}
                    ]
                }},
                {{
                    "node": 4,
                    "label": "Technology Adoption for Consumer Goods",
                    "summary": "Technological innovations in consumer goods contribute to shaping how consumers spend their money on products and services.",
                    "children": [
                        {{"node": 9, "label": "Smart Home Devices", "summary": "Consumers spend on smart home devices to enhance their living environments."}},
                        {{"node": 10, "label": "Virtual Products and Experiences", "summary": "Virtual products and experiences represent significant categories of consumer spending."}}
                    ]
                }},
                {{
                    "node": 5,
                    "label": "Service-Based Consumption",
                    "summary": "Spending on services is a key component of consumer expenditures, influenced by evolving consumer preferences.",
                    "children": [
                        {{"node": 11, "label": "Online Education and Training", "summary": "Consumers allocate spending to online education and training services for personal and professional development."}},
                        {{"node": 12, "label": "Entertainment Subscriptions", "summary": "Entertainment subscription services are a growing part of consumer spending in the entertainment sector."}}
                    ]
                }}
            ]
        }}
    """
    return prompt.strip()

from enum import Enum
from typing import Dict


class SourceType(Enum):
    """
    Enumeration representing different types of data sources that can be analyzed.

    Attributes:
        PATENTS (str): Represents patent-related data.
        JOBS (str): Represents job postings data.
        CORPORATE_DOCS (str): Represents corporate documents such as reports or filings.
    """

    PATENTS = "PATENTS"
    JOBS = "JOBS"
    CORPORATE_DOCS = "CORPORATE_DOCS"


theme_generation_default_prompts: Dict[SourceType, str] = {
    SourceType.CORPORATE_DOCS: """
Forget all previous prompts. 
You are assisting a professional analyst tasked with creating a screener to measure the impact of the theme `main_theme` on companies. 
Your objective is to generate a comprehensive tree structure of distinct sub-themes that will guide the analyst's research process.

Follow these steps strictly:

1. **Understand the Core Theme `main_theme`**:
   - The theme `main_theme` is a central concept. All components are essential for a thorough understanding.

2. **Create a Taxonomy of Sub-themes for `main_theme`**:
   - Decompose the main theme `main_theme` into concise, focused, and self-contained sub-themes.
   - Each sub-theme should represent a singular, concise, informative, and clear aspect of the main theme.
   - Expand the sub-theme to be relevant for the `main_theme`: a single word is not informative enough.    
   - Prioritize clarity and specificity in your sub-themes.
   - Avoid repetition and strive for diverse angles of exploration.
   - Provide a comprehensive list of potential sub-themes.

3. **Iterate Based on the Analyst's Focus `analyst_focus`**:
   - Continuously refine the tree structure, delving deeper into the analyst's focus `analyst_focus`.
   - If relevant information isn't available under the given focus, explore other aspects of the tree structure.
   - If `analyst_focus` is empty, transition directly to step 4.
   - If you don't understand the `analyst_focus`, ask an open-ended question to the analyst. 

4. **Format Your Response as a JSON Object**:
   - Each node in the JSON object must include:
     - `node`: an integer representing the unique identifier for the node.
     - `label`: a string for the name of the sub-theme.
     - `summary`: a string to explain briefly in maximum 15 words why the sub-theme is related to the theme `main_theme`.
       - For the node referring to the first node `main_theme`, just define briefly in maximum 15 words the theme `main_theme`.
     - `children`: an array of child nodes.

### Example Structure:
**Theme: Global Warming**

{
    "node": 1,
    "label": "Global Warming",
    "children": [
        {
            "node": 2,
            "label": "Renewable Energy Adoption",
            "summary": "Renewable energy reduces greenhouse gas emissions and thereby global warming and climate change effects",
            "children": [
                {"node": 5, "label": "Solar Energy", "summary": "Solar energy reduces greenhouse gas emissions"},
                {"node": 6, "label": "Wind Energy", "summary": "Wind energy reduces greenhouse gas emissions"},
                {"node": 7, "label": "Hydropower", "summary": "Hydropower reduces greenhouse gas emissions"}
            ]
        },
        {
            "node": 3,
            "label": "Carbon Emission Reduction",
            "summary": "Carbon emission reduction decreases greenhouse gases",
            "children": [
                {"node": 8, "label": "Carbon Capture Technology", "summary": "Carbon capture technology reduces atmospheric CO2"},
                {"node": 9, "label": "Emission Trading Systems", "summary": "Emission trading systems incentivize reductions in greenhouse gases"}
            ]
        },
        {
            "node": 4,
            "label": "Climate Resilience and Adaptation",
            "summary": "Climate resilience adapts to global warming impacts, reducing vulnerability",
            "children": [
                {"node": 10, "label": "Sustainable Agriculture", "summary": "Sustainable agriculture reduces emissions, enhancing food security amid climate change"},
                {"node": 11, "label": "Infrastructure Upgrades", "summary": "Infrastructure upgrades enhance resilience and reduce emissions against climate change"}
            ]
        },
        {
            "node": 12,
            "label": "Biodiversity Conservation",
            "summary": "Biodiversity conservation supports ecosystems",
            "children": [
                {"node": 13, "label": "Protected Areas", "summary": "Protected areas preserve ecosystems, aiding climate resilience and mitigation"},
                {"node": 14, "label": "Restoration Projects", "summary": "Restoration projects sequester carbon"}
            ]
        },
        {
            "node": 15,
            "label": "Climate Policy and Governance",
            "summary": "Climate policy governs emissions, guiding efforts to combat global warming",
            "children": [
                {"node": 16, "label": "International Agreements", "summary": "International agreements coordinate global efforts to reduce greenhouse gas emissions"},
                {"node": 17, "label": "National Legislation", "summary": "National legislation enforces policies that reduce greenhouse gas emissions"}
            ]
        }
    ]
}
""",
    SourceType.PATENTS: """
Forget all previous prompts. 
You are assisting in creating a comprehensive categorization of patent filing types within the theme `main_theme`. 
Your objective is to generate a detailed tree structure of patent categories and their sub-categories that could exist within this field.

Follow these steps strictly:

1. **Understand the Core Theme `main_theme`**:
- The theme `main_theme` represents any topic or field. All patent filing types related to this theme are essential for a thorough understanding.

2. **Create a Taxonomy of Patent Types for `main_theme`**:
- Break down the main theme into distinct categories of patent filings that relate to this theme.
- Each category should represent a specific type of patent or protected intellectual property.
- Expand each category to include specific patent areas: avoid single-word descriptions.    
- Prioritize clarity and specificity in your patent categories.
- Avoid repetition and ensure comprehensive coverage of different aspects.
- Consider both direct applications and supporting/auxiliary patent filings.
- Include both new inventions and improvements to existing ones where applicable.

3. **Format Your Response as a JSON Object**:
- Each node in the JSON object must include:
    - `node`: an integer representing the unique identifier for the node.
    - `label`: a string for the name of the patent category.
    - `summary`: a string explaining briefly in maximum 15 words how this patent filing type relates to the theme `main_theme`.
    - For the node referring to the first node `main_theme`, just define briefly in maximum 15 words the theme.
    - `children`: an array of child nodes.

### Example Structure:
**Theme: Coffee**

{
    "node": 1,
    "label": "Coffee",
    "summary": "Beverage made from roasted coffee beans, including its production and consumption methods",
    "children": [
        {
            "node": 2,
            "label": "Brewing Method Patents",
            "summary": "Patents covering different ways to extract coffee from beans",
            "children": [
                {"node": 5, "label": "Pressure-Based Extraction Systems", "summary": "Methods using pressure to brew coffee, like espresso machines"},
                {"node": 6, "label": "Cold Brew Apparatus", "summary": "Systems for extracting coffee flavor at low temperatures"},
                {"node": 7, "label": "Filter Design Patents", "summary": "Innovations in coffee filtering and straining methods"}
            ]
        },
        {
            "node": 3,
            "label": "Bean Processing Patents",
            "summary": "Patents related to treating and preparing coffee beans",
            "children": [
                {"node": 8, "label": "Roasting Equipment Designs", "summary": "Systems for roasting raw coffee beans to desired levels"},
                {"node": 9, "label": "Grinding Mechanism Patents", "summary": "Methods for reducing coffee beans to specific particle sizes"}
            ]
        },
        {
            "node": 4,
            "label": "Storage Solution Patents",
            "summary": "Patents for preserving coffee freshness and flavor",
            "children": [
                {"node": 10, "label": "Degassing Valve Systems", "summary": "Methods for releasing gases while maintaining freshness"},
                {"node": 11, "label": "Moisture Control Patents", "summary": "Systems for maintaining optimal humidity levels in coffee storage"}
            ]
        }
    ]
}
""",
    SourceType.JOBS: """
Forget all previous prompts. 
You are assisting a financial analyst evaluating a company's exposure to `main_theme` by examining their job postings.
Your objective is to generate a comprehensive tree structure of distinct qualifications found in job postings that pertain to the theme `main_theme`. 

Follow these steps strictly:

1. **Understand the Core Theme `main_theme`**:
   - The theme `main_theme` is a central concept. All components are essential for a thorough understanding.

2. **Create a Domain-Unique Skills Taxonomy using Depth-First, then Breadth**:
   - First, achieve sufficient depth in categorization:
     - Start with ONE highly representative qualifications category  for `main_theme`
     - Drill down through sub-categories until reaching truly specific qualifications
     - Continue drilling down until skills cannot be made more specific
     - Use these leaf nodes (nodes with no children) as a "specificity benchmark"
   - Then, expand breadth across the domain:
     - Once proper depth is established, identify parallel categories
     - Each new category must achieve the same depth of specificity
     - Ensure comprehensive coverage of the parent node
     - Add categories until the parent node is well-represented

3. **Rules for Leaf nodes**:
    - Leaf nodes MUST pass this test: "Would this qualification be found in the Skills and Qualifications section of a job posting within the theme `main_theme`?"
    - Leaf nodes MUST NOT be in any of the following
         - General professional qualifications
         - Common business knowledge
         - Universal technical qualifications
         - Cross-industry standards or practices
         - Generic process frameworks
         - Industry-agnostic regulations
         - Basic management capabilities
         - General compliance requirements
    - If a leaf node doesn't pass the above requirements, amend it until it does

4. **Format Your Response as a JSON Object**:
   - Each node in the JSON object must include:
     - `node`: an integer representing the unique identifier for the node
     - `label`: a string for the specific skill
     - `summary`: a string explaining in maximum 15 words why this skill is unique to the domain
       - For the first node `main_theme`, provide a 15-word definition
     - `children`: an array of child nodes (sub-categories of qualifications)

### Example Structure:
{
    "node": 1,
    "label": "Electric Vehicles",
    "summary": "Development and manufacturing of battery-powered vehicles and supporting infrastructure",
    "children": [
        {
            "node": 2,
            "label": "Battery System Expertise",
            "summary": "Specialized knowledge of EV-specific battery technologies and implementations",
            "children": [
                {
                    "node": 5,
                    "label": "Pack Architecture Design",
                    "summary": "Creating EV-specific battery configurations for optimal vehicle integration",
                    "children": [
                        {
                            "node": 11,
                            "label": "18650 to Prismatic Cell Migration",
                            "summary": "Converting EV battery packs from cylindrical to prismatic cell architectures"
                        },
                        {
                            "node": 12,
                            "label": "Pouch Cell Thermal Runaway Prevention",
                            "summary": "Implementing safeguards specific to pouch cells in EV battery packs"
                        },
                        {
                            "node": 13,
                            "label": "Battery Module Bus Bar Design",
                            "summary": "Designing current distribution systems for high-voltage EV battery modules"
                        },
                        {
                            "node": 14,
                            "label": "Cell Tab Ultrasonic Welding",
                            "summary": "Specialized welding of battery cell tabs in EV pack manufacturing"
                        }
                    ]
                },
                {
                    "node": 6,
                    "label": "Charging Infrastructure Planning",
                    "summary": "Developing charging solutions specific to electric vehicle fleets",
                    "children": [
                        {
                            "node": 15,
                            "label": "CCS to CHAdeMO Protocol Translation",
                            "summary": "Implementing cross-standard charging compatibility for mixed EV fleets"
                        },
                        {
                            "node": 16,
                            "label": "V2G Frequency Regulation Programming",
                            "summary": "Programming vehicle-to-grid services for power grid stabilization"
                        },
                        {
                            "node": 17,
                            "label": "SAE J1772 Signal Monitoring",
                            "summary": "Implementing safety protocols for EV charging control pilot signals"
                        },
                        {
                            "node": 18,
                            "label": "ISO 15118 Plug-and-Charge Integration",
                            "summary": "Implementing secure authentication protocols for automatic EV charging authorization"
                        }
                    ]
                },
                {
                    "node": 7,
                    "label": "BMS Development",
                    "summary": "Creating battery management systems for electric vehicle applications",
                    "children": [
                        {
                            "node": 19,
                            "label": "Cell Balancing Algorithm Development",
                            "summary": "Programming active cell balancing for large-format EV battery packs"
                        },
                        {
                            "node": 20,
                            "label": "SOH Estimation Using EIS",
                            "summary": "Implementing electrochemical impedance spectroscopy for battery health monitoring"
                        },
                        {
                            "node": 21,
                            "label": "Passive Balancing Circuit Design",
                            "summary": "Designing resistive balancing networks for EV battery management"
                        },
                        {
                            "node": 22,
                            "label": "CAN Bus BMS Integration",
                            "summary": "Implementing battery data communication protocols for vehicle systems"
                        }
                    ]
                }
            ]
        },
        {
            "node": 3,
            "label": "Powertrain Systems",
            "summary": "Development of electric vehicle propulsion and power delivery systems",
            "children": [
                {
                    "node": 8,
                    "label": "Motor Control Systems",
                    "summary": "Developing control systems for electric vehicle motors",
                    "children": [
                        {
                            "node": 23,
                            "label": "PMSM Field-Oriented Control",
                            "summary": "Implementing torque control for permanent magnet synchronous motors"
                        },
                        {
                            "node": 24,
                            "label": "SiC MOSFET Inverter Design",
                            "summary": "Designing silicon carbide inverters for high-efficiency motor control"
                        },
                        {
                            "node": 25,
                            "label": "Motor Hall Sensor Calibration",
                            "summary": "Calibrating position sensors for electric motor commutation timing"
                        },
                        {
                            "node": 26,
                            "label": "Regenerative Torque Mapping",
                            "summary": "Programming variable regenerative braking based on vehicle dynamics"
                        }
                    ]
                },
                {
                    "node": 9,
                    "label": "Power Electronics",
                    "summary": "Designing and implementing electric vehicle power conversion systems",
                    "children": [
                        {
                            "node": 27,
                            "label": "DC-DC Converter Thermal Design",
                            "summary": "Designing cooling systems for high-power EV voltage converters"
                        },
                        {
                            "node": 28,
                            "label": "GaN Power Stage Layout",
                            "summary": "Designing gallium nitride power stages for EV power conversion"
                        },
                        {
                            "node": 29,
                            "label": "EMI Filter Design",
                            "summary": "Creating filters for electromagnetic interference in EV power systems"
                        },
                        {
                            "node": 30,
                            "label": "Bidirectional Charger Control",
                            "summary": "Programming dual-direction power flow for V2G applications"
                        }
                    ]
                },
                {
                    "node": 10,
                    "label": "Transmission Integration",
                    "summary": "Developing specialized transmission systems for electric powertrains",
                    "children": [
                        {
                            "node": 31,
                            "label": "Single-Speed Reduction Design",
                            "summary": "Designing compact reduction gearboxes for electric motors"
                        },
                        {
                            "node": 32,
                            "label": "Multi-Motor Torque Distribution",
                            "summary": "Programming torque vectoring for multi-motor electric vehicles"
                        },
                        {
                            "node": 33,
                            "label": "E-Axle Integration",
                            "summary": "Integrating motor, gearing, and power electronics into single units"
                        },
                        {
                            "node": 34,
                            "label": "Transmission Lubrication Optimization",
                            "summary": "Designing lubrication systems for high-RPM electric motor gearing"
                        }
                    ]
                }
            ]
        }
    ]
}
""",
}

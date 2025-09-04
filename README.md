# Bigdata Research Tools - User Guide

**Building with Bigdata.com**

[![Python version support](https://img.shields.io/badge/Python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.13-blue?logo=python)](https://pypi.org/project/bigdata-research-tools)
[![PyPI version](https://badge.fury.io/py/bigdata-research-tools.svg)](https://badge.fury.io/py/bigdata-research-tools)


## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Installation](#installation)
4. [Authentication Setup](#authentication-setup)
5. [Core Workflows](#core-workflows)
6. [Narrative Miner](#narrative-miner)
7. [Thematic Screener](#thematic-screener)
8. [Company Objects](#company-objects)
9. [Risk Analyzer](#risk-analyzer)
10. [Query Builder](#query-builder)
11. [Search Manager](#search-manager)
12. [LLM Integration](#llm-integration)
13. [Advanced Features](#advanced-features)
14. [Parameter Deep Dive](#parameter-deep-dive)
    - [Fiscal Year Guide](#fiscal-year-guide)
    - [Focus Parameter Guide](#focus-parameter-guide)
15. [Interactive Tutorial](#interactive-tutorial)
    - [Quick Start with uv](#quick-start-with-uv)
    - [Tutorial Overview](#tutorial-overview)
    - [Alternative Installation Methods](#alternative-installation-methods)
16. [Examples](#examples)
17. [Support and Resources](#support-and-resources)
18. [License](#license)

---

## Overview

**Bigdata Research Tools** is a Python library designed to automate and streamline research workflows using the Bigdata.com API. It provides high-level, plug-and-play functions for building customized research processes with minimal effort.

## Key Features

- **⚡ Concurrent Search**: Execute multiple searches efficiently with built-in rate limiting.
- **🛡️ Thread-Safe Operations**: Safe concurrent access for all workflows.
- **🧭 Guided Workflow Builder**: Easily build guided research workflows—see ready-to-use examples in the [Bigdata Cookbook](https://github.com/Bigdata-com/bigdata-cookbook).
- **🎨 Interactive Visualizations**: Create dashboards and charts for your results.


### Library Architecture

```
bigdata_research_tools/
├── workflows/          # High-level research workflows
├── search/            # Search utilities and query builders
├── visuals/           # Visualization and dashboard tools
├── labeler/           # AI-powered content labeling
├── llm/               # LLM integration (OpenAI, Bedrock)
└── prompts/           # Prompt templates for AI models
```

---

## Installation

Install the library using pip:

```bash
pip install bigdata-research-tools
```

### Optional Dependencies

Install additional packages for specific features:

```bash
# For Excel export functionality
pip install bigdata-research-tools[excel]

# For visualization features
pip install bigdata-research-tools[plotly]

# For OpenAI integration
pip install bigdata-research-tools[openai]

# For all optional features
pip install bigdata-research-tools[excel,plotly,openai]
```

---

## Authentication Setup

### Environment Variables

Set up your credentials using environment variables:

```bash
export BIGDATA_USERNAME="your_username"
export BIGDATA_PASSWORD="your_password"
export OPENAI_API_KEY= "your_openai_api_key"
```

### Using .env File

Create a `.env` file in your project directory:

```bash
BIGDATA_USERNAME="your_username"
BIGDATA_PASSWORD="your_password"
OPENAI_API_KEY="your_openai_api_key"
```

Load the environment variables in your Python script:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Core Workflows

### Jupyter Notebook Setup

If you're running these workflows in a Notebook, you'll need to set up asyncio properly to avoid event loop conflicts:

```python
import asyncio
asyncio.get_running_loop()
import nest_asyncio; nest_asyncio.apply()
```

## Narrative Miner

The Narrative Miner tracks how specific narratives evolve over time across different document types.

### Basic Usage

```python
from bigdata_research_tools.workflows import NarrativeMiner
from bigdata_client.models.search import DocumentType

narrative_miner = NarrativeMiner(
    narrative_sentences=[
        "Artificial Intelligence Development",
        "Machine Learning Innovation",
        "Data Privacy Concerns"
    ],
    llm_model="openai::gpt-4o-mini",
    start_date="2024-01-01",
    end_date="2024-12-31",
    fiscal_year=2024,

    document_type=DocumentType.NEWS
)

results = narrative_miner.mine_narratives(
    export_path="narrative_analysis.xlsx"
)
```

### Parameters

#### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `narrative_sentences` | `List[str]` | ✅ | List of narrative sentences to track |
| `start_date` | `str` | ✅ | Start date in YYYY-MM-DD format |
| `end_date` | `str` | ✅ | End date in YYYY-MM-DD format |
| `llm_model` | `str` | ✅ | LLM model in format "provider::model" |
| `document_type` | `DocumentType` | ✅ | Type of documents to search |
| `fiscal_year` | `int` | ❌ | Fiscal year for transcripts/filings. Set to `None` for news |
| `sources` | `List[str]` | ❌ | Filter by specific news sources |
| `rerank_threshold` | `float` | ❌ | Cross-encoder threshold (0-1) |

#### Method Parameters - `mine_narratives()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_limit` | `int` | `10` | Max documents per query |
| `batch_size` | `int` | `10` | Entities per batch |
| `freq` | `str` | `"3M"` | Analysis frequency (Y/M/W/D) |
| `export_path` | `str` | `None` | Excel export path |

### Document Types

```python
from bigdata_client.models.search import DocumentType

# Available document types
DocumentType.NEWS          # News articles
DocumentType.TRANSCRIPTS   # Earnings call transcripts
DocumentType.FILINGS       # SEC filings
DocumentType.ALL           # All document types. fiscal_year must not be None
```

### Return Values

```python
results = {
    "df_labeled": DataFrame  # Labeled search results with narrative classifications
}
```

---

## Thematic Screener

Analyzes company exposure to specific themes by generating sub-themes and scoring companies.

### Basic Usage

```python
from bigdata_research_tools.workflows import ThematicScreener
from bigdata_research_tools.client import bigdata_connection
from bigdata_client.models.search import DocumentType


# Get companies from a watchlist
bigdata = bigdata_connection()
watchlist = bigdata.watchlists.get("watchlist_id")
companies = bigdata.knowledge_graph.get_entities(watchlist.items)

screener = ThematicScreener(
    llm_model="openai::gpt-4o-mini",
    main_theme="Electric Vehicles",
    companies=companies,
    start_date="2024-01-01",
    end_date="2024-12-31",
    document_type=DocumentType.TRANSCRIPTS,
    fiscal_year=2024
)

results = screener.screen_companies(
    export_path="thematic_screening.xlsx"
)
```

### Parameters

#### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `llm_model` | `str` | ✅ | LLM model identifier |
| `main_theme` | `str` | ✅ | Main theme to analyze |
| `companies` | `List[Company]` | ✅ | List of companies to screen (see [Company Objects](#company-objects)) |
| `start_date` | `str` | ✅ | Start date (YYYY-MM-DD) |
| `end_date` | `str` | ✅ | End date (YYYY-MM-DD) |
| `document_type` | `DocumentType` | ✅ | Document scope |
| `fiscal_year` | `int` | ❌ | Required for transcripts/filings. Set to `None` for news (see [Fiscal Year Guide](#fiscal-year-guide))  |
| `sources` | `List[str]` | ❌ | Source filters |
| `rerank_threshold` | `float` | ❌ | Reranking threshold |
| `focus` | `str` | ❌ | Additional focus description (see [Focus Parameter Guide](#focus-parameter-guide)) |

#### Method Parameters - `screen_companies()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_limit` | `int` | `10` | Documents per query |
| `batch_size` | `int` | `10` | Batch size for processing |
| `frequency` | `str` | `"3M"` | Date range frequency |
| `word_range` | `Tuple[int, int]` | `(50, 100)` | Word range for motivations |
| `export_path` | `str` | `None` | Excel export path |

### Return Values

```python
results = {
    "df_labeled": DataFrame,     # Labeled search results
    "df_company": DataFrame,     # Company-level theme scores
    "df_industry": DataFrame,    # Industry-level aggregations
    "df_motivation": DataFrame,  # Company motivations
    "theme_tree": ThemeTree     # Generated theme hierarchy
}
```
---
## Company Objects

Company objects are `bigdata_client.models.entities.Company` instances that represent companies in the Bigdata knowledge graph. Here's how to obtain them:

#### Method 1: From Watchlists (Recommended)

```python
from bigdata_research_tools.client import bigdata_connection

# Connect to Bigdata API
bigdata = bigdata_connection()

# Get companies from a specific watchlist
watchlist_id = "a3915138-bba9-437e-a813-aa1620a822cc"  # Example GRID watchlist
watchlist = bigdata.watchlists.get(watchlist_id)
companies = bigdata.knowledge_graph.get_entities(watchlist.items)

print(f"Found {len(companies)} companies in watchlist")
# Output: Found 7 companies in watchlist
```

#### Method 2: Search by Company Names

```python
# Search for specific companies by name
company_names = ["Apple Inc", "Microsoft Corporation", "Tesla Inc"]
companies = []

for name in company_names:
    # Find company in knowledge graph
    search_results = bigdata.knowledge_graph.find_companies(name)
    if search_results:
        companies.append(next(iter(search_results)))
        print(f"Found: {companies[-1].name} (ID: {companies[-1].id})")

# Output:
# Found: Apple Inc (ID: D8442C)
# Found: Microsoft Corporation (ID: D4A6CC) 
# Found: Tesla Inc (ID: 054E32)
```

#### Method 3: Filter by Criteria

```python
# Get all companies from a watchlist, then filter
all_companies = bigdata.knowledge_graph.get_entities(watchlist.items)

# Filter by sector or other criteria
tech_companies = [
    company for company in all_companies 
    if hasattr(company, 'sector') and 'Technology' in company.sector
]

```

#### Company Object Properties

Each `Company` object has these key properties:

```python
company = companies[0]
print(f"Name: {company.name}")           # Apple Inc
print(f"ID: {company.id}")               # D8442C
print(f"Ticker: {company.ticker}")       # AAPL
print(f"Type: {type(company)}")          # <class 'bigdata_client.models.entities.Company'>

# Additional properties may include:
# company.sector, company.industry, company.country, etc.
```

---

## Risk Analyzer

Assesses company exposure to risk scenarios with detailed risk taxonomy generation.

### Basic Usage

```python
from bigdata_research_tools.workflows.risk_analyzer import RiskAnalyzer
from bigdata_client.models.search import DocumentType


analyzer = RiskAnalyzer(
    llm_model="openai::gpt-4o-mini",
    main_theme="Supply Chain Disruption",
    companies=companies,
    start_date="2024-01-01",
    end_date="2024-12-31",
    document_type=DocumentType.NEWS,
    keywords=["supply chain", "logistics"],
    control_entities={"place": ["China", "Taiwan"]}
)

results = analyzer.screen_companies(
    export_path="risk_analysis.xlsx"
)
```

### Parameters

#### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `llm_model` | `str` | ✅ | LLM model identifier |
| `main_theme` | `str` | ✅ | Main risk theme |
| `companies` | `List[Company]` | ✅ | Companies to analyze (see [Company Objects](#company-objects)) |
| `start_date` | `str` | ✅ | Analysis start date |
| `end_date` | `str` | ✅ | Analysis end date |
| `document_type` | `DocumentType` | ✅ | Document scope |
| `keywords` | `List[str]` | ❌ | Keyword filters |
| `control_entities` | `Dict[str, List[str]]` | ❌ | Entity co-mention filters (see [Control Entities](#control-entities)) |
| `fiscal_year` | `int` | ❌ |  Required for transcripts/filings. Set to `None` for news (see [Fiscal Year Guide](#fiscal-year-guide))  |
| `sources` | `List[str]` | ❌ | Source filters |
| `rerank_threshold` | `float` | ❌ | Reranking threshold |
| `focus` | `str` | ❌ | Additional focus description (see [Focus Parameter Guide](#focus-parameter-guide)) |

#### Method Parameters - `screen_companies()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_limit` | `int` | `10` | Documents per query |
| `batch_size` | `int` | `10` | Batch size for processing |
| `frequency` | `str` | `"3M"` | Date range frequency |
| `word_range` | `Tuple[int, int]` | `(50, 100)` | Word range for motivations |
| `export_path` | `str` | `None` | Excel export path |

### Return Values

```python
results = {
    "df_labeled": DataFrame,     # Labeled search results
    "df_company": DataFrame,     # Company risk scores
    "df_industry": DataFrame,    # Industry risk aggregations
    "df_motivation": DataFrame,  # Risk motivations
    "risk_tree": ThemeTree      # Risk taxonomy tree
}
```

### Control Entities

Control entities allow you to filter results based on **co-mentions** - documents must mention both your target companies AND the control entities to be included in results.

#### How Control Entities Work

```python
# Example: Find documents about Tesla that also mention China or Taiwan
tesla_company_search = bigdata.knowledge_graph.autosuggest("Tesla Inc.")
tesla_company = tesla_company_search[0]

analyzer = RiskAnalyzer(
    llm_model="openai::gpt-4o-mini",
    main_theme="Supply Chain Risk",
    companies=[tesla_company],
    start_date="2024-01-01",
    end_date="2024-12-31",
    document_type=DocumentType.NEWS,
    control_entities={
        "place": ["China", "Taiwan"],  # Must also mention these places
        "people": ["Elon Musk", "Tim Cook"],
        "product": ["iPhone", "Model S", "Azure"]
    }
)
```

#### Control Entity Types

```python
control_entities = {
    # Geographic filters
    "place": ["United States", "China", "Taiwan", "Germany"],
    
    # People filters  
    "people": ["Elon Musk", "Tim Cook", "Satya Nadella"],
    
    # Topic/concept filters
    "topic": ["regulation", "trade policy", "cybersecurity"],
    
    # Product filters  
    "product": ["iPhone", "Model S", "Azure"]
}
```

#### Important Notes

- **AND Logic**: Documents must mention target companies AND control entities
- **OR Logic**: Within each control entity type, documents can mention ANY of the listed entities
- **Performance**: More control entities = fewer but more targeted results
- **Optional**: Control entities are completely optional - omit for broader analysis

---

## Query Builder

Advanced query construction for the Bigdata API with entity batching and control entities.

### Basic Usage

```python
from bigdata_research_tools.search.query_builder import (
    EntitiesToSearch,
    build_batched_query
)
from bigdata_client.models.search import DocumentType
from bigdata_research_tools.client import bigdata_connection

bigdata = bigdata_connection()
company_names = ["Apple Inc", "Microsoft Corp", "Tesla Inc"]
companies = []

for name in company_names:
    results = bigdata.knowledge_graph.find_companies(name)
    if results:
        companies.append(next(iter(results)))

control_entities = {
    "people": ["Tim Cook", "Satya Nadella"],
    "concepts": ["artificial intelligence"]
}

entity_keys = [entity.id for entity in companies]
entities_config = EntitiesToSearch(companies=entity_keys)

control_entities_config = None
if control_entities:
    control_entities_config = EntitiesToSearch(**control_entities)

# Build queries
queries = build_batched_query(
    sentences=["Technology innovation strategies"],
    keywords=["innovation", "technology"],
    entities=entities_config,
    control_entities=control_entities_config,

    batch_size=5,
    fiscal_year=2024,
    scope=DocumentType.TRANSCRIPTS,
    custom_batches=None,
    sources=None,
)
```

### EntitiesToSearch Class

```python
@dataclass
class EntitiesToSearch:
    people: Optional[List[str]] = None        # Person names
    companies: Optional[List[str]] = None     # Company names
    org: Optional[List[str]] = None          # Organization names
    product: Optional[List[str]] = None       # Product names
    place: Optional[List[str]] = None         # Place names
    topic: Optional[List[str]] = None         # Topic keywords
    concepts: Optional[List[str]] = None      # Concept terms
```

### Function Parameters - `build_batched_query()`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sentences` | `List[str]` | ✅ | Similarity search sentences |
| `keywords` | `List[str]` | ❌ | Keyword search terms |
| `entities` | `EntitiesToSearch` | ❌ | Entity configuration |
| `control_entities` | `EntitiesToSearch` | ❌ | Co-mention entities |
| `sources` | `List[str]` | ❌ | Source filters |
| `batch_size` | `int` | ✅ | Entities per batch |
| `fiscal_year` | `int` | ❌ | Fiscal year filter |
| `scope` | `DocumentType` | ✅ | Document scope |
| `custom_batches` | `List[EntitiesToSearch]` | ❌ | Custom entity batches |

---

## Search Manager

High-performance concurrent search execution with rate limiting.

### Basic Usage

```python
from bigdata_research_tools.search.search import run_search
from bigdata_client.models.search import DocumentType, SortBy
from bigdata_research_tools.search.query_builder import create_date_ranges

date_ranges = create_date_ranges("2024-11-01", "2025-03-15", "M")

results = run_search(
        queries,
        date_ranges=date_ranges,
        limit=50,
        scope=DocumentType.ALL,
        sortby=SortBy.RELEVANCE,
        rerank_threshold=None,
    )
```

### Function Parameters - `run_search()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `queries` | `List[QueryComponent]` |  | List of search queries |
| `date_ranges` | `DATE_RANGE_TYPE` | `None` | Date range specifications |
| `limit` | `int` | `10` | Results per query |
| `only_results` | `bool` | `True` | Return format control |
| `scope` | `DocumentType` | `ALL` | Document type filter |
| `sortby` | `SortBy` | `RELEVANCE` | Result sorting |
| `rerank_threshold` | `float` | `None` | Cross-encoder threshold |

**Note**: The function uses `bigdata_connection()` internally, so no explicit client parameter is needed.

### Rate Limiting Configuration

```python
from bigdata_research_tools.search.search import SearchManager, normalize_date_range
from bigdata_research_tools.client import bigdata_connection

bigdata = bigdata_connection()

manager = SearchManager(
    rpm=500,                         # Requests per minute
    bucket_size=100,                 # Token bucket capacity
    bigdata=bigdata                  # Optional: uses default if None
)

date_ranges = create_date_ranges("2024-11-01", "2025-03-15", "M")
date_ranges = normalize_date_range(date_ranges)
date_ranges.sort(key=lambda x: x[0])


# Use the manager for concurrent searches
results = manager.concurrent_search(
    queries=queries,
    date_ranges=date_ranges,
    limit=1000,
    scope=DocumentType.ALL
)
```

---

## LLM Integration

The library supports multiple LLM providers:

### OpenAI Configuration

```python
# Using OpenAI models
llm_model = "openai::gpt-4o-mini"     # Cost-effective
llm_model = "openai::gpt-4o"          # High performance
llm_model = "openai::gpt-3.5-turbo"   # Fast processing


# Set AWS credentials
import os
os.environ["OPENAI_API_KEY"] = "your_key"
```

### AWS Bedrock Configuration

```python
# Using Bedrock models
llm_model = "bedrock::anthropic.claude-3-sonnet-20240229-v1:0"
llm_model = "bedrock::anthropic.claude-3-haiku-20240307-v1:0"

# Set AWS credentials
import os
os.environ["AWS_ACCESS_KEY_ID"] = "your_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
```

### Azure Configuration

TBD

## Advanced Features

### Cross-Encoder Reranking

Improve search relevance with cross-encoder reranking:

```python
# Enable reranking with threshold
narrative_miner = NarrativeMiner(
    narrative_sentences=sentences,
    rerank_threshold=0.7,  # Higher = more strict
    # ... other parameters
)
```

### Custom Date Frequencies

Control temporal analysis granularity:

```python
# Frequency options
"Y"    # Yearly intervals
"6M"   # Six-monthly intervals  
"3M"   # Quarterly intervals (default)
"M"    # Monthly intervals
"W"    # Weekly intervals
"D"    # Daily intervals

# Usage example
results = screener.screen_companies(
    frequency="M",  # Monthly analysis
    # ... other parameters
)
```

### Batch Processing Optimization

Optimize performance with proper batching:

```python
# For large company universes
screener = ThematicScreener(
    companies=large_company_list,
    # ... other parameters
)

results = screener.screen_companies(
    batch_size=25,        # Larger batches for efficiency
    document_limit=20,    # More documents per company
    # ... other parameters
)
```

---

### Logging Configuration

```python
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Library-specific logging
logging.getLogger("bigdata_research_tools").setLevel(logging.DEBUG)
```

## Parameter Deep Dive

### Fiscal Year Guide

The `fiscal_year` parameter is **required** when working with **transcripts** or **filings** and determines which fiscal year documents to analyze.

#### How Fiscal Years Work

```python
# For fiscal year 2024, the system will search for:
fiscal_year = 2024

# Transcripts: Earnings calls from fiscal year 2024
# - Q1 2024 earnings calls (typically Jan-Mar 2024 reports)
# - Q2 2024 earnings calls (typically Apr-Jun 2024 reports)  
# - Q3 2024 earnings calls (typically Jul-Sep 2024 reports)
# - Q4 2024 earnings calls (typically Oct-Dec 2024 reports)

# Filings: SEC filings for fiscal year 2024
# - 10-K annual reports for fiscal year ending in 2024
# - 10-Q quarterly reports for quarters in fiscal year 2024
# - 8-K current reports filed during fiscal year 2024
```

#### Fiscal Year Examples

```python
# Analyze recent earnings calls
screener = ThematicScreener(
    # ... other parameters ...
    document_type=DocumentType.TRANSCRIPTS,
    fiscal_year=2024,  # Latest completed or current fiscal year
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Analyze historical filings
screener = ThematicScreener(
    # ... other parameters ...
    document_type=DocumentType.FILINGS,
    fiscal_year=2023,  # Previous fiscal year
    start_date="2023-01-01", 
    end_date="2023-12-31"
)
```

#### Important Notes

- **Calendar vs Fiscal Year**: Companies may have different fiscal year end dates (e.g., Apple's fiscal year ends in September)
- **Availability**: Not all companies may have documents for every fiscal year
- **Current Year**: For the current fiscal year, only filed documents up to the current date will be available

#### When NOT to Use Fiscal Year

```python
# For NEWS documents, fiscal_year should be None or omitted
screener = ThematicScreener(
    # ... other parameters ...
    document_type=DocumentType.NEWS,
    fiscal_year=None,  # Not applicable for news
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

### Focus Parameter Guide

The `focus` parameter provides **additional context and specificity** to guide the AI's theme generation and analysis.

#### What Focus Does

1. **Refines Theme Generation**: Influences how sub-themes are created
2. **Guides Analysis Direction**: Helps the AI understand what aspects to emphasize
3. **Improves Relevance**: Makes results more targeted to your specific research interest

#### Focus Examples

#### Basic Theme vs Focused Theme

```python
# Basic theme - broad analysis
screener = ThematicScreener(
    main_theme="Artificial Intelligence",
    focus="",  # No additional focus
    # ... other parameters
)
# Generated sub-themes might include:
# - AI Development, AI Applications, AI Ethics, AI Investment, etc.

# Focused theme - specific analysis
screener = ThematicScreener(
    main_theme="Artificial Intelligence", 
    focus="Focus on enterprise AI adoption, implementation challenges, and ROI measurement in large corporations",
    # ... other parameters
)
# Generated sub-themes might include:
# - Enterprise AI Implementation, AI ROI Metrics, AI Integration Challenges, 
#   Corporate AI Strategy, AI Vendor Selection, etc.
```

#### Best Practices for Focus

1. **Be Specific**: Include concrete aspects you want to explore
2. **Use Domain Language**: Include relevant terminology from your field
3. **Set Context**: Explain the business or research context
4. **Define Scope**: Clarify what should be included or excluded

```python
# Good focus examples:
focus = "Analyze cybersecurity investments, breach prevention strategies, and incident response capabilities specifically for financial services companies"

focus = "Examine renewable energy transition strategies including wind, solar, and battery storage investments, with emphasis on grid integration challenges"

focus = "Focus on AI-powered drug discovery, clinical trial optimization, and personalized medicine approaches in pharmaceutical companies"

# Less effective focus examples:
focus = "Look at technology"  # Too vague
focus = "AI and stuff"        # Unclear
focus = ""                    # No guidance provided
```

#### Focus for Different Document Types

```python
# For transcripts - focus on management commentary
focus = "Focus on management's strategic outlook, guidance updates, and responses to analyst questions about market positioning"

# For news - focus on market reactions
focus = "Analyze market sentiment, analyst opinions, and competitive positioning as reported in financial media"

# For filings - focus on formal disclosures
focus = "Examine risk factor disclosures, business segment performance, and regulatory compliance discussions in official filings"
```

---

## Interactive Tutorial

The library includes an interactive Jupyter notebook tutorial that demonstrates all key functionality with practical, working examples. This is the best way to get started with the library.

### Quick Start with uv

The fastest way to get up and running with the tutorial is using `uv` (the modern Python package manager):

#### Step 1: Clone and Navigate to Tutorial

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/bigdata-com/bigdata-research-tools.git
cd bigdata-research-tools/tutorial
```

#### Step 2: Set Up Environment with uv

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install tutorial dependencies
uv pip install -r requirements.txt

# Install the main package in development mode
uv pip install -e ../.
```

#### Step 3: Set Up Authentication

Create a `.env` file in the tutorial directory:

```bash
# Create .env file with your credentials
echo "BIGDATA_API_KEY=your_api_key_here" > .env
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env   # Required to run the Advanced Workflows
```

#### Step 4: Launch Jupyter Notebook

```bash
# Install Jupyter if not included in requirements
uv pip install jupyterlab

# Start Jupyter notebook
jupyter lab tutorial_notebook.ipynb
```

### Tutorial Overview

The interactive tutorial covers:

**📚 Fundamentals**
- Setting up authentication and connections
- Basic search functionality with `search_by_companies()`
- Custom query building with `run_search()`

**🔍 Key Features Demonstrated**
- Company-specific document searches
- Custom query construction and execution
- Result processing and analysis
- DataFrame export and manipulation

**💡 Learning Outcomes**
- Understand core library concepts
- See practical, working examples
- Get hands-on experience with real data

**🚀 Next Steps**
After completing the tutorial, you'll be ready to:
- Explore the advanced workflows (NarrativeMiner, ThematicScreener, RiskAnalyzer)
- Run the complete examples in the `examples/` directory
- Build custom analysis workflows for your specific use cases and explore our [Bigdata Cookbook](https://github.com/Bigdata-com/bigdata-cookbook), which features a collection of ready-to-use notebooks for a variety of finance-related guided workflows.

### Alternative Installation Methods

If you prefer not to use `uv`, you can also use traditional pip:

```bash
# Create virtual environment
python -m venv tutorial_env
source tutorial_env/bin/activate  # On Windows: tutorial_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e ..

# Launch notebook
jupyter notebook tutorial_notebook.ipynb
```

---

## Examples

The library includes several complete examples in the `examples/` directory. 

#### 1. Narrative Miner Example

**File**: `examples/narrative_miner.py`

**What it does**: Tracks AI-related narratives across transcripts

```bash
# Run the narrative miner example
cd examples
python narrative_miner.py
```

**Expected output**:
```
Environment variables loaded: True
INFO:bigdata_research_tools:Starting narrative mining...
INFO:bigdata_research_tools:Processing 15 narrative sentences...
INFO:bigdata_research_tools:Analysis complete. Results saved to narrative_miner_sample.xlsx
```

#### 2. Thematic Screener Example

**File**: `examples/thematic_screener.py`

**What it does**: Analyzes companies' exposure to "Chip Manufacturers" theme

```bash
# Run the thematic screener example
python thematic_screener.py
```

**Expected output**:
```
Environment variables loaded: True
INFO:bigdata_research_tools:Generating theme tree for: Chip Manufacturers
INFO:bigdata_research_tools:Screening 50 companies...
INFO:bigdata_research_tools:Creating visualizations...
# Browser opens with interactive dashboard
```

#### 3. Risk Analyzer Example

**File**: `examples/risk_analyzer.py`

**What it does**: Assesses risk exposure to US import tariffs

```bash
# Run the risk analyzer example
python risk_analyzer.py
```

**Expected output**:
```
Environment variables loaded: True
INFO:bigdata_research_tools:Creating risk taxonomy...
INFO:bigdata_research_tools:Analyzing risk exposure...
INFO:bigdata_research_tools:Risk analysis complete. Results saved to risk_analyzer_results.xlsx
# Browser opens with risk dashboard
```

#### 4. Query Builder Example

**File**: `examples/query_builder.py`

**What it does**: Demonstrates advanced query construction techniques

```bash
# Run the query builder example
python query_builder.py
```

**Expected output**:
```
INFO:__main__:======================================
INFO:__main__:TEST 1: Basic EntityConfig with Auto-batching
INFO:__main__:Generated 2 query components
INFO:__main__:Sample query structure: [QueryComponent(...)]
```

#### 5. Portfolio Constructor Example

**File**: `examples/portfolio_example.py`

**What it does**: Shows different portfolio construction methods

```bash
# Run the portfolio constructor example
python portfolio_example.py
```

**Expected output**:
```
INFO:__main__:======================================
INFO:__main__:EXAMPLE 1: Basic Equal-Weighted Portfolio (Sector Balanced)
INFO:__main__:Portfolio Size: 20 companies
INFO:__main__:Sectors Represented: 5
```

#### 6. Search by Companies Example

**File**: `examples/search_by_companies.py`

**What it does**: Shows how to search for documents mentioning specific companies and topics

```bash
# Run the search by companies example
python search_by_companies.py
```

**Expected output**:
```
Environment variables loaded: True
INFO:__main__:Found: Apple Inc (ID: D8442C)
INFO:__main__:Found: Microsoft Corporation (ID: D4A6CC)
INFO:__main__:Found 24 relevant documents
INFO:__main__:  Apple Inc: 15 documents
INFO:__main__:  Microsoft Corporation: 9 documents
# Results exported to search_by_companies_results.xlsx
```

#### 7. Run Search Example

**File**: `examples/run_search.py`

**What it does**: Demonstrates custom query building and search execution

```bash
# Run the run_search example
python run_search.py
```

**Expected output**:
```
Environment variables loaded: True
INFO:__main__:Generated 4 search queries
INFO:__main__:Searching across 3 time periods
INFO:__main__:Found 32 documents total
INFO:__main__:  Reuters: 12 documents
INFO:__main__:  Bloomberg: 8 documents
# Results exported to run_search_results.xlsx
```
---

## Support and Resources

- **Documentation**: [https://docs.bigdata.com](https://docs.bigdata.com)
- **API Reference**: Check the `docs/` directory for detailed API documentation
- **Examples**: See the `examples/` directory for complete working examples
- **Issues**: Report issues through [support@bigdata.com](mailto:support@bigdata.com)

---

## License

This software is licensed for use solely under the terms agreed upon in the
applicable Master Agreement and Order Schedule between the parties.
For trials, the applicable legal documents are the Mutual Non-Disclosure
Agreement, or if applicable the Trial Agreement.
No other rights or licenses are granted by implication, estoppel, or otherwise.
For further details, please refer to your specific Master Agreement and Order
Schedule or contact us at legal@ravenpack.com.

---

**RavenPack** | **Bigdata.com** \
All rights reserved © 2025


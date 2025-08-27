# Bigdata Research Tools - Comprehensive User Guide

<p align="center">
  <picture>
    <source srcset="https://sdk.bigdata.com/en/latest/_static/bigdata_dark.svg" media="(prefers-color-scheme: dark)">
    <img src="https://sdk.bigdata.com/en/latest/_static/bigdata_light.svg" alt="Bigdata Logo" width="250">
  </picture>
</p>

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Authentication Setup](#authentication-setup)
4. [Core Workflows](#core-workflows)
   - [Narrative Miner](#narrative-miner)
   - [Thematic Screener](#thematic-screener)
   - [Risk Analyzer](#risk-analyzer)
5. [Utility Modules](#utility-modules)
   - [Query Builder](#query-builder)
   - [Portfolio Constructor](#portfolio-constructor)
   - [Search Manager](#search-manager)
   - [Visualization Tools](#visualization-tools)
6. [Advanced Features](#advanced-features)
7. [Configuration Options](#configuration-options)
8. [Examples and Tutorials](#examples-and-tutorials)
9. [Troubleshooting](#troubleshooting)

---

## Overview

**Bigdata Research Tools** is a Python library designed to automate and streamline research workflows using the Bigdata.com API. It provides high-level, plug-and-play functions for building customized research processes with minimal effort.

### Key Features

- **🔍 Narrative Mining**: Track narrative evolution across news, transcripts, and filings
- **📊 Thematic Screening**: Analyze company exposure to specific themes
- **⚠️ Risk Analysis**: Assess company risk exposure to various scenarios
- **📈 Portfolio Construction**: Build balanced and weighted portfolios with constraints
- **🎨 Interactive Visualizations**: Create comprehensive dashboards and charts
- **⚡ Concurrent Processing**: Execute multiple searches efficiently with rate limiting
- **🛡️ Thread-Safe Operations**: Built-in safety for concurrent processing

### Library Architecture

```
bigdata_research_tools/
├── workflows/          # High-level research workflows
├── search/            # Search utilities and query builders
├── portfolio/         # Portfolio construction tools
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
```

### Using .env File

Create a `.env` file in your project directory:

```bash
BIGDATA_USERNAME=your_username
BIGDATA_PASSWORD=your_password
```

Load the environment variables in your Python script:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Core Workflows

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
| `fiscal_year` | `int` | ❌ | Fiscal year for transcripts/filings |
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
DocumentType.ALL           # All document types
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
| `fiscal_year` | `int` | ❌ | Required for transcripts/filings (see [Fiscal Year Guide](#fiscal-year-guide)) |
| `sources` | `List[str]` | ❌ | Source filters |
| `rerank_threshold` | `float` | ❌ | Reranking threshold |
| `focus` | `str` | `""` | Additional focus description (see [Focus Parameter Guide](#focus-parameter-guide)) |

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

### Company Objects

Company objects are `bigdata_client.models.entities.Company` instances that represent companies in the Bigdata knowledge graph. Here's how to obtain them:

#### Method 1: From Watchlists (Recommended)

```python
from bigdata_research_tools.client import bigdata_connection

# Connect to Bigdata API
bigdata = bigdata_connection()

# Get companies from a specific watchlist
watchlist_id = "a60c351a-1822-4a88-8c45-a4e78abd979a"  # Example GRID watchlist
watchlist = bigdata.watchlists.get(watchlist_id)
companies = bigdata.knowledge_graph.get_entities(watchlist.items)

print(f"Found {len(companies)} companies in watchlist")
# Output: Found 50 companies in watchlist
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

# Filter by market cap (if available in metadata)
large_cap_companies = [
    company for company in all_companies
    if hasattr(company, 'market_cap') and company.market_cap > 10_000_000_000
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
| `fiscal_year` | `int` | ❌ | Fiscal year filter (see [Fiscal Year Guide](#fiscal-year-guide)) |
| `sources` | `List[str]` | ❌ | Source filters |
| `rerank_threshold` | `float` | ❌ | Reranking threshold |
| `focus` | `str` | `""` | Additional focus description (see [Focus Parameter Guide](#focus-parameter-guide)) |

### Control Entities

Control entities allow you to filter results based on **co-mentions** - documents must mention both your target companies AND the control entities to be included in results.

#### How Control Entities Work

```python
# Example: Find documents about Tesla that also mention China or Taiwan
analyzer = RiskAnalyzer(
    main_theme="Supply Chain Risk",
    companies=[tesla_company],  # Target companies
    control_entities={
        "place": ["China", "Taiwan"]  # Must also mention these places
    }
)
# Results will only include documents that mention Tesla AND (China OR Taiwan)
```

#### Control Entity Types

```python
control_entities = {
    # Geographic filters
    "place": ["United States", "China", "Taiwan", "Germany"],
    
    # People filters  
    "people": ["Elon Musk", "Tim Cook", "Satya Nadella"],
    
    # Company filters
    "companies": ["Apple Inc", "Microsoft Corp", "Tesla Inc"],
    
    # Topic/concept filters
    "topics": ["regulation", "trade policy", "cybersecurity"],
    
    # Product filters  
    "product": ["iPhone", "Model S", "Azure"]
}
```

#### Real-World Use Cases

```python
# Geopolitical Risk Analysis
control_entities = {
    "place": ["Russia", "Ukraine", "China"],
    "topics": ["sanctions", "trade war", "geopolitical tension"]
}

# Regulatory Risk Analysis  
control_entities = {
    "topics": ["FDA approval", "regulatory compliance", "SEC investigation"],
    "people": ["Federal Reserve Chair", "SEC Commissioner"]
}

# Competitive Analysis
control_entities = {
    "companies": ["Amazon", "Google", "Meta"],
    "topics": ["market share", "competition", "antitrust"]
}
```

#### Important Notes

- **AND Logic**: Documents must mention target companies AND control entities
- **OR Logic**: Within each control entity type, documents can mention ANY of the listed entities
- **Performance**: More control entities = fewer but more targeted results
- **Optional**: Control entities are completely optional - omit for broader analysis

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

---

## Utility Modules

## Query Builder

Advanced query construction for the Bigdata API with entity batching and control entities.

### Basic Usage

```python
from bigdata_research_tools.search.query_builder import (
    EntitiesToSearch,
    build_batched_query
)
from bigdata_client.models.search import DocumentType

# Define entities to search for
entities = EntitiesToSearch(
    companies=["Apple Inc", "Microsoft Corp"],
    people=["Tim Cook", "Satya Nadella"],
    concepts=["artificial intelligence"]
)

# Build queries
queries = build_batched_query(
    sentences=["Technology innovation strategies"],
    keywords=["innovation", "technology"],
    entities=entities,
    batch_size=5,
    fiscal_year=2024,
    scope=DocumentType.TRANSCRIPTS
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

### Custom Batching

```python
custom_batches = [
    # Tech companies
    EntitiesToSearch(
        companies=["Apple Inc", "Microsoft Corp"],
        concepts=["innovation", "technology"]
    ),
    # Auto companies
    EntitiesToSearch(
        companies=["Tesla", "Ford"],
        concepts=["electric vehicles"]
    )
]

queries = build_batched_query(
    sentences=["Industry trends"],
    entities=None,
    custom_batches=custom_batches,
    batch_size=10,
    scope=DocumentType.ALL
)
```

---

## Portfolio Constructor

Build balanced and weighted portfolios with sophisticated constraint management.

### Basic Usage

```python
from bigdata_research_tools.portfolio.portfolio_constructor import (
    PortfolioConstructor, 
    WeightMethod
)
import pandas as pd

# Sample data
df = pd.DataFrame({
    'Company': ['Apple', 'Microsoft', 'Google', 'Tesla'],
    'Sector': ['Technology', 'Technology', 'Technology', 'Auto'],
    'Market_Cap': [2800, 2500, 1800, 800],
    'ESG_Score': [85, 82, 78, 72],
    'Composite_Score': [92, 89, 85, 78]
})

constructor = PortfolioConstructor(
    max_iterations=1000,
    tolerance=1e-6
)

portfolio = constructor.construct_portfolio(
    df=df,
    score_col="Composite_Score",
    balance_col="Sector",
    weight_col="Market_Cap",
    size=20,
    max_position_weight=0.08,    # 8% max per position
    max_category_weight=0.25,    # 25% max per sector
    weight_method=WeightMethod.COLUMN
)
```

### Weight Methods

```python
class WeightMethod(Enum):
    EQUAL = auto()    # Equal weights for all positions
    COLUMN = auto()   # Weight by column values (e.g., market cap)
    SCORE = auto()    # Weight by scores (softmax normalized)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_iterations` | `int` | `1000` | Max constraint iterations |
| `tolerance` | `float` | `1e-6` | Convergence tolerance |

### Method Parameters - `construct_portfolio()`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `df` | `DataFrame` | ✅ | Input company data |
| `score_col` | `str` | ✅ | Column for ranking companies |
| `balance_col` | `str` | ✅ | Column for balancing (sector/industry) |
| `weight_col` | `str` | ❌ | Column for weighting (if applicable) |
| `size` | `int` | ❌ | Target portfolio size |
| `max_position_weight` | `float` | `0.05` | Max weight per position (5%) |
| `max_category_weight` | `float` | `0.15` | Max weight per category (15%) |
| `weight_method` | `WeightMethod` | `EQUAL` | Weighting methodology |

### Examples by Weight Method

#### Equal Weighting
```python
portfolio = constructor.construct_portfolio(
    df=df,
    score_col="Composite_Score",
    balance_col="Sector",
    weight_method=WeightMethod.EQUAL
)
```

#### Market Cap Weighting
```python
portfolio = constructor.construct_portfolio(
    df=df,
    score_col="Composite_Score",
    balance_col="Sector",
    weight_col="Market_Cap",
    weight_method=WeightMethod.COLUMN
)
```

#### Score-Based Weighting (Softmax)
```python
portfolio = constructor.construct_portfolio(
    df=df,
    score_col="Composite_Score",
    balance_col="Sector",
    weight_col="ESG_Score",
    weight_method=WeightMethod.SCORE
)
```

---

## Search Manager

High-performance concurrent search execution with rate limiting.

### Basic Usage

```python
from bigdata_research_tools.search.search import run_search

# Simple search execution (uses internal bigdata_connection())
results = run_search(
    queries=query_list,
    limit=1000
)
```

### Function Parameters - `run_search()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `queries` | `List[QueryComponent]` | ✅ | List of search queries |
| `date_ranges` | `DATE_RANGE_TYPE` | `None` | Date range specifications |
| `limit` | `int` | `10` | Results per query |
| `only_results` | `bool` | `True` | Return format control |
| `scope` | `DocumentType` | `ALL` | Document type filter |
| `sortby` | `SortBy` | `RELEVANCE` | Result sorting |
| `rerank_threshold` | `float` | `None` | Cross-encoder threshold |

**Note**: The function uses `bigdata_connection()` internally, so no explicit client parameter is needed.

### Rate Limiting Configuration

```python
from bigdata_research_tools.search.search import SearchManager
from bigdata_research_tools.client import bigdata_connection

bigdata = bigdata_connection()

manager = SearchManager(
    rpm=500,                         # Requests per minute
    bucket_size=100,                 # Token bucket capacity
    bigdata=bigdata                  # Optional: uses default if None
)

# Use the manager for concurrent searches
results = manager.concurrent_search(
    queries=queries,
    date_ranges=date_ranges,
    limit=1000,
    scope=DocumentType.ALL
)
```

---

## Visualization Tools

Create interactive dashboards and visualizations for analysis results.

### Thematic Exposure Dashboard

```python
from bigdata_research_tools.visuals import create_thematic_exposure_dashboard

# Create dashboard from screening results
fig, industry_fig = create_thematic_exposure_dashboard(
    df_company=results["df_company"],
    n_companies=15,
    config={
        'heatmap_colorscale': 'Plasma',
        'dashboard_height': 1800,
        'main_title': 'Custom Thematic Analysis'
    }
)

# Display dashboards
fig.show(renderer="browser")
industry_fig.show(renderer="browser")
```

### Risk Exposure Dashboard

```python
from bigdata_research_tools.visuals import create_risk_exposure_dashboard

fig, industry_fig = create_risk_exposure_dashboard(
    df_company=risk_results["df_company"],
    n_companies=20
)

fig.show(renderer="browser")
industry_fig.show(renderer="browser")
```

### Dashboard Configuration

```python
custom_config = {
    # Visual styling
    'heatmap_colorscale': 'Viridis',      # Color scheme
    'dashboard_height': 2000,              # Dashboard height
    'company_column': 'Company',           # Company column name
    
    # Content configuration
    'top_themes_count': 8,                 # Themes to display
    'main_title': 'Custom Analysis',       # Dashboard title
    
    # Layout settings
    'subplot_spacing': 0.05,               # Space between plots
    'margin': {'l': 50, 'r': 50, 't': 100, 'b': 50}
}
```

---

## Advanced Features

### LLM Integration

The library supports multiple LLM providers:

#### OpenAI Configuration
```python
# Using OpenAI models
llm_model = "openai::gpt-4o-mini"     # Cost-effective
llm_model = "openai::gpt-4o"          # High performance
llm_model = "openai::gpt-3.5-turbo"   # Fast processing
```

#### AWS Bedrock Configuration
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

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BIGDATA_USERNAME` | API username | Required |
| `BIGDATA_PASSWORD` | API password | Required |
| `BIGDATA_FILE_CONFIG` | Config file path | None |
| `BIGDATA_OTHER_ENTITY_PLACEHOLDER` | Entity placeholder | "Other Company" |
| `BIGDATA_TARGET_ENTITY_PLACEHOLDER` | Target placeholder | "Target Company" |

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

### Resource Management

```python
# Configure concurrent processing
from bigdata_research_tools.search.search import SearchManager

manager = SearchManager(
    max_workers=8,              # Adjust based on your system
    requests_per_minute=300,    # Respect API limits
    token_bucket_size=50       # Buffer for burst requests
)
```

---

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

#### Real-World Focus Examples

```python
# Climate Risk Analysis
analyzer = RiskAnalyzer(
    main_theme="Climate Change Impact",
    focus="Assess physical climate risks including extreme weather events, sea level rise, and temperature changes affecting operations, supply chains, and asset values",
    # ... other parameters
)

# Supply Chain Resilience
screener = ThematicScreener(
    main_theme="Supply Chain Management",
    focus="Examine supply chain diversification strategies, nearshoring trends, and supplier relationship management in response to recent disruptions",
    # ... other parameters
)

# ESG Investment Trends
screener = ThematicScreener(
    main_theme="ESG Investing",
    focus="Analyze how companies are integrating environmental, social, and governance factors into capital allocation decisions and stakeholder communications",
    # ... other parameters
)
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

## Examples and Tutorials

### Complete Workflow Example

```python
import logging
from dotenv import load_dotenv
from bigdata_research_tools.workflows import ThematicScreener
from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.visuals import create_thematic_exposure_dashboard
from bigdata_client.models.search import DocumentType

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Get companies
bigdata = bigdata_connection()
watchlist = bigdata.watchlists.get("your_watchlist_id")
companies = bigdata.knowledge_graph.get_entities(watchlist.items)

# Run thematic screening
screener = ThematicScreener(
    llm_model="openai::gpt-4o-mini",
    main_theme="Renewable Energy Transition",
    companies=companies,
    start_date="2024-01-01",
    end_date="2024-12-31",
    document_type=DocumentType.TRANSCRIPTS,
    fiscal_year=2024,
    focus="Focus on solar, wind, and battery technologies"
)

results = screener.screen_companies(
    document_limit=15,
    frequency="M",
    export_path="renewable_energy_analysis.xlsx"
)

# Create visualizations
fig, industry_fig = create_thematic_exposure_dashboard(
    df_company=results["df_company"],
    n_companies=20
)

fig.show(renderer="browser")
print(f"Analysis complete. {len(results['df_company'])} companies analyzed.")
```

### Risk Scenario Analysis

```python
from bigdata_research_tools.workflows.risk_analyzer import RiskAnalyzer

# Define risk scenario
analyzer = RiskAnalyzer(
    llm_model="openai::gpt-4o-mini",
    main_theme="Cybersecurity Threats",
    companies=tech_companies,
    start_date="2024-01-01",
    end_date="2024-12-31",
    document_type=DocumentType.NEWS,
    keywords=["cybersecurity", "data breach", "ransomware"],
    control_entities={
        "concepts": ["artificial intelligence", "cloud computing"],
        "place": ["United States", "Europe"]
    },
    focus="Analyze risks from AI-powered cyber attacks on cloud infrastructure"
)

risk_results = analyzer.screen_companies(
    document_limit=25,
    frequency="M",
    export_path="cybersecurity_risk_assessment.xlsx"
)

# Generate risk dashboard
from bigdata_research_tools.visuals import create_risk_exposure_dashboard

risk_fig, risk_industry_fig = create_risk_exposure_dashboard(
    df_company=risk_results["df_company"],
    n_companies=15
)

risk_fig.show(renderer="browser")
```

### Portfolio Construction Workflow

```python
import pandas as pd
from bigdata_research_tools.portfolio.portfolio_constructor import (
    PortfolioConstructor, WeightMethod
)

# Load screening results
df_scores = pd.read_excel("thematic_screening_results.xlsx", sheet_name="By Company")

# Construct portfolio
constructor = PortfolioConstructor(
    max_iterations=2000,
    tolerance=1e-8
)

portfolio = constructor.construct_portfolio(
    df=df_scores,
    score_col="Composite Score",
    balance_col="Sector",
    weight_col="Market Cap",
    size=30,
    max_position_weight=0.06,    # 6% max position
    max_category_weight=0.20,    # 20% max sector
    weight_method=WeightMethod.COLUMN
)

print("Portfolio Construction Results:")
print(f"Total companies: {len(portfolio)}")
print(f"Total weight: {portfolio['weight'].sum():.1%}")
print(f"Weight range: {portfolio['weight'].min():.1%} - {portfolio['weight'].max():.1%}")

# Export portfolio
portfolio.to_excel("balanced_portfolio.xlsx", index=False)
```

---

## Troubleshooting

### Common Issues

#### Authentication Errors
```python
# Check credentials
import os
print("Username:", os.environ.get("BIGDATA_USERNAME"))
print("Password set:", bool(os.environ.get("BIGDATA_PASSWORD")))

# Test connection
from bigdata_research_tools.client import bigdata_connection
try:
    bigdata = bigdata_connection()
    print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
```

#### Missing Dependencies
```python
# Check Excel dependencies
from bigdata_research_tools.excel import check_excel_dependencies
if not check_excel_dependencies():
    print("Install Excel dependencies: pip install bigdata-research-tools[excel]")

# Check Plotly dependencies
from bigdata_research_tools.visuals.thematic_visuals import check_plotly_dependencies
if not check_plotly_dependencies():
    print("Install Plotly: pip install bigdata-research-tools[plotly]")
```

#### Memory and Performance Issues
```python
# Reduce batch sizes for large datasets
results = screener.screen_companies(
    batch_size=5,         # Smaller batches
    document_limit=5,     # Fewer documents
    frequency="3M"        # Less frequent intervals
)

# Monitor memory usage
import psutil
print(f"Memory usage: {psutil.virtual_memory().percent}%")
```

#### Rate Limiting
```python
# Adjust rate limits
from bigdata_research_tools.search.search import SearchManager

manager = SearchManager(
    max_workers=2,              # Reduce concurrency
    requests_per_minute=200,    # Lower rate limit
    token_bucket_size=30       # Smaller buffer
)
```

### Error Handling

```python
import logging
from bigdata_research_tools.workflows import NarrativeMiner

logger = logging.getLogger(__name__)

try:
    miner = NarrativeMiner(
        narrative_sentences=sentences,
        llm_model="openai::gpt-4o-mini",
        start_date="2024-01-01",
        end_date="2024-12-31",
        document_type=DocumentType.NEWS
    )
    
    results = miner.mine_narratives()
    
except ValueError as e:
    logger.error(f"Configuration error: {e}")
except EnvironmentError as e:
    logger.error(f"Authentication error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Validation Checks

```python
# Validate date formats
from datetime import datetime

def validate_date(date_string):
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# Validate LLM model format
def validate_llm_model(model_string):
    return "::" in model_string and len(model_string.split("::")) == 2

# Example usage
start_date = "2024-01-01"
llm_model = "openai::gpt-4o-mini"

assert validate_date(start_date), f"Invalid date format: {start_date}"
assert validate_llm_model(llm_model), f"Invalid LLM model format: {llm_model}"
```

---

## Support and Resources

- **Documentation**: [https://sdk.bigdata.com](https://sdk.bigdata.com)
- **API Reference**: Check the `docs/` directory for detailed API documentation
- **Examples**: See the `examples/` directory for complete working examples
- **Issues**: Report issues through your organization's support channels

---

*Last updated: January 2025*
*Version: 0.17.3*

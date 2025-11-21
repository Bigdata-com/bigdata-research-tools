(Changelog)=
# Changelog

All notable changes to the bigdata-research-tools package will be documented in this
file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-21
Preparation for a first stable release.

## Added
- Added support for providing several fiscal years to any workflow or search function that
  accepts a `fiscal_year` parameter. The parameter can now be a single integer or a list
  of integers. When a list is provided, the workflow or function will search for the union
  of all values provided.

### Changed
- Refactor the `themes` submodule to `tree`, allowing for a more generic tree structure
  that can be re-used accross different workflows.
- Moved `workflows.utils.save_to_excel` to `excel.save_to_excel`, grouping all optional
  features related to Excel in one place.
- Renamed `settings` to `utils` to better reflect its purpose as a utility module and free
  the name for future use.
- Renamed all `freq` parameters to `frequency` for better clarity and consistency accross workflows.
- Implement custom motivation prompts for different use cases, including thematic screening and risk analysis.

### Fixed
- Fix duplicate dependencies in main vs optional dependencies. `openai` is now only optional while `graphviz`, `openpyxl` and `Pillow` is now only in main dependencies.

### Removed
- Removed support for Python 3.9 as it has reached its end of life. The minimum supported version is now Python 3.10.
- Removed `ipython` from main dependencies and removed unused function `bigdata_research_tools.workflows.utils.display_output_chunks_dataframe`.

## [0.21.1] - 2025-11-13

### Added
- Fix typing and async bugs in Python3.9


## [0.21.0] - 2025-11-05

### Added
- Now the LLMEngine accepts sending keywords that will be used for initializing the client
- NarrativeMiner, NarrativeLabeler, ScreenerLabeler and Labeler benefit from being able to send an LLMEngine already initialized instead of the provider::model string

## [0.20.2] - 2025-10-21

### Fix
- Fix the function `create_date_intervals` in file `query_builder.py`. It now creates proper weekly/monthly/yearly intervals without losing any day before the first interval.
- Fix `uv sync` not properly installing the `bigdata_research_tools` package.
- Fix tracing reporting incorrect query usage.

## [0.20.1] - 2025-09-16

### Fix
- Fix code duplication that caused duplicated LLM calls introduced at 0.19.0 (#5)

## [0.20.0] - 2025-09-15

### Added
- Add support for Bigdata.com API keys for authentication. Follow this guide to create your API key: https://docs.bigdata.com/api-rest/introduction
- Applied the observer pattern to workflows to allow external monitoring of progress during execution. You can find more details on the `bigdata_research_tools.utils.observer` module.
- Add utilities to create watchlists from a list of company names and to find watchlists by name and optionally fuzzy matching.


## [0.19.0] - 2025-09-03

### Added
- First version of Azure provider included in the LLMEngine

### Changed
- Now LLM response in the function `generate_theme_tree` uses `repair_json` to clean the response.

## [0.18.1] - 2025-08-28

### Fix
- Labeler class now choses a parallel call if Bedrock provider is used and concurrent async loop if any other is selected
- Functions `generate_theme_tree` and `generate_risk_tree` are called passing down the llm_model provided.

### Changed
- Improved validation of json responses from llms.

## [0.18.0] - 2025-08-25

### Added
- First version of the async bedrock llm provider
- Make `__version__` dynamic based on package metadata

### Fix
- Entity-level motivation was not being returned in the `screen_companies` function


## [0.17.3] - 2025-08-08

### Changed
- Improve logging and tracing

## [0.17.2] - 2025-07-17

### Changed
- Improve logging and tracing

## [0.17.1] - 2025-07-16

### Changed 
- Reinstate filter for company entities in screener

## [0.17.0] - 2025-07-16

### Changed 
- Fix logic to add logo to excel spreadsheets
- Add post-processing fields to narrative miner
- Add tracing when calling search_by_companies

## [0.16.0] - 2025-07-10

### Added 
- Add thematic screener visuals code
- Add risk scenario workflow, which includes prompts, labeler, visuals, risk theme tree

### Changed 
- Moved over input validation to query builder
- Parse Reporting Entity correctly in query builder
- Show summaries in leaf nodes of theme tree
- Simplify prompt logic for thematic mindmapper

## [0.15.1] - 2025-06-12

### Changed
- Fix bug in labeler logic which affected Colab

## [0.15.0] - 2025-06-11

### Added 
- Logic to add a LLM generated motivation explaining why a company exposed to a theme
- Logic to construct a portfolio of a certain size, with balancing (by sector/region/other) and 
  weighting (by thematic score/other score) capabilities
- Logic to build queries with custom batching and non-company entities
- Workflow usage metrics

### Changed
- Generalise input params for labeler to work for Risk Scenario Analyzer

## [0.14.0] - 2025-05-30

### Changed
- Chunk numbers now match the Chunk index from the Vector DB
- Add dependencies like bigdata logo and IPython to run 2 workflows seamlessly
- Cleanup of Miners and Screeners logic
- Update Miners docs to use newly refactored code
- Remove any tech debt/unused code from the library

## [0.13.0] - 2025-04-25

### Added

* Add prompt which better integrates analyst focus into mindmapper

### Changed

* Updated narrative miners cookbook to use another source (as we no longer have CNBC)
* Fix excel logo 
* Update cookbooks section of documentation to explain why to look at the cookbook(s)
* Change ordering of docs
* Fix the labelling prompt to be the same as in thematic screener notebook
* Set the default temperature for all LLM calls to 0

## [0.12.0] - 2025-03-24

### Added

* Add screener class for the Narrative Executive Factor:
  * `screeners.ExecutiveNarrativeFactor`
* Add labeler for company screening: 
  * `labeler.screener_labeler`.
* Add screener search:
  * `search.screener_search`.
* Add a themes module with logic to generate sub-themes from a main one:
  * `themes.generate_theme_tree`.
  * `themes.ThemeTree` class.
* Resources folder moved inside the package source data.
* API Reference updated:
  * [Screeners](../docs/reference/screeners.rst)
  * [Search](../docs/reference/search.rst)
  * [Themes](../docs/reference/themes.rst)


## [0.11.0] - 2025-02-27

### Added

* Add narrative miner classes to track narratives in transcipts, filings, news (miners folder)
* Add capability to choose which LLM to run prompts with (llm folder)
* Add supporting functionality for hybrid searches and labelling (labeler and search folders)
* Add logic to export the structured dataset of labelled chunks to excel workbook (excel.py)
* Cookbook [Miners](../docs/cookbooks/miners.rst)
* API Reference [API Reference](../docs/reference/miners.rst)

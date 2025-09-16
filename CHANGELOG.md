(Changelog)=
# Changelog

All notable changes to the bigdata-research-tools package will be documented in this
file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

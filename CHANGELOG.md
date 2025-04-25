(Changelog)=
# Changelog

All notable changes to the bigdata-research-tools package will be documented in this
file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
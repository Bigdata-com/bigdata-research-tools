.PHONY: tests lint format

tests:
	@uv run -m pytest --cov --cov-report term --cov-report xml:./coverage-reports/coverage.xml -s tests/*

lint:
	@uvx ruff check --extend-select I --fix src/bigdata_research_tools/ examples/ tutorial/ tests/

lint-check:
	@uvx ruff check --extend-select I src/bigdata_research_tools/ examples/ tutorial/ tests/

format:
	@uvx ruff format src/bigdata_research_tools/ examples/ tutorial/ tests/

type-check:
	@uvx ty check --python-version 3.13 src/bigdata_research_tools/ examples/ tests/ # tutorial/ # Fix version to 3.13 due to this issue https://github.com/astral-sh/ty/issues/1355 # Ignore tutorials, the issues come from this open issue https://github.com/astral-sh/ty/issues/1297
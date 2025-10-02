.PHONY: tests lint format

tests:
	@uv run -m pytest --cov --cov-config=.coveragerc  --cov-report term --cov-report xml:./coverage-reports/coverage.xml -s tests/*

lint:
	@uvx ruff check --extend-select I --fix src/bigdata_research_tools/ tests/

lint-check:
	@uvx ruff check --extend-select I src/bigdata_research_tools/ tests/

format:
	@uvx ruff format src/bigdata_research_tools/ tests/

type-check:
	@uvx ty check src/bigdata_research_tools/ tests/
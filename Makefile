.DEFAULT_GOAL := help
.PHONY: help install ruff run test coverage coverage-html

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Uv install dependencies and set up the development environment
	uv sync --group dev --active

ruff: ## Run Ruff on all the code and autofix when possible
	ruff format .
	ruff check . --fix

test: ## Run pytest
	uv run pytest

coverage: ## Run pytest with inline terminal coverage report (branch + missing lines)
	uv run pytest --cov --cov-report=term-missing

coverage-html: ## Run pytest and open HTML coverage report
	uv run pytest --cov --cov-report=term-missing --cov-report=html

run: ## Run mcp_snowflake_server locally
	uv --directory . run mcp_snowflake_server


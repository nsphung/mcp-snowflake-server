.DEFAULT_GOAL := help
.PHONY: help install hooks hooks-run fmt fmt-check ruff format run test coverage coverage-html

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (uv + bun) and set up Git hooks
	uv sync --group dev --active
	bun install
	uv run prek install -f

hooks: ## Install prek Git hooks
	uv run prek install -f

hooks-run: ## Run prek hooks on all files
	uv run prek run --all-files

fmt: ## Format all files with oxfmt
	bun run fmt

fmt-check: ## Check formatting with oxfmt (non-destructive)
	bun run fmt:check

ruff: ## Run Ruff on all the code and autofix when possible
	ruff format .
	ruff check . --fix

format: hooks-run ## Format code using hooks (ruff, mypy, prek)

test: ## Run pytest
	uv run pytest

coverage: ## Run pytest with inline terminal coverage report (branch + missing lines)
	uv run pytest --cov --cov-report=term-missing

coverage-html: ## Run pytest and open HTML coverage report
	uv run pytest --cov --cov-report=term-missing --cov-report=html

run: ## Run mcp_snowflake_server locally
	uv --directory . run mcp_snowflake_server

validate-server: ## Validate server.json against the MCP registry API (no auth required)
	@payload=$$(jq '.version = "0.0.0" | .packages[0].version = "0.0.0" | .packages[1].identifier |= gsub("\\$${VERSION}"; "0.0.0")' server.json); \
	result=$$(echo "$$payload" | curl -sf -X POST https://registry.modelcontextprotocol.io/v0.1/validate \
		-H 'Content-Type: application/json' \
		-d @-); \
	echo "$$result" | jq .; \
	echo "$$result" | jq -e '.valid == true' > /dev/null && echo "server.json is valid" || (echo "server.json is INVALID" && exit 1)

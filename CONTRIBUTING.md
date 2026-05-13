# Contributing to Snowflake MCP Server NSP

Thanks for your interest in contributing to `mcp-snowflake-server-nsp`.

This guide covers local development, contributor workflow, and project conventions. For end-user installation and usage, see [`README.md`](./README.md).

Please review our community expectations in [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md).

## Prerequisites

You will need:

- Python 3.13+
- [`uv`](https://github.com/astral-sh/uv)
- [`bun`](https://bun.sh)
- Git

Optional (depending on how you want to run locally):

- [Visual Studio Code](https://code.visualstudio.com/)
- [Claude Desktop](https://claude.ai/download)
- Docker

## Development Setup

1. Clone the repository.
2. Install development dependencies and Git hooks:

```bash
make install
```

This command will:

- sync Python dependencies with `uv`
- install JavaScript tooling with `bun`
- install `prek` Git hooks

To reinstall hooks later:

```bash
make hooks
```

## Local Credentials

Use one of these options for local credentials:

- Copy `.env.example` to `.env`
- Or use a TOML connections file such as [`example_connections.toml`](./example_connections.toml)

> **Important:** Do not quote values and do not use inline comments in `.env` files. Use `VAR=value`, not `VAR="value"` or `VAR=value # comment`.

Typical `.env` flow:

```bash
cp .env.example .env
```

Then configure one of the supported authentication methods:

- external browser
- password
- key-pair
- OAuth 2.0 client credentials
- OAuth bearer token

For authentication details and runtime flags, refer to [`README.md`](./README.md#authentication) and [`README.md`](./README.md#configuration-reference).

## Running Locally

Run the server directly from source:

```bash
make run
```

Equivalent command:

```bash
uv --directory . run mcp_snowflake_server
```

To hide specific databases, schemas, or tables during local development, edit [`runtime_config.json`](./runtime_config.json).

### VS Code Local Setup

1. Install `uv`.
2. Prepare `.env` or a TOML connections file.
3. Test the server locally with `make run`.
4. Add a local server entry to `.vscode/mcp.json`.

<details>
<summary><strong>TOML configuration (recommended)</strong></summary>

```jsonc
"snowflake-local": {
    "type": "stdio",
    "command": "/absolute/path/to/uv",
    "args": [
      "--python=3.13",
      "--directory", "/absolute/path/to/mcp_snowflake_server",
      "run", "mcp_snowflake_server",
      "--connections-file", "/absolute/path/to/snowflake_connections.toml",
      "--connection-name", "development"
      // Optional flags — see README Configuration Reference
    ],
}
```

</details>

<details>
<summary><strong>Environment variables</strong></summary>

```jsonc
"snowflake-local": {
    "type": "stdio",
    "command": "/absolute/path/to/uv",
    "args": [
      "--python=3.13",
      "--directory", "/absolute/path/to/mcp_snowflake_server",
      "run", "mcp_snowflake_server"
      // Optional flags — see README Configuration Reference / .env.example
    ],
    "envFile": "/absolute/path/to/.env"
}
```

</details>

### Claude Desktop Local Setup

1. Install `uv`.
2. Prepare `.env` or a TOML connections file.
3. Test the server locally with `make run`.
4. Add a local server entry to `claude_desktop_config.json`.

<details>
<summary><strong>TOML configuration (recommended)</strong></summary>

```jsonc
"mcpServers": {
  "snowflake_local": {
    "command": "/absolute/path/to/uv",
    "args": [
      "--python=3.13",
      "--directory", "/absolute/path/to/mcp_snowflake_server",
      "run", "mcp_snowflake_server",
      "--connections-file", "/absolute/path/to/snowflake_connections.toml",
      "--connection-name", "development"
      // Optional flags — see README Configuration Reference
    ]
  }
}
```

</details>

<details>
<summary><strong>Environment variables</strong></summary>

```jsonc
"mcpServers": {
  "snowflake_local": {
    "command": "/absolute/path/to/uv",
    "args": [
      "--python=3.13",
      "--directory", "/absolute/path/to/mcp_snowflake_server",
      "run", "mcp_snowflake_server"
      // Optional flags — see README Configuration Reference
    ]
  }
}
```

</details>

## Docker from Source

This repository includes a `Dockerfile` for containerized contributor workflows.

> **Prerequisites:** The `Dockerfile` uses [Docker Hardened Images (DHI)](https://docs.docker.com/dhi/) as base images. You need registry access, so run `docker login dhi.io` first. If you do not have access, replace the `dhi.io/python` and `dhi.io/uv` base images with standard equivalents such as `python:3.13-slim` and `ghcr.io/astral-sh/uv:latest`.

```bash
# Build
docker build -t mcp-snowflake-server .

# Run with a .env file
# -i (--interactive) is required to keep stdin open for the MCP stdio transport
docker run --rm -i --env-file .env mcp-snowflake-server

# Or pass credentials individually as environment variables
docker run --rm -i \
  -e SNOWFLAKE_USER=user@example.com \
  -e SNOWFLAKE_ACCOUNT=myaccount \
  -e SNOWFLAKE_AUTHENTICATOR=snowflake \
  -e SNOWFLAKE_PASSWORD=secret \
  -e SNOWFLAKE_WAREHOUSE=COMPUTE_WH \
  -e SNOWFLAKE_DATABASE=MY_DB \
  -e SNOWFLAKE_SCHEMA=PUBLIC \
  -e SNOWFLAKE_ROLE=MYROLE \
  mcp-snowflake-server

# Or pass arguments directly
docker run --rm -i mcp-snowflake-server \
  --account your_account \
  --user your_user \
  --authenticator snowflake \
  --password your_password \
  --warehouse COMPUTE_WH \
  --database MY_DB \
  --schema PUBLIC \
  --role MYROLE

# Or use a TOML connections file
# Mount the file read-only; --connections-file path must match the mount target
docker run --rm -i \
  -v /path/to/snowflake_connections.toml:/app/snowflake_connections.toml:ro \
  mcp-snowflake-server \
  --connections-file /app/snowflake_connections.toml \
  --connection-name production
```

## Formatting, Linting, and Tests

Common contributor commands:

```bash
# Run all hooks across the repository
make hooks-run

# Check formatting with oxfmt (non-destructive)
make fmt-check

# Auto-format all files with oxfmt
make fmt

# Format Python + autofix lint issues with Ruff
make ruff

# Run tests
make test

# Run tests with terminal coverage report
make coverage

# Run tests and generate HTML coverage report
make coverage-html
```

Tooling notes:

- Python dev tooling includes `ruff`, `mypy`, `pytest`, `pytest-asyncio`, `pytest-cov`, and `prek`
- `oxfmt` is managed via `bun`
- hook configuration lives in `prek.toml`
- formatter configuration lives in `.oxfmtrc.json`

## Submitting Changes

When opening a pull request:

- Keep changes focused and scoped
- Run formatting, linting, and tests locally before pushing
- Use a PR title that follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format (for example: `feat: add OAuth token refresh`). PR titles are automatically validated by the `Lint PR` GitHub Actions workflow (`.github/workflows/lint_pr.yml`).
- Include context in the PR description, especially for config or behavior changes
- Link related issues when applicable
- Include screenshots or terminal output when changing user-facing docs or behavior

If you are unsure whether a change is in scope, open an issue or discussion first.

## How to Report Bugs and Request Features

Before opening a new issue, please:

- Search existing issues to avoid duplicates
- Confirm you're using the latest released version (or latest `main` when testing source changes)
- Include enough detail for maintainers to reproduce the behavior

For bug reports, include:

- Expected behavior
- Actual behavior
- Reproduction steps
- Environment details (OS, Python version, auth mode, and how the server is launched)
- Relevant logs or trace output (redact secrets)

For feature requests, include:

- The problem you are trying to solve
- A proposed solution or API shape (if you have one)
- Trade-offs or alternatives you considered

## Documentation and Coverage

- Full AI-generated documentation: [DeepWiki](https://deepwiki.com/nsphung/mcp-snowflake-server)
- Coverage report artifact: `htmlcov/index.html`
- Coverage sunburst: [Codecov graph](https://codecov.io/github/nsphung/mcp-snowflake-server/graphs/sunburst.svg?token=DSOJN7JOON)

<div align="center">

<a href="https://github.com/nsphung/mcp-snowflake-server"><img width="80%" height="80%" alt="mcp-snowflake-server-nsp-banner" src="https://github.com/user-attachments/assets/73ccb230-907e-4b4c-ae51-cbda9cdc8c2c" /></a>

[![PyPI](https://img.shields.io/pypi/v/mcp-snowflake-server-nsp)](https://pypi.org/project/mcp-snowflake-server-nsp/) • [![codecov](https://codecov.io/gh/nsphung/mcp-snowflake-server/graph/badge.svg?token=CODECOV_BADGE)](https://codecov.io/gh/nsphung/mcp-snowflake-server) • [![PyPI Downloads](https://img.shields.io/pypi/dm/mcp-snowflake-server-nsp.svg?label=PyPI%20downloads)](https://pypi.org/project/mcp-snowflake-server-nsp/) • [![Docker Pulls](https://img.shields.io/docker/pulls/nsphung/mcp-snowflake-server-nsp)](https://hub.docker.com/r/nsphung/mcp-snowflake-server-nsp) • [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

[![lint](https://github.com/nsphung/mcp-snowflake-server/actions/workflows/lint.yml/badge.svg)](https://github.com/nsphung/mcp-snowflake-server/actions/workflows/lint.yml)
[![test](https://github.com/nsphung/mcp-snowflake-server/actions/workflows/test.yml/badge.svg)](https://github.com/nsphung/mcp-snowflake-server/actions/workflows/test.yml)
[![Code of Conduct](https://img.shields.io/badge/Code%20of%20Conduct-Contributor%20Covenant%202.1-4baaaa.svg)](./CODE_OF_CONDUCT.md)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg?style=flat-square)](https://modelcontextprotocol.io/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![python-3.13+](https://img.shields.io/badge/Python-%3E%3D3.13-blue)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)
[![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek)
[![oxfmt](https://img.shields.io/badge/oxfmt-formatted-orange)](https://oxc.rs/docs/guide/usage/formatter)
[![CodeQL](https://github.com/nsphung/mcp-snowflake-server/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/nsphung/mcp-snowflake-server/actions/workflows/github-code-scanning/codeql)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/nsphung/mcp-snowflake-server/badge)](https://scorecard.dev/viewer/?uri=github.com/nsphung/mcp-snowflake-server)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/12747/badge)](https://www.bestpractices.dev/projects/12747)
![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/nsphung/mcp-snowflake-server?utm_source=oss&utm_medium=github&utm_campaign=nsphung%2Fmcp-snowflake-server&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)
[![Socket Badge](https://badge.socket.dev/pypi/package/mcp-snowflake-server-nsp/latest?artifact_id=tar-gz)](https://socket.dev/pypi/package/mcp-snowflake-server-nsp)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/nsphung/mcp-snowflake-server)

</div>

---

# Snowflake MCP Server NSP

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server / MCP server that connects AI assistants to Snowflake — enabling SQL queries, schema exploration, and data insights directly from your LLM client.

<!-- mcp-name: io.github.nsphung/mcp-snowflake-server -->

**Highlights:**

- Multiple authentication methods: password, key-pair, external browser, OAuth 2.0 (client credentials & bearer token), TOML connection files
- TOML multi-connection config — manage `production`, `staging`, and `development` environments in one file
- Write-safety guard — write operations are disabled by default and must be explicitly enabled
- Exclusion patterns — filter out databases, schemas, or tables from discovery
- `--exclude-json-results` flag — reduces LLM context window usage
- Selective tool exclusion via `--exclude_tools`
- Prefetch mode — pre-load table schema as MCP resources
- Docker support with hardened image ([DHI](https://docs.docker.com/dhi/), nonroot user, no shell in runtime)

---

## Table of Contents

- [Snowflake MCP Server NSP](#snowflake-mcp-server-nsp)
  - [Table of Contents](#table-of-contents)
  - [Quick Start](#quick-start)
    - [Claude Code](#claude-code)
    - [Visual Studio Code (VSCode)](#visual-studio-code-vscode)
    - [OpenCode](#opencode)
  - [Components](#components)
    - [Resources](#resources)
    - [Tools](#tools)
      - [Query Tools](#query-tools)
      - [Schema Tools](#schema-tools)
      - [Analysis Tools](#analysis-tools)
  - [Authentication](#authentication)
    - [Password](#password)
    - [Key-Pair](#key-pair)
    - [External Browser](#external-browser)
    - [OAuth 2.0 Client Credentials](#oauth-20-client-credentials)
    - [OAuth Bearer Token](#oauth-bearer-token)
    - [TOML Connection File (Recommended)](#toml-connection-file-recommended)
  - [Installation](#installation)
    - [Via UVX](#via-uvx)
    - [Via Docker Hub](#via-docker-hub)
  - [Configuration Reference](#configuration-reference)
  - [Exclusion Patterns](#exclusion-patterns)
  - [License](#license)
  - [Fork and Attribution](#fork-and-attribution)

---

## Quick Start

The fastest way to try it — using `uvx` with a TOML connection file:

```bash
# 1. Create a connections file
cat > ~/snowflake_connections.toml << 'EOF'
[myconn]
account = "your_account"
user = "your_user"
password = "your_password"
warehouse = "COMPUTE_WH"
database = "MY_DB"
schema = "PUBLIC"
role = "MYROLE"
EOF

# 2. Run the server
uvx --python=3.13 --from mcp-snowflake-server-nsp mcp_snowflake_server \
  --connections-file ~/snowflake_connections.toml \
  --connection-name myconn
```

### Claude Code

Add to your MCP client config (e.g. `claude_desktop_config.json`) using `snowflake_connections.toml`:

```jsonc
"mcpServers": {
  "snowflake": {
    "command": "uvx",
    "args": [
      "--python=3.13",
      "--from", "mcp-snowflake-server-nsp",
      "mcp_snowflake_server",
      "--connections-file", "/absolute/path/to/snowflake_connections.toml",
      "--connection-name", "myconn"
    ]
  }
}
```

### Visual Studio Code (VSCode)

**uvx** — [![Install in VS Code](https://img.shields.io/badge/VS%20Code-Install%20Server-0078d4?style=flat-square&logo=visualstudiocode)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522snowflake%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522--python%253D3.13%2522%252C%2522--from%2522%252C%2522mcp-snowflake-server-nsp%2522%252C%2522mcp_snowflake_server%2522%255D%257D) [![Install in VS Code Insiders](https://img.shields.io/badge/VS%20Code%20Insiders-Install%20Server-24bfa5?style=flat-square&logo=visualstudiocode)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522snowflake%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522--python%253D3.13%2522%252C%2522--from%2522%252C%2522mcp-snowflake-server-nsp%2522%252C%2522mcp_snowflake_server%2522%255D%257D)

**Docker** — [![Install in VS Code (Docker)](https://img.shields.io/badge/VS%20Code-Install%20Docker%20Server-0078d4?style=flat-square&logo=visualstudiocode)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522snowflake%2522%252C%2522command%2522%253A%2522docker%2522%252C%2522args%2522%253A%255B%2522run%2522%252C%2522--rm%2522%252C%2522-i%2522%252C%2522nsphung%252Fmcp-snowflake-server-nsp%2522%255D%257D) [![Install in VS Code Insiders (Docker)](https://img.shields.io/badge/VS%20Code%20Insiders-Install%20Docker%20Server-24bfa5?style=flat-square&logo=visualstudiocode)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522snowflake%2522%252C%2522command%2522%253A%2522docker%2522%252C%2522args%2522%253A%255B%2522run%2522%252C%2522--rm%2522%252C%2522-i%2522%252C%2522nsphung%252Fmcp-snowflake-server-nsp%2522%255D%257D)

Or add manually to your MCP client config (e.g. `.vscode/mcp.json`) using `.env` file (see [Authentication](#authentication)):

```jsonc
"snowflake": {
      // Snowflake MCP server
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from", "mcp-snowflake-server-nsp",
        "--python=3.13",
        "mcp_snowflake_server"
      ],
      "envFile": "${workspaceFolder}/.env"
    }
```

### OpenCode

Add to your MCP client config (e.g. `opencode.jsonc`) with `.env` file (see [Authentication](#authentication)):

```jsonc
"snowflake": {
  "type": "local",
  "command": [
    "uvx",
    "--from",
    "mcp-snowflake-server-nsp",
    "--python=3.13",
    "mcp_snowflake_server",
  ],
  "enabled": true,
  "timeout": 300000,
}
```

---

## Components

### Resources

| URI                            | Description                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------ |
| `memo://insights`              | A continuously updated memo aggregating data insights appended via `append_insight`. |
| `context://table/{table_name}` | _(Prefetch mode only)_ Per-table schema summaries including columns and comments.    |

---

### Tools

#### Query Tools

| Tool           | Description                                                                   | Requires        |
| -------------- | ----------------------------------------------------------------------------- | --------------- |
| `read_query`   | Execute `SELECT` queries. **Input:** `query` (string).                        | —               |
| `write_query`  | Execute `INSERT`, `UPDATE`, or `DELETE` queries. **Input:** `query` (string). | `--allow_write` |
| `create_table` | Execute `CREATE TABLE` statements. **Input:** `query` (string).               | `--allow_write` |

#### Schema Tools

| Tool             | Description                                                              | Input                                   |
| ---------------- | ------------------------------------------------------------------------ | --------------------------------------- |
| `list_databases` | List all databases in the Snowflake instance.                            | —                                       |
| `list_schemas`   | List all schemas within a database.                                      | `database` (string)                     |
| `list_tables`    | List all tables within a database and schema.                            | `database`, `schema` (strings)          |
| `describe_table` | Describe columns of a table (name, type, nullability, default, comment). | `table_name` as `database.schema.table` |

#### Analysis Tools

| Tool             | Description                                           | Input              |
| ---------------- | ----------------------------------------------------- | ------------------ |
| `append_insight` | Add a data insight to the `memo://insights` resource. | `insight` (string) |

---

## Authentication

### Password

Set credentials via environment variables or CLI flags (see [Configuration Reference](#configuration-reference)):

```bash
SNOWFLAKE_USER="user@example.com"
SNOWFLAKE_ACCOUNT="myaccount"
SNOWFLAKE_AUTHENTICATOR="snowflake"
SNOWFLAKE_PASSWORD="secret"
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="MY_DB"
SNOWFLAKE_SCHEMA="PUBLIC"
SNOWFLAKE_ROLE="MYROLE"
```

### Key-Pair

```bash
SNOWFLAKE_USER="user@example.com"
SNOWFLAKE_ACCOUNT="myaccount"
SNOWFLAKE_AUTHENTICATOR="snowflake_jwt"
SNOWFLAKE_PRIVATE_KEY_FILE="/absolute/path/to/key.p8"
SNOWFLAKE_PRIVATE_KEY_FILE_PWD="passphrase"  # Optional — only if key is encrypted
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="MY_DB"
SNOWFLAKE_SCHEMA="PUBLIC"
SNOWFLAKE_ROLE="MYROLE"
```

Or via CLI: `--private_key_file /path/to/key.p8 --private_key_file_pwd passphrase`

### External Browser

```bash
SNOWFLAKE_AUTHENTICATOR="externalbrowser"
```

Or in a TOML connection entry: `authenticator = "externalbrowser"`

### OAuth 2.0 Client Credentials

Use the [OAuth 2.0 client credentials flow](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#using-oauth) to authenticate with a client ID and secret (no user interaction required):

```bash
SNOWFLAKE_AUTHENTICATOR="oauth_client_credentials"
SNOWFLAKE_ACCOUNT="myaccount"
SNOWFLAKE_OAUTH_CLIENT_ID="your_client_id"
SNOWFLAKE_OAUTH_CLIENT_SECRET="your_client_secret"
SNOWFLAKE_OAUTH_TOKEN_REQUEST_URL="https://your-idp.example.com/oauth/token"
SNOWFLAKE_OAUTH_SCOPE="session:role:MY_ROLE"  # Optional
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="MY_DB"
SNOWFLAKE_SCHEMA="PUBLIC"
SNOWFLAKE_ROLE="MYROLE"
```

### OAuth Bearer Token

Use a pre-fetched OAuth bearer token:

```bash
SNOWFLAKE_AUTHENTICATOR="oauth"
SNOWFLAKE_ACCOUNT="myaccount"
SNOWFLAKE_TOKEN="eyJhbGciOiJSUzI1NiJ9..."
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="MY_DB"
SNOWFLAKE_SCHEMA="PUBLIC"
SNOWFLAKE_ROLE="MYROLE"
```

### TOML Connection File (Recommended)

Manage multiple environments in a single file. See [`example_connections.toml`](https://github.com/nsphung/mcp-snowflake-server/blob/main/example_connections.toml) for a full template.

```toml
[production]
account = "your_account"
user = "your_user"
password = "your_password"
authenticator = "snowflake"
warehouse = "COMPUTE_WH"
database = "PROD_DB"
schema = "PUBLIC"
role = "ACCOUNTADMIN"

[development]
account = "your_account"
user = "dev_user"
authenticator = "externalbrowser"
warehouse = "DEV_WH"
database = "DEV_DB"
schema = "PUBLIC"
role = "DEVELOPER"

[reporting]
account = "your_account"
user = "reporting_user"
authenticator = "snowflake_jwt"
private_key_file = "/path/to/private_key.pem"
private_key_file_pwd = "passphrase"  # Optional
warehouse = "REPORTING_WH"
database = "REPORTING_DB"
schema = "REPORTS"
role = "REPORTING_ROLE"

[analytics_oauth]
account = "your_account"
authenticator = "oauth_client_credentials"
oauth_client_id = "your_client_id"
oauth_client_secret = "your_client_secret"
oauth_token_request_url = "https://your-idp.example.com/oauth/token"
oauth_scope = "session:role:ANALYTICS_ROLE"  # Optional
warehouse = "ANALYTICS_WH"
database = "ANALYTICS_DB"
schema = "PUBLIC"
role = "ANALYTICS_ROLE"
```

Pass the file with `--connections-file` and select a profile with `--connection-name`. Both flags are required together.

---

## Installation

The package is published on [PyPI as `mcp-snowflake-server-nsp`](https://pypi.org/project/mcp-snowflake-server-nsp/).

> **Contributing or running from source?** See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for local development setup, test commands, formatting, and building the Docker image from source.

---

### Via UVX

<details>
<summary><strong>TOML configuration (recommended)</strong></summary>

```jsonc
"mcpServers": {
  "snowflake_production": {
    "command": "uvx",
    "args": [
      "--python=3.13",
      "--from", "mcp-snowflake-server-nsp",
      "mcp_snowflake_server",
      "--connections-file", "/path/to/snowflake_connections.toml",
      "--connection-name", "production"
      // Optional flags — see Configuration Reference
    ]
  },
  "snowflake_staging": {
    "command": "uvx",
    "args": [
      "--python=3.13",
      "--from", "mcp-snowflake-server-nsp",
      "mcp_snowflake_server",
      "--connections-file", "/path/to/snowflake_connections.toml",
      "--connection-name", "staging"
    ]
  }
}
```

</details>

<details>
<summary><strong>Individual parameters</strong></summary>

```jsonc
"mcpServers": {
  "snowflake": {
    "command": "uvx",
    "args": [
      "--python=3.13",
      "--from", "mcp-snowflake-server-nsp",
      "mcp_snowflake_server",
      "--account", "your_account",
      "--warehouse", "your_warehouse",
      "--user", "your_user",
      "--password", "your_password",
      "--role", "your_role",
      "--database", "your_database",
      "--schema", "your_schema"
      // Optional: "--private_key_file", "/absolute/path/key.p8"
      // Optional: "--private_key_file_pwd", "passphrase"
      // Optional flags — see Configuration Reference
    ]
  }
}
```

</details>

---

### Via Docker Hub

The image is published on [Docker Hub](https://hub.docker.com/r/nsphung/mcp-snowflake-server-nsp) — no build step required:

```bash
docker pull nsphung/mcp-snowflake-server-nsp
```

> **Note:** `-i` (`--interactive`) is required to keep stdin open for the MCP stdio transport. Do **not** use `-d` (detach).

<details>
<summary><strong>Claude Desktop — <code>claude_desktop_config.json</code></strong></summary>

With `.env` file (see [Authentication](#authentication)):

```jsonc
"mcpServers": {
  "snowflake": {
    "command": "docker",
    "args": [
      "run", "--rm", "-i",
      "--env-file", "/absolute/path/to/.env",
      "nsphung/mcp-snowflake-server-nsp"
    ]
  }
}
```

With TOML connections file:

```jsonc
"mcpServers": {
  "snowflake": {
    "command": "docker",
    "args": [
      "run", "--rm", "-i",
      "-v", "/path/to/snowflake_connections.toml:/app/snowflake_connections.toml:ro",
      "nsphung/mcp-snowflake-server-nsp",
      "--connections-file", "/app/snowflake_connections.toml",
      "--connection-name", "production"
    ]
  }
}
```

</details>

<details>
<summary><strong>VS Code — <code>.vscode/mcp.json</code></strong></summary>

With `.env` file:

```jsonc
"snowflake": {
  "type": "stdio",
  "command": "docker",
  "args": [
    "run", "--rm", "-i",
    "nsphung/mcp-snowflake-server-nsp"
  ],
  "envFile": "${workspaceFolder}/.env"
}
```

With TOML connections file:

```jsonc
"snowflake": {
  "type": "stdio",
  "command": "docker",
  "args": [
    "run", "--rm", "-i",
    "-v", "/path/to/snowflake_connections.toml:/app/snowflake_connections.toml:ro",
    "nsphung/mcp-snowflake-server-nsp",
    "--connections-file", "/app/snowflake_connections.toml",
    "--connection-name", "production"
  ]
}
```

</details>

<details>
<summary><strong>OpenCode — <code>opencode.jsonc</code></strong></summary>

```jsonc
"snowflake": {
  "type": "local",
  "command": [
    "docker", "run", "--rm", "-i",
    "--env-file", "/absolute/path/to/.env",
    "nsphung/mcp-snowflake-server-nsp"
  ],
  "enabled": true,
  "timeout": 300000
}
```

</details>

---

## Configuration Reference

All connection parameters can also be set as environment variables (`SNOWFLAKE_<PARAM_UPPER>`).

| Flag                           | Env var                          | Default      | Description                                                                                        |
| ------------------------------ | -------------------------------- | ------------ | -------------------------------------------------------------------------------------------------- |
| `--account`                    | `SNOWFLAKE_ACCOUNT`              | —            | Snowflake account identifier                                                                       |
| `--user`                       | `SNOWFLAKE_USER`                 | —            | Snowflake username                                                                                 |
| `--password`                   | `SNOWFLAKE_PASSWORD`             | —            | Password (not required for key-pair / SSO)                                                         |
| `--warehouse`                  | `SNOWFLAKE_WAREHOUSE`            | —            | Virtual warehouse to use                                                                           |
| `--database`                   | `SNOWFLAKE_DATABASE`             | _(required)_ | Default database                                                                                   |
| `--schema`                     | `SNOWFLAKE_SCHEMA`               | _(required)_ | Default schema                                                                                     |
| `--role`                       | `SNOWFLAKE_ROLE`                 | —            | Role to assume                                                                                     |
| `--private_key_file`           | `SNOWFLAKE_PRIVATE_KEY_FILE`     | —            | Absolute path to `.p8` private key file                                                            |
| `--private_key_file_pwd`       | `SNOWFLAKE_PRIVATE_KEY_FILE_PWD` | —            | Passphrase for encrypted private key                                                               |
| `--connections-file`           | —                                | —            | Path to TOML connections file                                                                      |
| `--connection-name`            | —                                | —            | Connection profile name in TOML file (required with `--connections-file`)                          |
| `--allow_write`                | —                                | `false`      | Enable `write_query` and `create_table` tools                                                      |
| `--prefetch` / `--no-prefetch` | —                                | `false`      | Pre-load table schema as `context://table/*` resources (disables `list_tables` / `describe_table`) |
| `--exclude_tools`              | —                                | `[]`         | Space-separated list of tool names to disable                                                      |
| `--exclude-json-results`       | —                                | `false`      | Omit embedded JSON resources from responses (reduces context window usage)                         |
| `--log_dir`                    | —                                | —            | Directory for log file output                                                                      |
| `--log_level`                  | —                                | `INFO`       | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`                                     |

---

## Exclusion Patterns

Edit [`runtime_config.json`](https://github.com/nsphung/mcp-snowflake-server/blob/main/runtime_config.json) to exclude databases, schemas, or tables from all discovery tools. Patterns are matched case-insensitively as substrings.

```json
{
  "exclude_patterns": {
    "databases": ["temp"],
    "schemas": ["temp", "information_schema"],
    "tables": ["temp"]
  }
}
```

The server loads this file automatically at startup from the working directory.

---

## License

This project is licensed under the **MIT License**. See the [`LICENSE`](https://github.com/nsphung/mcp-snowflake-server/blob/main/LICENSE) file for the full text.

---

## Fork and Attribution

This repository is a fork of [`isaacwasserman/mcp-snowflake-server`](https://github.com/isaacwasserman/mcp-snowflake-server).

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/isaacwasserman-mcp-snowflake-server-badge.png)](https://mseep.ai/app/isaacwasserman-mcp-snowflake-server)

- Upstream authors and contributors retain copyright for their contributions.
- Fork-specific changes are maintained by `nsphung`.
- A summary of notable modifications is tracked in [`NOTICE`](https://github.com/nsphung/mcp-snowflake-server/blob/main/NOTICE).

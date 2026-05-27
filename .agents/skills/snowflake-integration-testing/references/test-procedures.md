# Integration Test Procedures

## Pre-requisites

- MCP Snowflake server running (local via `uv run` or Docker)
- Valid `.env` file with Snowflake credentials
- At least one of the MCP server entries enabled in `.vscode/mcp.json`

## Test Scenarios

### Scenario 1: Basic Connectivity

**Goal**: Confirm the MCP server starts and authenticates to Snowflake.

**Steps**:

1. Use `read_query` with: `SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()`
2. Verify all fields return non-null values
3. Confirm the role matches expected permissions

**Expected**: Response contains user identity, role, warehouse, database, and schema.

### Scenario 2: Database Discovery

**Goal**: Verify `list_databases` returns the expected set of databases.

**Steps**:

1. Call `list_databases` (no parameters)
2. Verify the response contains `DATABASE_NAME` entries
3. Check that exclusion patterns (if configured) are applied

**Expected**: A list of databases accessible to the configured role.

### Scenario 3: Schema & Table Navigation

**Goal**: Verify hierarchical navigation (database → schema → table).

**Steps**:

1. Call `list_schemas` with a known database
2. Call `list_tables` with database + schema from step 1
3. Call `describe_table` with a fully-qualified table name

**Expected**: Each level returns valid metadata without errors.

### Scenario 4: Read Query Execution

**Goal**: Verify SQL queries execute and return structured data.

**Steps**:

1. Execute a simple query: `SELECT 1 AS test_col`
2. Execute a query against a known table with LIMIT
3. Verify data is returned in YAML format (and optionally JSON resource)

**Expected**: Structured response with `type: data`, `data_id`, and `data` array.

### Scenario 5: Write Detection Guard

**Goal**: Confirm write operations are blocked via `read_query`.

**Steps**:

1. Attempt: `INSERT INTO test VALUES (1)` via `read_query`
2. Attempt: `DROP TABLE test` via `read_query`
3. Attempt: `UPDATE test SET x = 1` via `read_query`

**Expected**: All attempts return an error: "Calls to read_query should not contain write operations".

### Scenario 6: Complex Data Types

**Goal**: Discover and sample tables with VARIANT/OBJECT/ARRAY columns.

**Steps**:

1. Query `information_schema.columns` filtering `data_type IN ('VARIANT', 'OBJECT', 'ARRAY')`
2. Pick a table with an OBJECT column
3. Sample rows where the OBJECT column IS NOT NULL
4. Verify the JSON structure is readable

**Expected**: Nested JSON objects are returned as serialized strings with valid structure.

### Scenario 7: Docker Deployment

**Goal**: Verify the Docker image works identically to local.

**Steps**:

1. Build: `docker build -t mcp-snowflake-server-nsp:test .`
2. Enable the Docker MCP server entry in `.vscode/mcp.json`
3. Disable the local MCP server entry
4. Re-run Scenarios 1-4

**Expected**: Same results as local execution.

## Troubleshooting

| Symptom                              | Likely Cause                           | Fix                                            |
| ------------------------------------ | -------------------------------------- | ---------------------------------------------- |
| "Process exited with code 125"       | Docker container failed to start       | Check `docker logs`, verify `.env` file path   |
| "Missing required parameter"         | Tool called without arguments          | Ensure database/schema/table params are passed |
| Timeout on `list_databases`          | Network or auth issue                  | Verify Snowflake account, check firewall       |
| Empty results                        | Exclusion patterns too broad           | Review `runtime_config.json` exclusions        |
| "Table name must be fully qualified" | Missing `database.schema.table` format | Use 3-part naming                              |

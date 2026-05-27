---
name: snowflake-integration-testing
description: 'Integration testing workflow for mcp-snowflake-server. Use when verifying MCP tool connectivity, exploring Snowflake schemas, discovering tables with specific column types (VARIANT, OBJECT, ARRAY, nested JSON), and sampling data. Trigger phrases: "integration test", "test snowflake connection", "explore snowflake", "verify MCP tools", "test data types".'
---

# Snowflake Integration Testing

## When to Use

- Verifying MCP Snowflake server connectivity after configuration changes
- Testing that MCP tools (`list_databases`, `list_schemas`, `list_tables`, `describe_table`, `read_query`) work correctly
- Exploring Snowflake schemas to validate data access permissions
- Discovering tables with specific column data types (VARIANT, OBJECT, ARRAY)
- Sampling rows to verify data shape, nested JSON structure, and content
- Validating Docker or local MCP server deployments

## Available MCP Tools

| Tool             | Purpose                                         |
| ---------------- | ----------------------------------------------- |
| `list_databases` | List all accessible databases                   |
| `list_schemas`   | List schemas in a database                      |
| `list_tables`    | List tables in a database.schema                |
| `describe_table` | Get column metadata for a fully-qualified table |
| `read_query`     | Execute a read-only SQL query                   |

## Procedure

### 1. Connectivity Check

Verify the connection is active and inspect the session context:

```sql
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()
```

Use `read_query` to execute this. Confirm user, role, warehouse, database, and schema are as expected.

### 2. Schema Exploration

Follow this sequence to explore the data landscape:

1. Call `list_databases` — note accessible databases
2. Pick a target database, call `list_schemas` with `database` parameter
3. Pick a target schema, call `list_tables` with `database` and `schema` parameters
4. For specific tables, call `describe_table` with fully-qualified name (`database.schema.table`)

### 3. Data Type Discovery

Find tables with specific column types using `read_query`:

```sql
-- Find OBJECT columns (nested JSON)
SELECT table_schema, table_name, column_name, data_type
FROM <DATABASE>.information_schema.columns
WHERE data_type = 'OBJECT'
LIMIT 20

-- Find VARIANT columns
SELECT table_schema, table_name, column_name, data_type
FROM <DATABASE>.information_schema.columns
WHERE data_type = 'VARIANT'
LIMIT 20

-- Find ARRAY columns
SELECT table_schema, table_name, column_name, data_type
FROM <DATABASE>.information_schema.columns
WHERE data_type = 'ARRAY'
LIMIT 20
```

### 4. Data Sampling

Sample rows from discovered tables to verify data shape:

```sql
SELECT * FROM <DATABASE>.<SCHEMA>.<TABLE> LIMIT 10
```

For tables with JSON columns, verify nested structure:

```sql
SELECT * FROM <DATABASE>.<SCHEMA>.<TABLE>
WHERE <JSON_COLUMN> IS NOT NULL
LIMIT 10
```

### 5. Validation Checklist

- [ ] Connection successful (user/role/warehouse confirmed)
- [ ] Databases listed without errors
- [ ] Schemas discoverable within target database
- [ ] Tables listed with metadata (name, comment)
- [ ] Column descriptions returned for `describe_table`
- [ ] Read queries execute and return data
- [ ] VARIANT/OBJECT/ARRAY columns discoverable
- [ ] Nested JSON data readable and properly formatted

## Reference

- [Detailed test procedures](./references/test-procedures.md)
- [Sample SQL queries](./scripts/sample-queries.sql)

## Notes

- All queries are **read-only** — write operations are blocked by default
- The MCP server enforces SQL write detection; only SELECT/SHOW/DESCRIBE are allowed via `read_query`
- Exclusion patterns may filter databases/schemas/tables from discovery results
- Use `--exclude-json-results` flag awareness: JSON resource attachments may be omitted

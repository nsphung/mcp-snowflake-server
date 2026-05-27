-- =============================================================================
-- Snowflake Integration Testing: Sample Queries
-- =============================================================================
-- Use these with the `read_query` MCP tool to validate connectivity and data.
-- Replace <DATABASE>, <SCHEMA>, <TABLE> with actual identifiers.
-- =============================================================================

-- ─── 1. Session Identity ─────────────────────────────────────────────────────
SELECT
    CURRENT_USER() AS current_user,
    CURRENT_ROLE() AS current_role,
    CURRENT_WAREHOUSE() AS current_warehouse,
    CURRENT_DATABASE() AS current_database,
    CURRENT_SCHEMA() AS current_schema;

-- ─── 2. List Databases (alternative to list_databases tool) ──────────────────
SELECT DATABASE_NAME
FROM INFORMATION_SCHEMA.DATABASES
ORDER BY DATABASE_NAME;

-- ─── 3. List Schemas in a Database ──────────────────────────────────────────
SELECT SCHEMA_NAME
FROM <DATABASE>.INFORMATION_SCHEMA.SCHEMATA
ORDER BY SCHEMA_NAME;

-- ─── 4. List Tables in a Schema ─────────────────────────────────────────────
SELECT table_catalog, table_schema, table_name, comment
FROM <DATABASE>.information_schema.tables
WHERE table_schema = '<SCHEMA>'
ORDER BY table_name;

-- ─── 5. Describe Table Columns ──────────────────────────────────────────────
SELECT column_name, column_default, is_nullable, data_type, comment
FROM <DATABASE>.information_schema.columns
WHERE table_schema = '<SCHEMA>' AND table_name = '<TABLE>'
ORDER BY ordinal_position;

-- ─── 6. Find OBJECT Columns (Nested JSON) ───────────────────────────────────
SELECT table_schema, table_name, column_name, data_type
FROM <DATABASE>.information_schema.columns
WHERE data_type = 'OBJECT'
LIMIT 20;

-- ─── 7. Find VARIANT Columns ────────────────────────────────────────────────
SELECT table_schema, table_name, column_name, data_type
FROM <DATABASE>.information_schema.columns
WHERE data_type = 'VARIANT'
LIMIT 20;

-- ─── 8. Find ARRAY Columns ──────────────────────────────────────────────────
SELECT table_schema, table_name, column_name, data_type
FROM <DATABASE>.information_schema.columns
WHERE data_type = 'ARRAY'
LIMIT 20;

-- ─── 9. Find All Semi-Structured Columns ────────────────────────────────────
SELECT table_schema, table_name, column_name, data_type
FROM <DATABASE>.information_schema.columns
WHERE data_type IN ('VARIANT', 'OBJECT', 'ARRAY')
ORDER BY table_schema, table_name, column_name
LIMIT 50;

-- ─── 10. Sample Rows (generic) ──────────────────────────────────────────────
SELECT *
FROM <DATABASE>.<SCHEMA>.<TABLE>
LIMIT 10;

-- ─── 11. Sample Rows with Non-Null JSON Column ──────────────────────────────
SELECT *
FROM <DATABASE>.<SCHEMA>.<TABLE>
WHERE <JSON_COLUMN> IS NOT NULL
LIMIT 10;

-- ─── 12. Parse Nested JSON Keys (OBJECT column) ─────────────────────────────
SELECT
    <JSON_COLUMN>,
    TYPEOF(<JSON_COLUMN>) AS json_type,
    OBJECT_KEYS(<JSON_COLUMN>) AS top_level_keys
FROM <DATABASE>.<SCHEMA>.<TABLE>
WHERE <JSON_COLUMN> IS NOT NULL
LIMIT 5;

-- ─── 13. Simple Health Check ─────────────────────────────────────────────────
SELECT 1 AS health_check;

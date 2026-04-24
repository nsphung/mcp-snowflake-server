import pathlib
from unittest.mock import MagicMock

import pytest
from mcp import types
from pydantic import AnyUrl

from mcp_snowflake_server.db_client import SnowflakeDB
from mcp_snowflake_server.server import (
    _build_exclusion_config,
    _resolve_resource,
    handle_create_table,
    handle_describe_table,
    handle_list_databases,
    handle_list_schemas,
    handle_list_tables,
    handle_read_query,
    handle_tool_errors,
    handle_write_query,
)
from mcp_snowflake_server.write_detector import SQLWriteDetector


# ── handle_tool_errors decorator ──────────────────────────────────────────────


async def test_handle_tool_errors_passes_through() -> None:
    @handle_tool_errors
    async def ok_func(x: str) -> list[types.TextContent]:
        return [types.TextContent(type="text", text=x)]

    result = await ok_func("hello")
    assert result[0].text == "hello"


async def test_handle_tool_errors_catches_exception() -> None:
    @handle_tool_errors
    async def bad_func() -> list[types.TextContent]:
        raise RuntimeError("boom")

    result = await bad_func()
    assert len(result) == 1
    assert "Error:" in result[0].text
    assert "boom" in result[0].text


# ── handle_list_databases ─────────────────────────────────────────────────────


async def test_list_databases_basic(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["INFORMATION_SCHEMA.DATABASES"] = lambda s: s.create_dataframe(
        [["DB1"], ["DB2"]], schema=["DATABASE_NAME"]
    )
    results = await handle_list_databases(None, fake_db)
    assert any(isinstance(r, types.TextContent) for r in results)
    assert any(isinstance(r, types.EmbeddedResource) for r in results)
    text = next(r for r in results if isinstance(r, types.TextContent)).text
    assert "DB1" in text


async def test_list_databases_exclusion(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["INFORMATION_SCHEMA.DATABASES"] = lambda s: s.create_dataframe(
        [["MYDB"], ["TESTDB"]], schema=["DATABASE_NAME"]
    )
    results = await handle_list_databases(
        None, fake_db, exclusion_config={"databases": ["test"], "schemas": [], "tables": []}
    )
    text = next(r for r in results if isinstance(r, types.TextContent)).text
    assert "MYDB" in text
    assert "TESTDB" not in text


async def test_list_databases_exclude_json(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["INFORMATION_SCHEMA.DATABASES"] = lambda s: s.create_dataframe(
        [["DB1"]], schema=["DATABASE_NAME"]
    )
    results = await handle_list_databases(None, fake_db, exclude_json_results=True)
    assert not any(isinstance(r, types.EmbeddedResource) for r in results)


# ── handle_list_schemas ───────────────────────────────────────────────────────


async def test_list_schemas_missing_database_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Missing required 'database'"):
        await handle_list_schemas(None, db)


async def test_list_schemas_invalid_identifier_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Invalid Snowflake identifier"):
        await handle_list_schemas({"database": "a;DROP"}, db)


async def test_list_schemas_basic(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["INFORMATION_SCHEMA.SCHEMATA"] = lambda s: s.create_dataframe(
        [["PUBLIC"], ["PRIVATE"]], schema=["SCHEMA_NAME"]
    )
    results = await handle_list_schemas({"database": "mydb"}, fake_db)
    text = next(r for r in results if isinstance(r, types.TextContent)).text
    assert "PUBLIC" in text


# ── handle_list_tables ────────────────────────────────────────────────────────


async def test_list_tables_missing_params_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Missing required"):
        await handle_list_tables({"database": "mydb"}, db)


async def test_list_tables_invalid_schema_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Invalid Snowflake identifier"):
        await handle_list_tables({"database": "mydb", "schema": "bad-schema"}, db)


async def test_list_tables_basic(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["information_schema.tables"] = lambda s: s.create_dataframe(
        [["MYDB", "PUBLIC", "ORDERS", "comment"]],
        schema=["TABLE_CATALOG", "TABLE_SCHEMA", "TABLE_NAME", "COMMENT"],
    )
    results = await handle_list_tables({"database": "mydb", "schema": "public"}, fake_db)
    text = next(r for r in results if isinstance(r, types.TextContent)).text
    assert "ORDERS" in text


# ── handle_describe_table ─────────────────────────────────────────────────────


async def test_describe_table_missing_arg_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Missing table_name"):
        await handle_describe_table(None, db)


async def test_describe_table_not_fully_qualified_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="fully qualified"):
        await handle_describe_table({"table_name": "schema.table"}, db)


async def test_describe_table_invalid_identifier_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Invalid Snowflake identifier"):
        await handle_describe_table({"table_name": "db.schema.bad-table"}, db)


async def test_describe_table_basic(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["information_schema.columns"] = lambda s: s.create_dataframe(
        [["ID", None, "NO", "NUMBER", "pk"]],
        schema=["COLUMN_NAME", "COLUMN_DEFAULT", "IS_NULLABLE", "DATA_TYPE", "COMMENT"],
    )
    results = await handle_describe_table({"table_name": "mydb.public.orders"}, fake_db)
    text = next(r for r in results if isinstance(r, types.TextContent)).text
    assert "ID" in text


# ── handle_read_query ─────────────────────────────────────────────────────────


async def test_read_query_blocks_write() -> None:
    db = MagicMock(spec=SnowflakeDB)
    detector = SQLWriteDetector()
    with pytest.raises(ValueError, match="write operations"):
        await handle_read_query({"query": "INSERT INTO foo VALUES (1)"}, db, detector)


async def test_read_query_missing_arg_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    detector = SQLWriteDetector()
    with pytest.raises(ValueError, match="Missing query"):
        await handle_read_query(None, db, detector)


async def test_read_query_basic(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["SELECT 1"] = lambda s: s.create_dataframe([[1]], schema=["V"])
    detector = SQLWriteDetector()
    results = await handle_read_query({"query": "SELECT 1"}, fake_db, detector)
    assert any(isinstance(r, types.TextContent) for r in results)


# ── handle_write_query ────────────────────────────────────────────────────────


async def test_write_query_not_allowed_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="not allowed"):
        await handle_write_query({"query": "INSERT INTO foo VALUES (1)"}, db, None, False, None)


async def test_write_query_select_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="SELECT queries are not allowed"):
        await handle_write_query({"query": "SELECT 1"}, db, None, True, None)


async def test_write_query_missing_arg_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Missing query"):
        await handle_write_query(None, db, None, True, None)


async def test_write_query_executes(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["INSERT"] = lambda s: s.create_dataframe([[1]], schema=["N"])
    results = await handle_write_query(
        {"query": "INSERT INTO foo VALUES (1)"}, fake_db, None, True, None
    )
    assert any(isinstance(r, types.TextContent) for r in results)


# ── handle_create_table ───────────────────────────────────────────────────────


async def test_create_table_not_allowed_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="not allowed"):
        await handle_create_table({"query": "CREATE TABLE t (id INT)"}, db, None, False, None)


async def test_create_table_wrong_statement_raises() -> None:
    db = MagicMock(spec=SnowflakeDB)
    with pytest.raises(ValueError, match="Only CREATE TABLE"):
        await handle_create_table({"query": "DROP TABLE t"}, db, None, True, None)


async def test_create_table_executes(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["CREATE TABLE"] = lambda s: s.create_dataframe([[1]], schema=["N"])
    results = await handle_create_table(
        {"query": "CREATE TABLE t (id INT)"}, fake_db, None, True, None
    )
    assert "Table created successfully" in results[0].text


# ── _build_exclusion_config ───────────────────────────────────────────────────


def test_build_exclusion_config_no_file_no_patterns() -> None:
    result = _build_exclusion_config(None, None)
    assert result == {"databases": [], "schemas": [], "tables": []}


def test_build_exclusion_config_with_patterns() -> None:
    result = _build_exclusion_config(None, {"databases": ["test"], "schemas": []})
    assert "test" in result["databases"]
    assert result["schemas"] == []
    assert result["tables"] == []


def test_build_exclusion_config_missing_file(tmp_path: pathlib.Path) -> None:
    result = _build_exclusion_config(str(tmp_path / "nonexistent.json"), None)
    assert result == {"databases": [], "schemas": [], "tables": []}


def test_build_exclusion_config_valid_file(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"exclude_patterns": {"databases": ["prod"], "schemas": [], "tables": []}}'
    )
    result = _build_exclusion_config(str(config_file), {"databases": ["dev"]})
    assert "prod" in result["databases"]
    assert "dev" in result["databases"]


# ── _resolve_resource ─────────────────────────────────────────────────────────


def test_resolve_resource_memo() -> None:
    db = SnowflakeDB({})
    db.add_insight("hello")
    result = _resolve_resource(AnyUrl("memo://insights"), db, {})
    assert "hello" in result


def test_resolve_resource_table() -> None:
    db = SnowflakeDB({})
    tables_info: dict[str, object] = {"ORDERS": {"TABLE_NAME": "ORDERS", "COLUMNS": {}}}
    result = _resolve_resource(AnyUrl("context://table/ORDERS"), db, tables_info)
    assert "ORDERS" in result


def test_resolve_resource_unknown_table_raises() -> None:
    db = SnowflakeDB({})
    with pytest.raises(ValueError, match="Unknown table"):
        _resolve_resource(AnyUrl("context://table/MISSING"), db, {})


def test_resolve_resource_unknown_uri_raises() -> None:
    db = SnowflakeDB({})
    with pytest.raises(ValueError, match="Unknown resource"):
        _resolve_resource(AnyUrl("unknown://foo"), db, {})

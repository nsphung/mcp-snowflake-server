import importlib.metadata
import pathlib
import tomllib
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp import types
from pydantic import AnyUrl

from mcp_snowflake_server.db_client import SnowflakeDB
from mcp_snowflake_server.server import (
    Tool,
    _build_exclusion_config,
    _dispatch_tool_call,
    _load_exclusion_from_file,
    _register_handlers,
    _resolve_resource,
    handle_append_insight,
    handle_create_table,
    handle_describe_table,
    handle_list_databases,
    handle_list_schemas,
    handle_list_tables,
    handle_read_query,
    handle_tool_errors,
    handle_write_query,
    main as server_main,
    prefetch_tables,
)
from mcp_snowflake_server.write_detector import SQLWriteDetector


type _Response = types.TextContent | types.ImageContent | types.EmbeddedResource


def _text(content: _Response) -> str:
    assert isinstance(content, types.TextContent)
    return str(content.text)


# ── handle_tool_errors decorator ──────────────────────────────────────────────


async def test_handle_tool_errors_passes_through() -> None:
    @handle_tool_errors
    async def ok_func(x: str) -> list[_Response]:
        return [types.TextContent(type="text", text=x)]

    result = await ok_func("hello")
    assert _text(result[0]) == "hello"


async def test_handle_tool_errors_catches_exception() -> None:
    @handle_tool_errors
    async def bad_func() -> list[_Response]:
        raise RuntimeError("boom")

    result = await bad_func()
    assert len(result) == 1
    assert "Error:" in _text(result[0])
    assert "boom" in _text(result[0])


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


async def test_list_schemas_exclusion(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["INFORMATION_SCHEMA.SCHEMATA"] = lambda s: s.create_dataframe(
        [["PUBLIC"], ["PRIVATE"]], schema=["SCHEMA_NAME"]
    )
    results = await handle_list_schemas(
        {"database": "mydb"},
        fake_db,
        exclusion_config={"databases": [], "schemas": ["priv"], "tables": []},
    )
    text = next(r for r in results if isinstance(r, types.TextContent)).text
    assert "PUBLIC" in text
    assert "PRIVATE" not in text


async def test_list_schemas_exclude_json(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["INFORMATION_SCHEMA.SCHEMATA"] = lambda s: s.create_dataframe(
        [["PUBLIC"]], schema=["SCHEMA_NAME"]
    )
    results = await handle_list_schemas({"database": "mydb"}, fake_db, exclude_json_results=True)
    assert not any(isinstance(r, types.EmbeddedResource) for r in results)


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


async def test_list_tables_exclusion(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["information_schema.tables"] = lambda s: s.create_dataframe(
        [["MYDB", "PUBLIC", "ORDERS", "ok"], ["MYDB", "PUBLIC", "TMP_TABLE", "tmp"]],
        schema=["TABLE_CATALOG", "TABLE_SCHEMA", "TABLE_NAME", "COMMENT"],
    )
    results = await handle_list_tables(
        {"database": "mydb", "schema": "public"},
        fake_db,
        exclusion_config={"databases": [], "schemas": [], "tables": ["tmp"]},
    )
    text = next(r for r in results if isinstance(r, types.TextContent)).text
    assert "ORDERS" in text
    assert "TMP_TABLE" not in text


async def test_list_tables_exclude_json(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["information_schema.tables"] = lambda s: s.create_dataframe(
        [["MYDB", "PUBLIC", "ORDERS", "comment"]],
        schema=["TABLE_CATALOG", "TABLE_SCHEMA", "TABLE_NAME", "COMMENT"],
    )
    results = await handle_list_tables(
        {"database": "mydb", "schema": "public"}, fake_db, exclude_json_results=True
    )
    assert not any(isinstance(r, types.EmbeddedResource) for r in results)


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


async def test_describe_table_exclude_json(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["information_schema.columns"] = lambda s: s.create_dataframe(
        [["ID", None, "NO", "NUMBER", "pk"]],
        schema=["COLUMN_NAME", "COLUMN_DEFAULT", "IS_NULLABLE", "DATA_TYPE", "COMMENT"],
    )
    results = await handle_describe_table(
        {"table_name": "mydb.public.orders"}, fake_db, exclude_json_results=True
    )
    assert not any(isinstance(r, types.EmbeddedResource) for r in results)


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


async def test_read_query_exclude_json(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["SELECT 1"] = lambda s: s.create_dataframe([[1]], schema=["V"])
    detector = SQLWriteDetector()
    results = await handle_read_query(
        {"query": "SELECT 1"}, fake_db, detector, exclude_json_results=True
    )
    assert not any(isinstance(r, types.EmbeddedResource) for r in results)


# ── handle_append_insight ─────────────────────────────────────────────────────


async def test_append_insight_missing_arg_raises() -> None:
    db = SnowflakeDB({})
    mock_server = MagicMock()
    with pytest.raises(ValueError, match="Missing insight"):
        await handle_append_insight(None, db, None, None, mock_server)


async def test_append_insight_updates_resource() -> None:
    db = SnowflakeDB({})
    mock_server = MagicMock()
    mock_server.request_context.session.send_resource_updated = AsyncMock()
    result = await handle_append_insight({"insight": "new finding"}, db, None, None, mock_server)
    assert _text(result[0]) == "Insight added to memo"
    assert "new finding" in db.get_memo()
    mock_server.request_context.session.send_resource_updated.assert_awaited_once()


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
    assert "Table created successfully" in _text(results[0])


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


def test_load_exclusion_non_object_returns_empty(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / "list.json"
    config_file.write_text("[1, 2, 3]")
    assert _load_exclusion_from_file(str(config_file)) == {}


def test_load_exclusion_invalid_json_returns_empty(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / "broken.json"
    config_file.write_text("{ not-json ")
    assert _load_exclusion_from_file(str(config_file)) == {}


def test_load_exclusion_missing_pattern_returns_empty(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text('{"hello": "world"}')
    assert _load_exclusion_from_file(str(config_file)) == {}


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


# ── prefetch_tables ───────────────────────────────────────────────────────────


async def test_prefetch_tables_basic(fake_db: SnowflakeDB, patched_sql: dict) -> None:
    patched_sql["information_schema.tables"] = lambda s: s.create_dataframe(
        [["ORDERS", "orders table"]], schema=["TABLE_NAME", "COMMENT"]
    )
    patched_sql["information_schema.columns"] = lambda s: s.create_dataframe(
        [["ORDERS", "ID", "NUMBER", "pk"]],
        schema=["TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "COMMENT"],
    )
    result = await prefetch_tables(fake_db, {"database": "mydb", "schema": "public"})
    assert "ORDERS" in result
    orders = cast(dict[str, object], result["ORDERS"])
    columns = cast(dict[str, object], orders["COLUMNS"])
    assert "ID" in columns


async def test_prefetch_tables_invalid_credentials_raises(fake_db: SnowflakeDB) -> None:
    with pytest.raises(Exception):
        await prefetch_tables(fake_db, {})


# ── _dispatch_tool_call ───────────────────────────────────────────────────────


async def test_dispatch_tool_call_excluded_tool() -> None:
    db = SnowflakeDB({})
    result = await _dispatch_tool_call(
        "read_query",
        {"query": "SELECT 1"},
        db,
        [],
        ["read_query"],
        {"databases": [], "schemas": [], "tables": []},
        False,
        SQLWriteDetector(),
        MagicMock(),
        False,
    )
    assert "excluded" in _text(result[0])


async def test_dispatch_tool_call_unknown_tool_raises() -> None:
    db = SnowflakeDB({})
    with pytest.raises(ValueError, match="Unknown tool"):
        await _dispatch_tool_call(
            "missing",
            {},
            db,
            [],
            [],
            {"databases": [], "schemas": [], "tables": []},
            False,
            SQLWriteDetector(),
            MagicMock(),
            False,
        )


async def test_dispatch_tool_call_list_path_passes_exclusion() -> None:
    db = SnowflakeDB({})
    handler = AsyncMock(return_value=[types.TextContent(type="text", text="ok")])
    allowed_tools = [
        Tool(
            name="list_databases", description="d", input_schema={"type": "object"}, handler=handler
        )
    ]
    exclusion = {"databases": ["tmp"], "schemas": [], "tables": []}
    await _dispatch_tool_call(
        "list_databases",
        {},
        db,
        allowed_tools,
        [],
        exclusion,
        False,
        SQLWriteDetector(),
        MagicMock(),
        True,
    )
    assert handler.await_count == 1
    assert handler.await_args_list[0].kwargs["exclusion_config"] == exclusion
    assert handler.await_args_list[0].kwargs["exclude_json_results"] is True


# ── _register_handlers / server.main ─────────────────────────────────────────


class _FakeServer:
    def __init__(self, _name: str = "fake") -> None:
        self.request_context = MagicMock()
        self.request_context.session.send_resource_updated = AsyncMock()
        self._list_resources: Callable[..., Awaitable[Any]] | None = None
        self._read_resource: Callable[..., Awaitable[Any]] | None = None
        self._list_prompts: Callable[..., Awaitable[Any]] | None = None
        self._get_prompt: Callable[..., Awaitable[Any]] | None = None
        self._call_tool: Callable[..., Awaitable[Any]] | None = None
        self._list_tools: Callable[..., Awaitable[Any]] | None = None

    def list_resources(
        self,
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self._list_resources = fn
            return fn

        return decorator

    def read_resource(
        self,
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self._read_resource = fn
            return fn

        return decorator

    def list_prompts(
        self,
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self._list_prompts = fn
            return fn

        return decorator

    def get_prompt(
        self,
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self._get_prompt = fn
            return fn

        return decorator

    def call_tool(
        self,
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self._call_tool = fn
            return fn

        return decorator

    def list_tools(
        self,
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self._list_tools = fn
            return fn

        return decorator

    def get_capabilities(
        self, notification_options: object, experimental_capabilities: object
    ) -> dict[str, bool]:
        return {"ok": True}

    async def run(self, read_stream: object, write_stream: object, init_options: object) -> None:
        return None


async def test_register_handlers_registers_and_executes_closures() -> None:
    fake_server = _FakeServer()
    db = SnowflakeDB({})
    allowed_tools = [
        Tool(
            name="read_query",
            description="Run query",
            input_schema={"type": "object"},
            handler=AsyncMock(return_value=[types.TextContent(type="text", text="ok")]),
        )
    ]
    _register_handlers(
        cast(Any, fake_server),
        db,
        {"ORDERS": {"TABLE_NAME": "ORDERS", "COLUMNS": {}}},
        allowed_tools,
        [],
        {"databases": [], "schemas": [], "tables": []},
        False,
        SQLWriteDetector(),
        False,
    )

    assert fake_server._list_resources is not None
    assert fake_server._list_prompts is not None
    assert fake_server._get_prompt is not None
    assert fake_server._list_tools is not None
    assert fake_server._call_tool is not None

    resources = await cast(
        Callable[[], Awaitable[list[types.Resource]]], fake_server._list_resources
    )()
    assert len(resources) == 2  # noqa: PLR2004
    assert (
        await cast(Callable[[], Awaitable[list[types.Prompt]]], fake_server._list_prompts)() == []
    )
    with pytest.raises(ValueError, match="Unknown prompt"):
        await cast(
            Callable[[str, dict[str, str] | None], Awaitable[types.GetPromptResult]],
            fake_server._get_prompt,
        )("missing", None)
    tools = await cast(Callable[[], Awaitable[list[types.Tool]]], fake_server._list_tools)()
    assert any(t.name == "read_query" for t in tools)
    error_result = await cast(
        Callable[[str, dict[str, str] | None], Awaitable[list[types.TextContent]]],
        fake_server._call_tool,
    )("missing", {})
    assert "Error:" in error_result[0].text


async def test_server_main_runs_with_fake_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeDB:
        def __init__(self, connection_config: dict[str, str]) -> None:
            self.connection_config = connection_config

        def start_init_connection(self) -> None:
            return None

    @asynccontextmanager
    async def _fake_stdio_server() -> AsyncIterator[tuple[str, str]]:
        yield ("read", "write")

    monkeypatch.setattr("mcp_snowflake_server.server.SnowflakeDB", _FakeDB)
    monkeypatch.setattr("mcp_snowflake_server.server.Server", _FakeServer)
    monkeypatch.setattr(
        "mcp_snowflake_server.server.mcp.server.stdio.stdio_server", _fake_stdio_server
    )
    monkeypatch.setattr("mcp_snowflake_server.server.importlib.metadata.version", lambda _: "0.0.0")

    await server_main(
        allow_write=False,
        connection_args={"database": "MYDB", "schema": "PUBLIC"},
        prefetch=False,
        exclude_tools=["write_query"],
        exclude_patterns={"tables": ["tmp"]},
        exclude_json_results=True,
    )


# ── package metadata lookup ────────────────────────────────────────────────────


def test_package_metadata_name_matches_pyproject() -> None:
    """Ensure the distribution name used in importlib.metadata.version() matches pyproject.toml.

    This guards against renames of the package that would cause a
    PackageNotFoundError at runtime.
    """
    pyproject_path = pathlib.Path(__file__).parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    dist_name: str = pyproject["project"]["name"]

    # Should not raise PackageNotFoundError
    version = importlib.metadata.version(dist_name)
    assert version, f"Expected a non-empty version for distribution '{dist_name}'"


def test_server_uses_correct_package_name_for_metadata() -> None:
    """Static check: the name passed to importlib.metadata.version() in server.py
    must match the distribution name declared in pyproject.toml.

    This test does not require the package to be installed and catches
    copy-paste or rename mistakes before runtime.
    """
    pyproject_path = pathlib.Path(__file__).parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)
    dist_name: str = pyproject["project"]["name"]

    server_path = (
        pathlib.Path(__file__).parent.parent / "src" / "mcp_snowflake_server" / "server.py"
    )
    server_source = server_path.read_text()

    # The source must contain a version() call with the exact distribution name
    assert f'importlib.metadata.version("{dist_name}")' in server_source, (
        f'server.py does not call importlib.metadata.version("{dist_name}"). '
        f'Ensure the distribution name matches pyproject.toml (name = "{dist_name}").'
    )

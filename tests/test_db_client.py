import time
from unittest.mock import MagicMock, patch

import pytest

from mcp_snowflake_server.db_client import SnowflakeDB, _validate_identifier


# ── _validate_identifier (pure, no session) ──────────────────────────────────


@pytest.mark.parametrize(
    "name,expected",
    [
        ("mydb", "MYDB"),
        ("MY_SCHEMA", "MY_SCHEMA"),
        ("table_1", "TABLE_1"),
        ("_private", "_PRIVATE"),
    ],
)
def test_validate_identifier_valid(name: str, expected: str) -> None:
    assert _validate_identifier(name, "test") == expected


@pytest.mark.parametrize("bad", ["", "1abc", "a-b", "a;b", "a b", "a.b", "drop--", "a'b"])
def test_validate_identifier_invalid(bad: str) -> None:
    with pytest.raises(ValueError, match="Invalid Snowflake identifier"):
        _validate_identifier(bad, "test")


# ── execute_query ─────────────────────────────────────────────────────────────


async def test_execute_query_returns_rows(
    fake_db: SnowflakeDB, patched_sql: dict, snowpark_session: object
) -> None:
    patched_sql["SELECT 1"] = lambda s: s.create_dataframe([[1]], schema=["VALUE"])
    rows, data_id = await fake_db.execute_query("SELECT 1")
    assert rows == [{"VALUE": 1}]
    assert len(data_id) == 36  # noqa: PLR2004  # UUID length


async def test_execute_query_multi_rows(
    fake_db: SnowflakeDB, patched_sql: dict, snowpark_session: object
) -> None:
    patched_sql["DATABASES"] = lambda s: s.create_dataframe(
        [["DB1"], ["DB2"]], schema=["DATABASE_NAME"]
    )
    rows, data_id = await fake_db.execute_query(
        "SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES"
    )
    assert len(rows) == 2  # noqa: PLR2004
    assert rows[0]["DATABASE_NAME"] == "DB1"


async def test_execute_query_reauth_on_expiry(
    patched_sql: dict, snowpark_session: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expired auth_time causes _init_database to be called."""
    db = SnowflakeDB({})
    db.session = snowpark_session
    db.auth_time = 0.0  # force expiry

    patched_sql["SELECT 42"] = lambda s: s.create_dataframe([[42]], schema=["N"])

    init_called: list[bool] = []

    async def fake_init(self: SnowflakeDB) -> None:
        init_called.append(True)
        self.session = snowpark_session
        self.auth_time = time.time()

    monkeypatch.setattr(SnowflakeDB, "_init_database", fake_init)
    rows, _ = await db.execute_query("SELECT 42")
    assert init_called


# ── _init_database ────────────────────────────────────────────────────────────


async def test_init_database_sets_session(
    snowpark_session: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_init_database should set self.session and auth_time when builder.configs().create() is mocked."""
    db = SnowflakeDB({"warehouse": "MY_WH"})

    sql_calls: list[str] = []

    def capture_sql(q: str) -> MagicMock:
        sql_calls.append(q)
        return MagicMock()

    monkeypatch.setattr(snowpark_session, "sql", capture_sql)

    mock_builder = MagicMock()
    mock_builder.configs.return_value = mock_builder
    mock_builder.create.return_value = snowpark_session

    with patch("mcp_snowflake_server.db_client.Session") as mock_session_cls:
        mock_session_cls.builder = mock_builder
        await db._init_database()

    assert db.session is not None
    assert db.auth_time > 0
    assert any("MY_WH" in c for c in sql_calls)


async def test_init_database_non_string_warehouse_raises() -> None:
    db = SnowflakeDB({"warehouse": 123})
    with pytest.raises(ValueError, match="Failed to connect"):
        with patch("mcp_snowflake_server.db_client.Session") as mock_session_cls:
            mock_builder = MagicMock()
            mock_builder.configs.return_value = mock_builder
            mock_session = MagicMock()
            mock_builder.create.return_value = mock_session
            mock_session_cls.builder = mock_builder
            await db._init_database()


# ── get_memo / add_insight ────────────────────────────────────────────────────


def test_get_memo_empty() -> None:
    db = SnowflakeDB({})
    assert "No data insights" in db.get_memo()


def test_add_and_get_memo() -> None:
    db = SnowflakeDB({})
    db.add_insight("Table X has 100 rows")
    memo = db.get_memo()
    assert "Table X has 100 rows" in memo

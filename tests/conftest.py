from __future__ import annotations

import time
from collections.abc import Callable, Generator
from decimal import Decimal
from functools import partial
from typing import Any

import pandas as pd
import pytest
from snowflake.snowpark import Session

from mcp_snowflake_server.db_client import SnowflakeDB


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--snowflake-session", action="store", default="local")


@pytest.fixture(scope="module")
def snowpark_session(request: pytest.FixtureRequest) -> Generator[Session]:
    """Real Snowpark session using local testing mode."""
    if request.config.getoption("--snowflake-session") == "local":
        with Session.builder.config("local_testing", True).create() as s:
            yield s
    else:
        pytest.skip("live Snowflake not configured for unit tests")


@pytest.fixture
def fake_db(snowpark_session: Session) -> SnowflakeDB:
    """SnowflakeDB with a real local-testing Session injected."""
    db = SnowflakeDB({})
    db.session = snowpark_session
    db.auth_time = time.time()
    return db


@pytest.fixture
def patched_sql(
    snowpark_session: Session, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Callable[[Session], Any]]:
    """
    Route session.sql(query) to Snowpark DataFrames by keyword matching.
    Usage: patched_sql["KEYWORD"] = lambda s: s.create_dataframe(...)
    """
    routes: dict[str, Callable[[Session], Any]] = {}

    def mock_sql(session: Session, sql_string: str) -> Any:
        for needle, factory in routes.items():
            if needle.upper() in sql_string.upper():
                return factory(session)
        raise RuntimeError(f"Unexpected SQL in local test: {sql_string!r}")

    monkeypatch.setattr(snowpark_session, "sql", partial(mock_sql, snowpark_session))
    return routes


@pytest.fixture
def sample_rows() -> list[dict[str, Any]]:
    return [
        {"NAME": "MYDB", "VALUE": Decimal("3.14"), "TS": pd.Timestamp("2024-01-01")},
        {"NAME": "OTHERDB", "VALUE": Decimal("0"), "TS": pd.NaT},
    ]

import pytest

from mcp_snowflake_server.write_detector import SQLWriteDetector


@pytest.fixture
def detector() -> SQLWriteDetector:
    return SQLWriteDetector()


def test_select_not_write(detector: SQLWriteDetector) -> None:
    result = detector.analyze_query("SELECT 1")
    assert result["contains_write"] is False
    assert result["write_operations"] == set()
    assert result["has_cte_write"] is False


def test_empty_query(detector: SQLWriteDetector) -> None:
    result = detector.analyze_query("")
    assert result["contains_write"] is False


def test_whitespace_query(detector: SQLWriteDetector) -> None:
    result = detector.analyze_query("   ")
    assert result["contains_write"] is False


@pytest.mark.parametrize("keyword", ["INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "REPLACE"])
def test_dml_write_detected(detector: SQLWriteDetector, keyword: str) -> None:
    result = detector.analyze_query(f"{keyword} INTO foo VALUES (1)")
    assert result["contains_write"] is True
    assert keyword in result["write_operations"]


@pytest.mark.parametrize("keyword", ["CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME"])
def test_ddl_detected(detector: SQLWriteDetector, keyword: str) -> None:
    result = detector.analyze_query(f"{keyword} TABLE foo (id INT)")
    assert result["contains_write"] is True


@pytest.mark.parametrize("keyword", ["GRANT", "REVOKE"])
@pytest.mark.xfail(
    reason="sqlparse assigns DCL keywords a token type not covered by the current check"
)
def test_dcl_detected(detector: SQLWriteDetector, keyword: str) -> None:
    result = detector.analyze_query(f"{keyword} SELECT ON foo TO user1")
    assert result["contains_write"] is True


@pytest.mark.xfail(
    reason="_analyze_cte does not recurse into sub-tokens; nested INSERT not detected"
)
def test_cte_write_detected(detector: SQLWriteDetector) -> None:
    result = detector.analyze_query("WITH x AS (INSERT INTO foo VALUES (1)) SELECT * FROM x")
    assert result["has_cte_write"] is True
    assert result["contains_write"] is True


def test_case_insensitive(detector: SQLWriteDetector) -> None:
    result = detector.analyze_query("insert into foo values (1)")
    assert result["contains_write"] is True

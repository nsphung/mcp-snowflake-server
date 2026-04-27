import json
import math
from datetime import date, time
from decimal import Decimal

import pandas as pd
import pytest

from mcp_snowflake_server.serialization import (
    _serialize_value,
    to_json,
    to_yaml,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (pd.NaT, None),
        (pd.Timestamp("2024-03-15 10:00:00"), "2024-03-15T10:00:00"),
        (date(2024, 3, 15), "2024-03-15"),
        (Decimal("3.14"), 3.14),
        (float("nan"), None),
        ("hello", "hello"),
        (42, 42),
        (True, True),
        (None, None),
    ],
)
def test_serialize_value(value: object, expected: object) -> None:
    result = _serialize_value(value)
    if expected is None:
        assert result is None
    elif isinstance(expected, float):
        assert isinstance(result, (int, float))
        assert abs(float(result) - expected) < 1e-9  # noqa: PLR2004
    else:
        assert result == expected


def test_to_json_roundtrip() -> None:
    data = {
        "name": "test",
        "value": Decimal("1.23"),
        "ts": pd.Timestamp("2024-01-01"),
        "dt": date(2024, 1, 1),
        "nat": pd.NaT,
        "nan_val": float("nan"),
    }
    result = to_json(data)
    parsed = json.loads(result)
    assert parsed["name"] == "test"
    assert abs(parsed["value"] - 1.23) < 1e-9  # noqa: PLR2004
    assert parsed["ts"] == "2024-01-01T00:00:00"
    assert parsed["dt"] == "2024-01-01"
    assert parsed["nat"] is None
    assert math.isnan(parsed["nan_val"])


def test_to_yaml_returns_str() -> None:
    result = to_yaml({"key": "value"})
    assert isinstance(result, str)
    assert len(result) > 0


def test_to_yaml_nat_is_null() -> None:
    result = to_yaml({"ts": pd.NaT})
    assert "null" in result or result.strip().endswith(":")


def test_to_yaml_decimal_as_float() -> None:
    result = to_yaml({"v": Decimal("2.5")})
    assert "2.5" in result


def test_to_yaml_empty_dict() -> None:
    result = to_yaml({})
    assert isinstance(result, str)


def test_serialize_value_binary_passthrough() -> None:
    assert _serialize_value(b"abc") == b"abc"
    assert _serialize_value(bytearray(b"abc")) == bytearray(b"abc")


def test_serialize_value_time_passthrough() -> None:
    assert _serialize_value(time(12, 34, 56)) == time(12, 34, 56)

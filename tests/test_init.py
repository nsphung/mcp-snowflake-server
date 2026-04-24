import pathlib
import sys

import pytest

from mcp_snowflake_server import load_connection_from_toml, parse_args


def write_toml(path: pathlib.Path, content: str) -> None:
    path.write_bytes(content.encode())


# ── load_connection_from_toml ─────────────────────────────────────────────────


def test_load_connection_found(tmp_path: pathlib.Path) -> None:
    toml_file = tmp_path / "connections.toml"
    write_toml(toml_file, '[dev]\naccount = "myaccount"\nuser = "myuser"\n')
    result = load_connection_from_toml(str(toml_file), "dev")
    assert result["account"] == "myaccount"
    assert result["user"] == "myuser"


def test_load_connection_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_connection_from_toml("/nonexistent/path.toml", "dev")


def test_load_connection_missing_connection(tmp_path: pathlib.Path) -> None:
    toml_file = tmp_path / "connections.toml"
    write_toml(toml_file, '[prod]\naccount = "prod"\n')
    with pytest.raises(KeyError, match="dev"):
        load_connection_from_toml(str(toml_file), "dev")


def test_load_connection_invalid_toml(tmp_path: pathlib.Path) -> None:
    toml_file = tmp_path / "bad.toml"
    toml_file.write_bytes(b"not valid [ toml")
    with pytest.raises(ValueError, match="Invalid TOML"):
        load_connection_from_toml(str(toml_file), "dev")


# ── parse_args ────────────────────────────────────────────────────────────────


def test_parse_args_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog"])
    server_args, connection_args = parse_args()
    assert server_args["allow_write"] is False
    assert server_args["prefetch"] is False
    assert server_args["exclude_tools"] == []
    assert connection_args == {}


def test_parse_args_allow_write(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--allow_write"])
    server_args, _ = parse_args()
    assert server_args["allow_write"] is True


def test_parse_args_exclude_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--exclude_tools", "list_databases", "list_schemas"])
    server_args, _ = parse_args()
    assert "list_databases" in server_args["exclude_tools"]
    assert "list_schemas" in server_args["exclude_tools"]


def test_parse_args_extra_connection_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--account", "myaccount", "--user", "bob"])
    _, connection_args = parse_args()
    assert connection_args["account"] == "myaccount"
    assert connection_args["user"] == "bob"

import pathlib
import sys
from types import SimpleNamespace

import pytest

from mcp_snowflake_server import load_connection_from_toml, main, parse_args


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


def test_parse_args_private_key_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--private_key_file",
            "/tmp/key.p8",
            "--private_key_file_pwd",
            "secret",
        ],
    )
    _, connection_args = parse_args()
    assert connection_args["private_key_file"] == "/tmp/key.p8"
    assert connection_args["private_key_file_pwd"] == "secret"


def test_parse_args_connection_file_and_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--connections-file", "connections.toml", "--connection-name", "dev"],
    )
    server_args, _ = parse_args()
    assert server_args["connections_file"] == "connections.toml"
    assert server_args["connection_name"] == "dev"


def test_main_requires_both_toml_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--connections-file", "connections.toml"])
    with pytest.raises(ValueError, match="must be provided together"):
        main()


def test_main_asserts_missing_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key: "PUBLIC" if key == "SNOWFLAKE_SCHEMA" else None,
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(AssertionError, match="database"):
        main()


def test_main_asserts_missing_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key: "MYDB" if key == "SNOWFLAKE_DATABASE" else None,
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(AssertionError, match="schema"):
        main()


def test_main_uses_toml_precedence_and_runs_server(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    toml_file = tmp_path / "connections.toml"
    write_toml(
        toml_file,
        '[dev]\ndatabase = "TOML_DB"\nschema = "TOML_SCHEMA"\nuser = "toml_user"\n',
    )

    monkeypatch.setenv("SNOWFLAKE_DATABASE", "ENV_DB")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "ENV_SCHEMA")
    monkeypatch.setenv("SNOWFLAKE_USER", "env_user")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_FILE", "/env/key.p8")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD", "env-secret")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--connections-file",
            str(toml_file),
            "--connection-name",
            "dev",
            "--user",
            "cli_user",
        ],
    )

    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))

    main()

    connection_args = captured["connection_args"]
    assert isinstance(connection_args, dict)
    assert connection_args["database"] == "TOML_DB"
    assert connection_args["schema"] == "TOML_SCHEMA"
    assert connection_args["user"] == "toml_user"

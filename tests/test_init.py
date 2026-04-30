import logging
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
    with pytest.raises(ValueError, match="database"):
        main()


def test_main_asserts_missing_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key: "MYDB" if key == "SNOWFLAKE_DATABASE" else None,
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="schema"):
        main()


def test_main_uses_toml_precedence_and_runs_server(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    toml_file = tmp_path / "connections.toml"
    write_toml(
        toml_file,
        '[dev]\ndatabase = "TOML_DB"\nschema = "TOML_SCHEMA"\nuser = "toml_user"\naccount = "toml_account"\nauthenticator = "externalbrowser"\n',
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


def test_main_missing_authenticator_defaults_to_snowflake(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """authenticator is optional — omitting it must log a warning and default to 'snowflake'."""
    env = {
        "SNOWFLAKE_DATABASE": "DB",
        "SNOWFLAKE_SCHEMA": "SCH",
        "SNOWFLAKE_ACCOUNT": "myorg-myaccount",
        "SNOWFLAKE_USER": "alice",
        "SNOWFLAKE_PASSWORD": "secret",
    }
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])

    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))

    with caplog.at_level(logging.WARNING, logger="mcp_snowflake_server"):
        main()

    connection_args = captured.get("connection_args")
    assert isinstance(connection_args, dict)
    assert connection_args.get("authenticator") == "snowflake"
    assert any("authenticator" in record.message.lower() for record in caplog.records)


# ── OAuth Client Credentials ──────────────────────────────────────────────────

_OAUTH_ENV: dict[str, str] = {
    "SNOWFLAKE_AUTHENTICATOR": "oauth_client_credentials",
    "SNOWFLAKE_ACCOUNT": "myorg-myaccount",
    "SNOWFLAKE_OAUTH_CLIENT_ID": "my-client-id",
    "SNOWFLAKE_OAUTH_CLIENT_SECRET": "my-secret",
    "SNOWFLAKE_OAUTH_TOKEN_REQUEST_URL": "https://example.com/token",
    "SNOWFLAKE_OAUTH_SCOPE": "session:role:MY_ROLE",
    "SNOWFLAKE_DATABASE": "DB",
    "SNOWFLAKE_SCHEMA": "SCH",
}


def test_main_reads_oauth_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: _OAUTH_ENV.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])

    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))

    main()

    connection_args = captured["connection_args"]
    assert isinstance(connection_args, dict)
    assert connection_args["oauth_client_id"] == "my-client-id"
    assert connection_args["oauth_client_secret"] == "my-secret"
    assert connection_args["oauth_token_request_url"] == "https://example.com/token"
    assert connection_args["oauth_scope"] == "session:role:MY_ROLE"


def test_main_oauth_without_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    """oauth_scope is optional — should not raise when absent."""
    env = {k: v for k, v in _OAUTH_ENV.items() if k != "SNOWFLAKE_OAUTH_SCOPE"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])

    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))

    main()

    connection_args = captured["connection_args"]
    assert isinstance(connection_args, dict)
    assert "oauth_scope" not in connection_args


def test_main_oauth_missing_client_id_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {k: v for k, v in _OAUTH_ENV.items() if k != "SNOWFLAKE_OAUTH_CLIENT_ID"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="oauth_client_id"):
        main()


def test_main_oauth_missing_client_secret_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {k: v for k, v in _OAUTH_ENV.items() if k != "SNOWFLAKE_OAUTH_CLIENT_SECRET"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="oauth_client_secret"):
        main()


def test_main_oauth_missing_token_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {k: v for k, v in _OAUTH_ENV.items() if k != "SNOWFLAKE_OAUTH_TOKEN_REQUEST_URL"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="oauth_token_request_url"):
        main()


# ── Other authenticator types ─────────────────────────────────────────────────

_BASE_ENV: dict[str, str] = {
    "SNOWFLAKE_DATABASE": "DB",
    "SNOWFLAKE_SCHEMA": "SCH",
    "SNOWFLAKE_ACCOUNT": "myorg-myaccount",
    "SNOWFLAKE_AUTHENTICATOR": "snowflake",
}


def test_main_snowflake_default_missing_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default (snowflake) authenticator requires account, user, password."""
    env = {**_BASE_ENV, "SNOWFLAKE_USER": "alice"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="password"):
        main()


def test_main_snowflake_default_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {**_BASE_ENV, "SNOWFLAKE_USER": "alice", "SNOWFLAKE_PASSWORD": "secret"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))
    main()
    connection_args = captured["connection_args"]
    assert isinstance(connection_args, dict)
    assert connection_args["password"] == "secret"


def test_main_externalbrowser_missing_user(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {**_BASE_ENV, "SNOWFLAKE_AUTHENTICATOR": "externalbrowser"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="user"):
        main()


def test_main_externalbrowser_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {**_BASE_ENV, "SNOWFLAKE_AUTHENTICATOR": "externalbrowser", "SNOWFLAKE_USER": "alice"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))
    main()


def test_main_snowflake_jwt_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {**_BASE_ENV, "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt", "SNOWFLAKE_USER": "alice"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="private_key_file.*private_key"):
        main()


def test_main_snowflake_jwt_ok_with_key_file(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {
        **_BASE_ENV,
        "SNOWFLAKE_AUTHENTICATOR": "snowflake_jwt",
        "SNOWFLAKE_USER": "alice",
        "SNOWFLAKE_PRIVATE_KEY_FILE": "/path/to/key.p8",
    }
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))
    main()


def test_main_oauth_bearer_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {**_BASE_ENV, "SNOWFLAKE_AUTHENTICATOR": "oauth"}
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    with pytest.raises(ValueError, match="token"):
        main()


def test_main_oauth_bearer_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    env = {
        **_BASE_ENV,
        "SNOWFLAKE_AUTHENTICATOR": "oauth",
        "SNOWFLAKE_TOKEN": "eyJhbGciOiJSUzI1NiJ9...",
    }
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))
    main()


def test_main_unknown_authenticator_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown authenticator should warn but not raise during validation."""
    env = {
        **_BASE_ENV,
        "SNOWFLAKE_AUTHENTICATOR": "some_future_auth",
        "SNOWFLAKE_USER": "alice",
    }
    monkeypatch.setattr(
        "mcp_snowflake_server.os.getenv",
        lambda key, default=None: env.get(key, default),
    )
    monkeypatch.setattr(sys, "argv", ["prog"])
    captured: dict[str, object] = {}

    async def fake_server_main(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("mcp_snowflake_server.server", SimpleNamespace(main=fake_server_main))
    main()  # should not raise

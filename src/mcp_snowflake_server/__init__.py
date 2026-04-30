import argparse
import asyncio
import importlib.metadata
import logging
import os
import tomllib
from typing import Any, cast

import dotenv
import snowflake.connector

from . import server, write_detector


logger = logging.getLogger("mcp_snowflake_server")


def load_connection_from_toml(toml_file: str, connection_name: str) -> dict[str, Any]:
    """Load connection configuration from a TOML file.

    Args:
        toml_file: Path to the TOML file containing connection configurations
        connection_name: Name of the connection to load from the file

    Returns:
        Dictionary containing connection parameters

    Raises:
        FileNotFoundError: If the TOML file doesn't exist
        KeyError: If the connection name doesn't exist in the file
        ValueError: If the TOML file is invalid
    """
    try:
        with open(toml_file, "rb") as f:
            toml_data = tomllib.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"TOML file not found: {toml_file}")
    except Exception as e:
        raise ValueError(f"Invalid TOML file: {e}")

    # Look for the connection as a top-level section
    if connection_name in toml_data:
        connection_config = toml_data[connection_name]
    else:
        raise KeyError(f"Connection '{connection_name}' not found in TOML file")

    return cast(dict[str, Any], connection_config)


def parse_args() -> tuple[dict[str, Any], dict[str, Any]]:
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument(
        "--allow_write",
        required=False,
        default=False,
        action="store_true",
        help="Allow write operations on the database",
    )
    parser.add_argument("--log_dir", required=False, default=None, help="Directory to log to")
    parser.add_argument("--log_level", required=False, default="INFO", help="Logging level")
    parser.add_argument(
        "--prefetch",
        action="store_true",
        dest="prefetch",
        default=False,
        help="Prefetch table descriptions (when enabled, list_tables and describe_table are disabled)",
    )
    parser.add_argument(
        "--no-prefetch",
        action="store_false",
        dest="prefetch",
        help="Don't prefetch table descriptions",
    )
    parser.add_argument(
        "--exclude_tools",
        required=False,
        default=[],
        nargs="+",
        help="List of tools to exclude",
    )
    parser.add_argument(
        "--exclude-json-results",
        action="store_true",
        dest="exclude_json_results",
        default=False,
        help="Exclude JSON output from results",
    )

    parser.add_argument(
        "--private_key_file",
        required=False,
        help="Path to private key file for authentication",
    )

    parser.add_argument(
        "--private_key_file_pwd",
        required=False,
        help="Passphrase for encrypted private key file (if your private key is password protected)",
    )

    parser.add_argument(
        "--connection-name",
        required=False,
        default=None,
        help="Name of the connection to use from the TOML file",
    )

    parser.add_argument(
        "--connections-file",
        required=False,
        default=None,
        help="Path to the TOML file containing connection configurations",
    )

    # First, get all the arguments we don't know about
    args, unknown = parser.parse_known_args()

    # Create a dictionary to store our key-value pairs
    connection_args = {}

    # Iterate through unknown args in pairs
    for i in range(0, len(unknown), 2):
        if i + 1 >= len(unknown):
            break

        key = unknown[i]
        value = unknown[i + 1]

        # Make sure it's a keyword argument (starts with --)
        if key.startswith("--"):
            key = key[2:]  # Remove the '--'
            connection_args[key] = value

    # Now we can add the known args to kwargs
    server_args = {
        "allow_write": args.allow_write,
        "log_dir": args.log_dir,
        "log_level": args.log_level,
        "prefetch": args.prefetch,
        "exclude_tools": args.exclude_tools,
        "exclude_json_results": args.exclude_json_results,
        "connection_name": getattr(args, "connection_name", None),
        "connections_file": getattr(args, "connections_file", None),
    }

    # Add private_key_file if provided
    if args.private_key_file:
        connection_args["private_key_file"] = args.private_key_file

    # Add private_key_file_pwd if provided
    if args.private_key_file_pwd:
        connection_args["private_key_file_pwd"] = args.private_key_file_pwd

    return server_args, connection_args


def _connection_args_from_env() -> dict[str, Any]:
    """Build a connection-args dict from SNOWFLAKE_* environment variables."""
    default_connection_args = snowflake.connector.connection.DEFAULT_CONFIGURATION
    args: dict[str, Any] = {
        k: os.getenv("SNOWFLAKE_" + k.upper())
        for k in default_connection_args
        if os.getenv("SNOWFLAKE_" + k.upper()) is not None
    }

    # Keys not in DEFAULT_CONFIGURATION that require explicit handling
    _optional_extras = {
        "private_key_file": "SNOWFLAKE_PRIVATE_KEY_FILE",
        "private_key_file_pwd": "SNOWFLAKE_PRIVATE_KEY_FILE_PWD",
        "oauth_client_id": "SNOWFLAKE_OAUTH_CLIENT_ID",
        "oauth_client_secret": "SNOWFLAKE_OAUTH_CLIENT_SECRET",
        "oauth_token_request_url": "SNOWFLAKE_OAUTH_TOKEN_REQUEST_URL",
        "oauth_scope": "SNOWFLAKE_OAUTH_SCOPE",
    }
    for key, env_var in _optional_extras.items():
        value = os.getenv(env_var)
        if value:
            args[key] = value

    return args


# Authenticator type → list of mandatory connection keys.
# "snowflake" (password-based) is the default when no authenticator is specified.
_AUTHENTICATOR_REQUIRED_PARAMS: dict[str, list[str]] = {
    "snowflake": ["account", "user", "password"],
    "externalbrowser": ["account", "user"],
    "snowflake_jwt": ["account", "user"],  # + private_key_file or private_key
    "oauth": ["account", "token"],
    "oauth_client_credentials": [
        "account",
        "oauth_client_id",
        "oauth_client_secret",
        "oauth_token_request_url",
    ],
}


def _validate_connection_args(connection_args: dict[str, Any]) -> None:
    """Validate that all mandatory parameters are present for the chosen authenticator.

    Raises ``ValueError`` with an actionable message (logged to stderr) so
    that MCP clients receive a clear startup-failure signal instead of a
    silent crash or an opaque ``AssertionError``.
    """

    def _missing(key: str, hint: str) -> None:
        msg = f"Missing required connection parameter '{key}'. {hint}"
        logger.error(msg)
        raise ValueError(msg)

    # -- common mandatory params regardless of authenticator -----------------
    if "database" not in connection_args:
        _missing(
            "database",
            'Provide via "--database" argument, "SNOWFLAKE_DATABASE" env var, or TOML file.',
        )
    if "schema" not in connection_args:
        _missing(
            "schema",
            'Provide via "--schema" argument, "SNOWFLAKE_SCHEMA" env var, or TOML file.',
        )

    # -- authenticator is optional; default to 'snowflake' for backward compat --
    if "authenticator" not in connection_args:
        valid = ", ".join(_AUTHENTICATOR_REQUIRED_PARAMS)
        logger.warning(
            "'authenticator' was not specified; defaulting to 'snowflake'. "
            'Please provide it explicitly via "--authenticator" argument, '
            '"SNOWFLAKE_AUTHENTICATOR" env var, or TOML file. '
            f"Valid values: {valid}."
        )
        connection_args["authenticator"] = "snowflake"
    authenticator = connection_args["authenticator"].lower()

    # -- authenticator-specific mandatory params -----------------------------
    required_keys = _AUTHENTICATOR_REQUIRED_PARAMS.get(authenticator)
    if required_keys is None:
        # Unknown authenticator – let Snowflake connector handle it, but warn.
        logger.warning("Unknown authenticator '%s'; skipping parameter validation.", authenticator)
        return

    for key in required_keys:
        if key not in connection_args:
            env_hint = f'"SNOWFLAKE_{key.upper()}" env var'
            _missing(
                key,
                f"Required for authenticator '{authenticator}'. Set via "
                f'"--{key}" argument, {env_hint}, or TOML file.',
            )

    # snowflake_jwt needs at least one of private_key_file / private_key
    if authenticator == "snowflake_jwt":
        if "private_key_file" not in connection_args and "private_key" not in connection_args:
            msg = (
                "Key-pair authentication (snowflake_jwt) requires 'private_key_file' or "
                "'private_key'. Provide via \"--private_key_file\" argument, "
                '"SNOWFLAKE_PRIVATE_KEY_FILE" env var, or TOML file.'
            )
            logger.error(msg)
            raise ValueError(msg)


def main() -> None:
    """Main entry point for the package."""

    dotenv.load_dotenv()

    connection_args_from_env = _connection_args_from_env()

    server_args, connection_args = parse_args()

    # Check if TOML configuration is requested
    if server_args.get("connections_file") and server_args.get("connection_name"):
        connections_file = server_args["connections_file"]
        connection_name = server_args["connection_name"]

        try:
            toml_connection_args = load_connection_from_toml(connections_file, connection_name)
            # TOML config takes precedence, then command line args, then environment variables
            connection_args = {
                **connection_args_from_env,
                **connection_args,
                **toml_connection_args,
            }
        except (FileNotFoundError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to load TOML configuration: {e}")

    elif server_args.get("connections_file") or server_args.get("connection_name"):
        # If only one of the TOML parameters is provided, show an error
        raise ValueError("Both --connections-file and --connection-name must be provided together")

    else:
        # Use traditional configuration method
        connection_args = {**connection_args_from_env, **connection_args}

    _validate_connection_args(connection_args)

    logger.info(
        "Starting MCP Snowflake Server with AUTHENTICATOR='%s' with Version='%s'",
        connection_args.get("authenticator", "?"),
        importlib.metadata.version("mcp-snowflake-server-nsp"),
    )

    asyncio.run(
        server.main(
            connection_args=connection_args,
            allow_write=server_args["allow_write"],
            log_dir=server_args["log_dir"],
            prefetch=server_args["prefetch"],
            log_level=server_args["log_level"],
            exclude_tools=server_args["exclude_tools"],
            exclude_json_results=server_args["exclude_json_results"],
        )
    )


# Optionally expose other important items at package level
__all__ = ["main", "server", "write_detector"]

if __name__ == "__main__":
    main()

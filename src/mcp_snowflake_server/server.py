import importlib.metadata
import json
import logging
import os
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import cast

import mcp.server.stdio
from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl, BaseModel

from .db_client import ConnectionConfig, SnowflakeDB, _validate_identifier
from .serialization import to_json, to_yaml
from .write_detector import SQLWriteDetector


type ResponseType = types.TextContent | types.ImageContent | types.EmbeddedResource

# Constant for fully qualified table name parts (database.schema.table)
FULLY_QUALIFIED_NAME_PARTS = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("mcp_snowflake_server")


def handle_tool_errors[**P](
    func: Callable[P, Awaitable[list[ResponseType]]],
) -> Callable[P, Awaitable[list[ResponseType]]]:
    """Decorator to standardize tool error handling"""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[ResponseType]:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    return wrapper


class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, object]
    handler: Callable[..., Awaitable[list[ResponseType]]]
    tags: list[str] = []


# Tool handlers
async def handle_list_databases(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    *_: object,
    exclusion_config: dict[str, list[str]] | None = None,
    exclude_json_results: bool = False,
) -> list[ResponseType]:
    query = "SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES"
    data, data_id = await db.execute_query(query)

    # Filter out excluded databases
    if exclusion_config and "databases" in exclusion_config and exclusion_config["databases"]:
        filtered_data = []
        for item in data:
            db_name = str(item.get("DATABASE_NAME", ""))
            exclude = False
            for pattern in exclusion_config["databases"]:
                if pattern.lower() in db_name.lower():
                    exclude = True
                    break
            if not exclude:
                filtered_data.append(item)
        data = filtered_data

    output = {
        "type": "data",
        "data_id": data_id,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"),
                    text=json_output,
                    mimeType="application/json",
                ),
            )
        )
    return results


async def handle_list_schemas(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    *_: object,
    exclusion_config: dict[str, list[str]] | None = None,
    exclude_json_results: bool = False,
) -> list[ResponseType]:
    if not arguments or "database" not in arguments:
        raise ValueError("Missing required 'database' parameter")

    database = _validate_identifier(arguments["database"], "database")
    query = f"SELECT SCHEMA_NAME FROM {database}.INFORMATION_SCHEMA.SCHEMATA"
    data, data_id = await db.execute_query(query)

    # Filter out excluded schemas
    if exclusion_config and "schemas" in exclusion_config and exclusion_config["schemas"]:
        filtered_data = []
        for item in data:
            schema_name = str(item.get("SCHEMA_NAME", ""))
            exclude = False
            for pattern in exclusion_config["schemas"]:
                if pattern.lower() in schema_name.lower():
                    exclude = True
                    break
            if not exclude:
                filtered_data.append(item)
        data = filtered_data

    output = {
        "type": "data",
        "data_id": data_id,
        "database": database,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"),
                    text=json_output,
                    mimeType="application/json",
                ),
            )
        )
    return results


async def handle_list_tables(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    *_: object,
    exclusion_config: dict[str, list[str]] | None = None,
    exclude_json_results: bool = False,
) -> list[ResponseType]:
    if not arguments or "database" not in arguments or "schema" not in arguments:
        raise ValueError("Missing required 'database' and 'schema' parameters")

    database = _validate_identifier(arguments["database"], "database")
    schema = _validate_identifier(arguments["schema"], "schema")

    query = f"""
        SELECT table_catalog, table_schema, table_name, comment
        FROM {database}.information_schema.tables
        WHERE table_schema = '{schema}'
    """
    data, data_id = await db.execute_query(query)

    # Filter out excluded tables
    if exclusion_config and "tables" in exclusion_config and exclusion_config["tables"]:
        filtered_data = []
        for item in data:
            table_name = str(item.get("TABLE_NAME", ""))
            exclude = False
            for pattern in exclusion_config["tables"]:
                if pattern.lower() in table_name.lower():
                    exclude = True
                    break
            if not exclude:
                filtered_data.append(item)
        data = filtered_data

    output = {
        "type": "data",
        "data_id": data_id,
        "database": database,
        "schema": schema,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"),
                    text=json_output,
                    mimeType="application/json",
                ),
            )
        )
    return results


async def handle_describe_table(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    *_: object,
    exclude_json_results: bool = False,
) -> list[ResponseType]:
    if not arguments or "table_name" not in arguments:
        raise ValueError("Missing table_name argument")

    table_spec = arguments["table_name"]
    split_identifier = table_spec.split(".")

    # Parse the fully qualified table name
    if len(split_identifier) < FULLY_QUALIFIED_NAME_PARTS:
        raise ValueError("Table name must be fully qualified as 'database.schema.table'")

    database_name = _validate_identifier(split_identifier[0], "database")
    schema_name = _validate_identifier(split_identifier[1], "schema")
    table_name = _validate_identifier(split_identifier[2], "table")

    query = f"""
        SELECT column_name, column_default, is_nullable, data_type, comment
        FROM {database_name}.information_schema.columns
        WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
    """
    data, data_id = await db.execute_query(query)

    output = {
        "type": "data",
        "data_id": data_id,
        "database": database_name,
        "schema": schema_name,
        "table": table_name,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"),
                    text=json_output,
                    mimeType="application/json",
                ),
            )
        )
    return results


async def handle_read_query(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    write_detector: SQLWriteDetector,
    *_: object,
    exclude_json_results: bool = False,
) -> list[ResponseType]:
    if not arguments or "query" not in arguments:
        raise ValueError("Missing query argument")

    if write_detector.analyze_query(arguments["query"])["contains_write"]:
        raise ValueError("Calls to read_query should not contain write operations")

    data, data_id = await db.execute_query(arguments["query"])

    output = {
        "type": "data",
        "data_id": data_id,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"),
                    text=json_output,
                    mimeType="application/json",
                ),
            )
        )
    return results


async def handle_append_insight(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    _: object,
    __: object,
    server: Server,
    exclude_json_results: bool = False,
) -> list[ResponseType]:
    if not arguments or "insight" not in arguments:
        raise ValueError("Missing insight argument")

    db.add_insight(arguments["insight"])
    await server.request_context.session.send_resource_updated(AnyUrl("memo://insights"))
    return [types.TextContent(type="text", text="Insight added to memo")]


async def handle_write_query(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    _: object,
    allow_write: bool,
    __: object,
    **___: object,
) -> list[ResponseType]:
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "query" not in arguments:
        raise ValueError("Missing query argument")
    if arguments["query"].strip().upper().startswith("SELECT"):
        raise ValueError("SELECT queries are not allowed for write_query")

    results, data_id = await db.execute_query(arguments["query"])
    return [types.TextContent(type="text", text=str(results))]


async def handle_create_table(
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    _: object,
    allow_write: bool,
    __: object,
    **___: object,
) -> list[ResponseType]:
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "query" not in arguments:
        raise ValueError("Missing query argument")
    if not arguments["query"].strip().upper().startswith("CREATE TABLE"):
        raise ValueError("Only CREATE TABLE statements are allowed")

    results, data_id = await db.execute_query(arguments["query"])
    return [types.TextContent(type="text", text=f"Table created successfully. data_id = {data_id}")]


async def prefetch_tables(db: SnowflakeDB, credentials: ConnectionConfig) -> dict[str, object]:
    """Prefetch table and column information"""
    try:
        logger.info("Prefetching table descriptions")
        db_name = _validate_identifier(str(credentials["database"]), "database")
        schema_name = _validate_identifier(str(credentials["schema"]), "schema")
        table_results, data_id = await db.execute_query(
            f"""SELECT table_name, comment
                FROM {db_name}.information_schema.tables
                WHERE table_schema = '{schema_name}'"""
        )

        column_results, data_id = await db.execute_query(
            f"""SELECT table_name, column_name, data_type, comment
                FROM {db_name}.information_schema.columns
                WHERE table_schema = '{schema_name}'"""
        )

        tables_brief: dict[str, object] = {}
        for row in table_results:
            tables_brief[str(row["TABLE_NAME"])] = cast(dict[str, object], {**row, "COLUMNS": {}})

        for row in column_results:
            row_without_table_name: dict[str, object] = {
                k: v for k, v in row.items() if k != "TABLE_NAME"
            }
            table_entry = cast(dict[str, object], tables_brief[str(row["TABLE_NAME"])])
            cast(dict[str, object], table_entry["COLUMNS"])[str(row["COLUMN_NAME"])] = (
                row_without_table_name
            )

        return tables_brief

    except Exception as e:
        logger.error(f"Error prefetching table descriptions: {e}")
        raise


def _setup_logging(log_dir: str | None, log_level: str) -> None:
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        logger.handlers.append(
            logging.FileHandler(os.path.join(log_dir, "mcp_snowflake_server.log"))
        )
    if log_level:
        logger.setLevel(log_level)


def _load_exclusion_from_file(config_file: str) -> dict[str, list[str]]:
    try:
        with open(config_file) as f:
            loaded: object = json.load(f)
        logger.info(f"Loaded configuration from {config_file}")
        if not isinstance(loaded, dict):
            logger.warning(f"Config file {config_file!r} is not a JSON object; ignoring")
            return {}
        raw = cast(dict[str, object], loaded).get("exclude_patterns", {})
        return cast(dict[str, list[str]], raw) if isinstance(raw, dict) else {}
    except FileNotFoundError:
        logger.debug(f"Config file not found: {config_file!r}; skipping")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration file {config_file!r}: {e}")
        return {}


def _build_exclusion_config(
    config_file: str | None, exclude_patterns: dict[str, list[str]] | None
) -> dict[str, list[str]]:
    exclusion_config = _load_exclusion_from_file(config_file) if config_file else {}

    if exclude_patterns:
        for key, patterns in exclude_patterns.items():
            exclusion_config.setdefault(key, []).extend(patterns)

    for key in ["databases", "schemas", "tables"]:
        exclusion_config.setdefault(key, [])

    return exclusion_config


def _resolve_resource(uri: AnyUrl, db: SnowflakeDB, tables_info: dict[str, object]) -> str:
    if str(uri) == "memo://insights":
        return str(db.get_memo())
    elif str(uri).startswith("context://table"):
        table_name = str(uri).split("/")[-1]
        if table_name in tables_info:
            return str(to_yaml(tables_info[table_name]))
        else:
            raise ValueError(f"Unknown table: {table_name}")
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def _dispatch_tool_call(
    name: str,
    arguments: dict[str, str] | None,
    db: SnowflakeDB,
    allowed_tools: list[Tool],
    exclude_tools: list[str],
    exclusion_config: dict[str, list[str]],
    allow_write: bool,
    write_detector: SQLWriteDetector,
    server: Server,
    exclude_json_results: bool,
) -> list[ResponseType]:
    if name in exclude_tools:
        return [
            types.TextContent(
                type="text",
                text=f"Tool {name} is excluded from this data connection",
            )
        ]
    handler = next((tool.handler for tool in allowed_tools if tool.name == name), None)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")
    if name in ["list_databases", "list_schemas", "list_tables"]:
        return await handler(
            arguments,
            db,
            write_detector,
            allow_write,
            server,
            exclusion_config=exclusion_config,
            exclude_json_results=exclude_json_results,
        )
    return await handler(
        arguments,
        db,
        write_detector,
        allow_write,
        server,
        exclude_json_results=exclude_json_results,
    )


def _register_handlers(
    server: Server,
    db: SnowflakeDB,
    tables_info: dict[str, object],
    allowed_tools: list[Tool],
    exclude_tools: list[str],
    exclusion_config: dict[str, list[str]],
    allow_write: bool,
    write_detector: SQLWriteDetector,
    exclude_json_results: bool,
) -> None:
    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        resources = [
            types.Resource(
                uri=AnyUrl("memo://insights"),
                name="Data Insights Memo",
                description="A living document of discovered data insights",
                mimeType="text/plain",
            )
        ]
        table_brief_resources = [
            types.Resource(
                uri=AnyUrl(f"context://table/{table_name}"),
                name=f"{table_name} table",
                description=f"Description of the {table_name} table",
                mimeType="text/plain",
            )
            for table_name in tables_info.keys()
        ]
        resources += table_brief_resources
        return resources

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        return _resolve_resource(uri, db, tables_info)

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        return []

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        raise ValueError(f"Unknown prompt: {name}")

    @server.call_tool()
    @handle_tool_errors
    async def handle_call_tool(name: str, arguments: dict[str, str] | None) -> list[ResponseType]:
        return await _dispatch_tool_call(
            name,
            arguments,
            db,
            allowed_tools,
            exclude_tools,
            exclusion_config,
            allow_write,
            write_detector,
            server,
            exclude_json_results,
        )

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        logger.info("Listing tools")
        logger.error(f"Allowed tools: {allowed_tools}")
        tools = [
            types.Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.input_schema,
            )
            for tool in allowed_tools
        ]
        return tools


async def main(
    allow_write: bool = False,
    connection_args: ConnectionConfig | None = None,
    log_dir: str | None = None,
    prefetch: bool = False,
    log_level: str = "INFO",
    exclude_tools: list[str] | None = None,
    config_file: str = "runtime_config.json",
    exclude_patterns: dict[str, list[str]] | None = None,
    exclude_json_results: bool = False,
) -> None:
    if exclude_tools is None:
        exclude_tools = []
    _setup_logging(log_dir, log_level)

    logger.info("Starting Snowflake MCP Server")
    logger.info("Allow write operations: %s", allow_write)
    logger.info("Prefetch table descriptions: %s", prefetch)
    logger.info("Excluded tools: %s", exclude_tools)

    exclusion_config = _build_exclusion_config(config_file, exclude_patterns)
    logger.info(f"Exclusion patterns: {exclusion_config}")

    _connection_args: ConnectionConfig = connection_args if connection_args is not None else {}
    db = SnowflakeDB(_connection_args)
    db.start_init_connection()
    server = Server("snowflake-manager")
    write_detector = SQLWriteDetector()

    tables_info = (await prefetch_tables(db, _connection_args)) if prefetch else {}

    all_tools = [
        Tool(
            name="list_databases",
            description="List all available databases in Snowflake",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=handle_list_databases,
        ),
        Tool(
            name="list_schemas",
            description="List all schemas in a database",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name to list schemas from",
                    },
                },
                "required": ["database"],
            },
            handler=handle_list_schemas,
        ),
        Tool(
            name="list_tables",
            description="List all tables in a specific database and schema",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {"type": "string", "description": "Database name"},
                    "schema": {"type": "string", "description": "Schema name"},
                },
                "required": ["database", "schema"],
            },
            handler=handle_list_tables,
        ),
        Tool(
            name="describe_table",
            description="Get the schema information for a specific table",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Fully qualified table name in the format 'database.schema.table'",
                    },
                },
                "required": ["table_name"],
            },
            handler=handle_describe_table,
        ),
        Tool(
            name="read_query",
            description="Execute a SELECT query.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SELECT SQL query to execute",
                    }
                },
                "required": ["query"],
            },
            handler=handle_read_query,
        ),
        Tool(
            name="append_insight",
            description="Add a data insight to the memo",
            input_schema={
                "type": "object",
                "properties": {
                    "insight": {
                        "type": "string",
                        "description": "Data insight discovered from analysis",
                    }
                },
                "required": ["insight"],
            },
            handler=handle_append_insight,
            tags=["resource_based"],
        ),
        Tool(
            name="write_query",
            description="Execute an INSERT, UPDATE, or DELETE query on the Snowflake database",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "SQL query to execute"}},
                "required": ["query"],
            },
            handler=handle_write_query,
            tags=["write"],
        ),
        Tool(
            name="create_table",
            description="Create a new table in the Snowflake database",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "CREATE TABLE SQL statement",
                    }
                },
                "required": ["query"],
            },
            handler=handle_create_table,
            tags=["write"],
        ),
    ]

    exclude_tags = []
    if not allow_write:
        exclude_tags.append("write")
    allowed_tools = [
        tool
        for tool in all_tools
        if tool.name not in exclude_tools and not any(tag in exclude_tags for tag in tool.tags)
    ]

    logger.info("Allowed tools: %s", [tool.name for tool in allowed_tools])

    _register_handlers(
        server,
        db,
        tables_info,
        allowed_tools,
        exclude_tools,
        exclusion_config,
        allow_write,
        write_detector,
        exclude_json_results,
    )

    # Start server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="snowflake",
                server_version=importlib.metadata.version("mcp-snowflake-server-nsp"),
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

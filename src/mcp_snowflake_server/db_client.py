import asyncio
import logging
import re
import time
import uuid
from datetime import date, datetime, time as time_
from decimal import Decimal
from typing import Any, cast

import pandas as pd
from snowflake.snowpark import Session


# Type alias for values returned by Snowflake query results.
# Covers Snowflake SQL → Python mappings via Session.sql(...).to_pandas():
#   BOOLEAN            → bool
#   INTEGER / NUMBER   → int | Decimal
#   FLOAT / DOUBLE     → float
#   VARCHAR / TEXT     → str
#   DATE               → date
#   TIMESTAMP_*        → datetime | pd.Timestamp (pandas/Arrow path)
#   TIME               → datetime.time
#   BINARY             → bytes | bytearray
#   VARIANT / OBJECT / ARRAY → str  (JSON-encoded; parse with json.loads if needed)
#   NULL               → None
type SnowflakeValue = (
    str
    | int
    | float
    | bool
    | Decimal
    | date
    | datetime
    | time_
    | pd.Timestamp
    | bytes
    | bytearray
    | None
)  # noqa: E501
type ConnectionConfig = dict[str, Any]

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def _validate_identifier(name: str, label: str) -> str:
    """Validate and uppercase a Snowflake SQL identifier to prevent injection."""
    if not _IDENT_RE.match(name):
        raise ValueError(f"Invalid Snowflake identifier for {label}: {name!r}")
    return name.upper()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("mcp_snowflake_server")


class SnowflakeDB:
    AUTH_EXPIRATION_TIME = 1800

    def __init__(self, connection_config: ConnectionConfig) -> None:
        self.connection_config = connection_config
        self.session: Session | None = None
        self.insights: list[str] = []
        self.auth_time: float = 0.0
        self.init_task: asyncio.Task[None] | None = None  # To store the task reference

    async def _init_database(self) -> None:
        """Initialize connection to the Snowflake database"""
        try:
            # Create session without setting specific database and schema
            session = Session.builder.configs(self.connection_config).create()

            # Set initial warehouse if provided, but don't set database or schema
            if "warehouse" in self.connection_config:
                warehouse = self.connection_config["warehouse"]
                if not isinstance(warehouse, str):
                    raise ValueError("'warehouse' connection config must be a string")
                session.sql(f"USE WAREHOUSE {_validate_identifier(warehouse, 'warehouse')}")

            self.session = session
            self.auth_time = time.time()
        except Exception as e:
            raise ValueError(f"Failed to connect to Snowflake database: {e}")

    def start_init_connection(self) -> asyncio.Task[None]:
        """Start database initialization in the background"""
        # Create a task that runs in the background
        loop = asyncio.get_event_loop()
        self.init_task = loop.create_task(self._init_database())
        return self.init_task

    async def execute_query(self, query: str) -> tuple[list[dict[str, SnowflakeValue]], str]:
        """Execute a SQL query and return results as a list of dictionaries"""
        # If init_task exists and isn't done, wait for it to complete
        if self.init_task and not self.init_task.done():
            await self.init_task
        # If session doesn't exist or has expired, initialize it and wait
        elif not self.session or time.time() - self.auth_time > self.AUTH_EXPIRATION_TIME:
            await self._init_database()

        logger.debug(f"Executing query: {query}")
        try:
            assert self.session is not None
            result = self.session.sql(query).to_pandas()
            result_rows = cast(list[dict[str, SnowflakeValue]], result.to_dict(orient="records"))
            data_id = str(uuid.uuid4())

            return result_rows, data_id

        except Exception as e:
            logger.error(f'Database error executing "{query}": {e}')
            raise

    def add_insight(self, insight: str) -> None:
        """Add a new insight to the collection"""
        self.insights.append(insight)

    def get_memo(self) -> str:
        """Generate a formatted memo from collected insights"""
        if not self.insights:
            return "No data insights have been discovered yet."

        memo = "📊 Data Intelligence Memo 📊\n\n"
        memo += "Key Insights Discovered:\n\n"
        memo += "\n".join(f"- {insight}" for insight in self.insights)

        if len(self.insights) > 1:
            memo += f"\n\nSummary:\nAnalysis has revealed {len(self.insights)} key data insights that suggest opportunities for strategic optimization and growth."

        return memo

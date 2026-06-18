import sqlparse
from sqlparse.sql import TokenList
from sqlparse.tokens import DDL, DML, Keyword


class SQLWriteDetector:
    def __init__(self) -> None:
        # Define sets of keywords that indicate write operations
        self.dml_write_keywords = {
            "INSERT",
            "UPDATE",
            "DELETE",
            "MERGE",
            "UPSERT",
            "REPLACE",
        }

        self.ddl_keywords = {"CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME"}

        self.dcl_keywords = {"GRANT", "REVOKE"}

        # Combine all write keywords
        self.write_keywords = self.dml_write_keywords | self.ddl_keywords | self.dcl_keywords

        # Keywords that trigger dynamic SQL execution; the actual payload lives in a
        # string literal or runtime variable that the parser cannot inspect, so we
        # treat their presence as a write operation (conservative / deny-by-default).
        self.dynamic_execution_keywords = {"EXECUTE", "CALL"}

    def analyze_query(self, sql_query: str) -> dict:
        """
        Analyze a SQL query to determine if it contains write operations.

        Args:
            sql_query: The SQL query string to analyze

        Returns:
            Dictionary containing analysis results
        """
        # Parse the SQL query
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return {
                "contains_write": False,
                "write_operations": set(),
                "has_cte_write": False,
            }

        # Initialize result tracking
        found_operations = set()
        has_cte_write = False

        # Analyze each statement in the query
        for statement in parsed:
            # Check for write operations in CTEs (WITH clauses)
            if self._has_cte(statement):
                cte_write = self._analyze_cte(statement)
                if cte_write:
                    has_cte_write = True
                    found_operations.add("CTE_WRITE")

            # Analyze the main query
            operations = self._find_write_operations(statement)
            found_operations.update(operations)

            # Detect dynamic execution commands (EXECUTE IMMEDIATE / EXECUTE TASK / CALL).
            # These can hide arbitrary write SQL in string literals or runtime variables
            # that the keyword scanner cannot inspect, so we block them unconditionally.
            dynamic_ops = self._find_dynamic_execution(statement)
            found_operations.update(dynamic_ops)

        return {
            "contains_write": bool(found_operations) or has_cte_write,
            "write_operations": found_operations,
            "has_cte_write": has_cte_write,
        }

    def _has_cte(self, statement: TokenList) -> bool:
        """Check if the statement has a WITH clause."""
        return any(token.is_keyword and token.normalized == "WITH" for token in statement.tokens)

    def _analyze_cte(self, statement: TokenList) -> bool:
        """
        Analyze CTEs (WITH clauses) for write operations.
        Returns True if any CTE contains a write operation.
        """
        in_cte = False
        for token in statement.tokens:
            if token.is_keyword and token.normalized == "WITH":
                in_cte = True
            elif in_cte:
                if any(write_kw in token.normalized for write_kw in self.write_keywords):
                    return True
        return False

    def _find_dynamic_execution(self, statement: TokenList) -> set[str]:
        """
        Detect dynamic-SQL execution commands (EXECUTE IMMEDIATE, EXECUTE TASK, CALL).

        sqlparse hides the executed payload inside a string literal or a Name token
        that is resolved only at runtime, so keyword-based scanning is insufficient.
        This method flags the dynamic-execution command itself as a write operation.

        Returns a set of labels such as {"EXECUTE IMMEDIATE"} or {"CALL"}.
        """
        operations: set[str] = set()
        flat = list(statement.flatten())
        i = 0
        while i < len(flat):
            token = flat[i]
            if token.ttype is Keyword:
                normalized = token.normalized.upper()
                if normalized == "EXECUTE":
                    # Look ahead past whitespace for a qualifier (IMMEDIATE / TASK).
                    j = i + 1
                    while j < len(flat) and flat[j].is_whitespace:
                        j += 1
                    if j < len(flat) and flat[j].normalized.upper() in ("IMMEDIATE", "TASK"):
                        operations.add(f"EXECUTE {flat[j].normalized.upper()}")
                        i = j + 1
                        continue
                    operations.add("EXECUTE")
                elif normalized == "CALL":
                    operations.add("CALL")
            i += 1
        return operations

    def _find_write_operations(self, statement: TokenList) -> set[str]:
        """
        Find all write operations in a statement.
        Returns a set of found write operation keywords.
        """
        operations = set()

        for token in statement.tokens:
            # Skip comments and whitespace
            if token.is_whitespace or token.ttype in (sqlparse.tokens.Comment,):
                continue

            # Check if token is a keyword
            if token.ttype in (Keyword, DML, DDL):
                normalized = token.normalized.upper()
                if normalized in self.write_keywords:
                    operations.add(normalized)

            # Recursively check child tokens
            if isinstance(token, TokenList):
                child_ops = self._find_write_operations(token)
                operations.update(child_ops)

        return operations

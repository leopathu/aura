from typing import List, Set, Tuple, Optional
import sqlglot
from sqlglot import exp
from app.core.config import settings

class SQLValidationError(Exception):
    pass

class SQLSecurityLayer:
    """AST-based SQL Safety Validator & Rewriter using sqlglot."""

    FORBIDDEN_EXPRESSIONS = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Alter,
        exp.Create,
        exp.Command,
        exp.Transaction,
        exp.Commit,
        exp.Rollback,
        exp.TruncateTable,
    )

    @classmethod
    def parse_and_validate(cls, sql_query: str) -> Tuple[exp.Expression, Set[str], Set[str]]:
        """
        Parses SQL, ensures it is STRICTLY a read-only SELECT query,
        and extracts referenced table names and column names.
        """
        clean_query = sql_query.strip()
        if not clean_query:
            raise SQLValidationError("Query is empty.")

        try:
            # Parse multiple statements if separated by semicolon
            expressions = sqlglot.parse(clean_query)
        except Exception as e:
            raise SQLValidationError(f"SQL Syntax Error: {str(e)}")

        if not expressions:
            raise SQLValidationError("No valid SQL statements found.")

        if len(expressions) > 1:
            raise SQLValidationError("Multiple statements in a single query are forbidden.")

        expression = expressions[0]

        # 1. Enforce SELECT only
        if not isinstance(expression, (exp.Select, exp.Union)):
            raise SQLValidationError(
                f"Forbidden statement type: {expression.key.upper()}. Only read-only SELECT queries are allowed."
            )

        # 2. Check for nested forbidden expressions (e.g. SELECT into, nested DML)
        for forbidden in cls.FORBIDDEN_EXPRESSIONS:
            if expression.find(forbidden):
                raise SQLValidationError(
                    f"Forbidden SQL operation detected: {forbidden.__name__}. Only read-only queries are permitted."
                )

        # 3. Extract tables
        tables: Set[str] = set()
        for table in expression.find_all(exp.Table):
            if table.name:
                tables.add(table.name.lower())

        # 4. Extract columns
        columns: Set[str] = set()
        for col in expression.find_all(exp.Column):
            if col.name:
                columns.add(col.name.lower())

        return expression, tables, columns

    @classmethod
    def enforce_limits_and_safety(
        cls,
        expression: exp.Expression,
        max_rows: int = settings.SQL_MAX_ROWS,
        default_limit: int = settings.SQL_DEFAULT_LIMIT,
        row_filters: Optional[List[str]] = None,
    ) -> str:
        """
        Ensures a query has a safety LIMIT and injects row-level policy filters if present.
        """
        # 1. Inject row-level policy filters if provided
        if row_filters:
            for filter_expr in row_filters:
                try:
                    parsed_cond = sqlglot.parse_one(filter_expr, into=exp.Condition)
                    expression = expression.where(parsed_cond)
                except Exception:
                    pass

        # 2. Enforce LIMIT
        limit_node = expression.find(exp.Limit)
        if limit_node:
            try:
                curr_limit = int(limit_node.expression.this)
                if curr_limit > max_rows:
                    limit_node.expression.this = str(max_rows)
            except Exception:
                limit_node.expression.this = str(default_limit)
        else:
            expression = expression.limit(default_limit)

        return expression.sql()

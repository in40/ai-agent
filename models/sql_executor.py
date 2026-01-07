from utils.database import DatabaseManager
from config.settings import TERMINATE_ON_POTENTIALLY_HARMFUL_SQL, ENABLE_SCREEN_LOGGING
import logging

logger = logging.getLogger(__name__)

class SQLExecutor:
    def __init__(self, database_manager: DatabaseManager):
        self.db_manager = database_manager

    def execute_sql_and_get_results(self, sql_query):
        """
        Execute the SQL query and return the results
        """
        try:
            # Check for potentially harmful commands
            is_safe, issues = self.check_for_harmful_commands(sql_query)

            if not is_safe:
                warning_msg = f"Potential security issue detected in SQL query: {', '.join(issues)}"
                if ENABLE_SCREEN_LOGGING:
                    logger.warning(warning_msg)
                print(f"WARNING: {warning_msg}")

                # Only terminate if the configuration parameter is enabled
                if TERMINATE_ON_POTENTIALLY_HARMFUL_SQL:
                    raise ValueError(f"SQL query blocked due to security concerns: {', '.join(issues)}")

            # Execute the query
            results = self.db_manager.execute_query(sql_query)

            return results

        except Exception as e:
            if ENABLE_SCREEN_LOGGING:
                logger.error(f"Error executing SQL query: {str(e)}")
            raise

    def check_for_harmful_commands(self, query):
        """
        Check the SQL query for potentially harmful commands
        Returns (is_safe: bool, issues: list)
        """
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower().strip()

        issues = []

        # Check for potentially harmful commands
        harmful_commands = [
            'drop', 'delete', 'truncate', 'alter', 'create', 'insert',
            'update', 'grant', 'revoke', 'exec', 'execute', 'merge'
        ]

        # Check if the query starts with SELECT (for basic safety)
        if not query_lower.strip().startswith('select'):
            issues.append("Query does not start with SELECT")

        # Check for harmful commands anywhere in the query
        for command in harmful_commands:
            if command in query_lower:
                # Allow 'select' but not other harmful commands
                if command != 'select':
                    issues.append(f"Contains potentially harmful command: {command}")

        # Check for other potentially harmful patterns
        harmful_patterns = [
            'union select',  # Could indicate SQL injection
            'information_schema',  # Could be used to extract schema info
            'pg_',  # PostgreSQL system tables/functions
            'sqlite_',  # SQLite system tables/functions
            'xp_',  # SQL Server extended procedures
            'sp_',  # SQL Server stored procedures
        ]

        for pattern in harmful_patterns:
            if pattern in query_lower:
                issues.append(f"Contains potentially harmful pattern: {pattern}")

        return len(issues) == 0, issues
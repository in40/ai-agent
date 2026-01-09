import re
from utils.multi_database_manager import multi_db_manager
from config.settings import TERMINATE_ON_POTENTIALLY_HARMFUL_SQL, ENABLE_SCREEN_LOGGING
import logging

logger = logging.getLogger(__name__)

class SQLExecutor:
    def __init__(self, database_manager=None):
        # Use the global multi-database manager if none provided
        self.db_manager = database_manager or multi_db_manager

    def execute_sql_and_get_results(self, sql_query, db_name="default"):
        """
        Execute the SQL query and return the results
        If db_name is "all_databases", execute on all databases and aggregate results
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

            # If db_name is "all_databases", execute on all databases and aggregate results
            if db_name == "all_databases":
                return self._execute_on_appropriate_databases(sql_query)

            # Execute the query on the specified database
            results = self.db_manager.execute_query(db_name, sql_query)

            return results

        except Exception as e:
            if ENABLE_SCREEN_LOGGING:
                logger.error(f"Error executing SQL query: {str(e)}")
            raise

    def _execute_on_appropriate_databases(self, sql_query):
        """
        Execute the SQL query on databases that contain the referenced tables and aggregate results
        """
        # Extract table names from the SQL query
        table_names = self._extract_table_names(sql_query)

        all_databases = self.db_manager.list_databases()
        combined_results = []

        for db_name in all_databases:
            try:
                # Get the schema for this database to check if the tables exist
                schema = self.db_manager.get_schema_dump(db_name)

                # Check if any of the table names in the query exist in this database
                tables_exist_in_db = any(table_name in schema for table_name in table_names)

                if tables_exist_in_db:
                    # Execute the query on this database
                    results = self.db_manager.execute_query(db_name, sql_query)

                    # Add database identifier to each result row to distinguish sources
                    for result in results:
                        result["_source_database"] = db_name

                    # Combine results from all databases
                    combined_results.extend(results)

                    logger.info(f"Query executed on '{db_name}' database, got {len(results)} results")
                else:
                    logger.info(f"Skipping '{db_name}' database - none of the tables {table_names} exist in this database")

            except Exception as e:
                error_msg = f"SQL execution error on '{db_name}' database: {str(e)}"
                logger.error(error_msg)
                # Continue with other databases even if one fails

        return combined_results

    def _extract_table_names(self, sql_query):
        """
        Extract table names from a SQL query
        This is a simplified implementation that handles basic SELECT statements
        """
        # Convert to uppercase for easier parsing
        query_upper = sql_query.upper()

        # Find table names in FROM clause
        # This regex looks for FROM followed by table names (optionally with aliases)
        from_matches = re.findall(r'FROM\s+([A-Z_][A-Z0-9_]*|\[[A-Z_][A-Z0-9_]*\]|[`"][A-Z_][A-Z0-9_]*[`"])(?:\s+|$)', query_upper)

        # Find table names in JOIN clauses
        join_matches = re.findall(r'(?:JOIN|INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN)\s+([A-Z_][A-Z0-9_]*|\[[A-Z_][A-Z0-9_]*\]|[`"][A-Z_][A-Z0-9_]*[`"])(?:\s+|$)', query_upper)

        # Find table names in other contexts (like INSERT INTO, UPDATE, etc.)
        insert_matches = re.findall(r'INSERT\s+INTO\s+([A-Z_][A-Z0-9_]*|\[[A-Z_][A-Z0-9_]*\]|[`"][A-Z_][A-Z0-9_]*[`"])(?:\s+|$)', query_upper)
        update_matches = re.findall(r'UPDATE\s+([A-Z_][A-Z0-9_]*|\[[A-Z_][A-Z0-9_]*\]|[`"][A-Z_][A-Z0-9_]*[`"])(?:\s+|$)', query_upper)

        # Combine all matches and clean them up
        all_matches = from_matches + join_matches + insert_matches + update_matches
        table_names = []

        for match in all_matches:
            # Remove quotes or brackets if present
            cleaned = match.strip('[]`"')
            table_names.append(cleaned)

        # Remove duplicates while preserving order
        unique_table_names = []
        for name in table_names:
            if name not in unique_table_names:
                unique_table_names.append(name)

        return unique_table_names

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
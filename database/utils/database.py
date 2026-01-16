import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.settings import DATABASE_URL
import logging
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url=None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url)
        # Add schema caching with timestamp
        self._schema_cache = None
        self._schema_cache_time = 0
        self._schema_cache_duration = 300  # Cache for 5 minutes (300 seconds)

    def get_schema_dump(self, force_refresh=False):
        """
        Get a dump of the database schema (table names, column names, types, etc.)
        Supports both PostgreSQL and SQLite
        """
        current_time = time.time()

        # Check if we have a cached schema and it's still valid (not expired)
        if (not force_refresh and
            self._schema_cache is not None and
            (current_time - self._schema_cache_time) < self._schema_cache_duration):
            logger.info("Returning cached schema dump")
            return self._schema_cache

        try:
            with self.engine.connect() as connection:
                # Determine database dialect
                dialect = self.engine.dialect.name

                if dialect == 'postgresql':
                    # PostgreSQL-specific schema query
                    result = connection.execute(text("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                    """))
                    tables = [row[0] for row in result.fetchall()]

                    schema_info = {}

                    for table in tables:
                        # Validate table name to prevent SQL injection
                        # Only allow alphanumeric characters, underscores, and hyphens
                        if not re.match(r'^[a-zA-Z0-9_-]+$', table):
                            logger.warning(f"Skipping table with invalid name: {table}")
                            continue

                        # Get column information for each table
                        # Note: We can't use parameterized queries for table names in this context
                        # but we've validated the table name above to prevent injection
                        columns_result = connection.execute(text(f"""
                            SELECT
                                c.column_name,
                                c.data_type,
                                c.is_nullable,
                                pgd.description AS column_comment
                            FROM information_schema.columns c
                            LEFT JOIN pg_catalog.pg_statio_all_tables st ON c.table_name = st.relname
                            LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
                            WHERE c.table_name = '{table}'
                            ORDER BY c.ordinal_position
                        """))

                        columns = []
                        for col in columns_result.fetchall():
                            columns.append({
                                'name': col[0],
                                'type': col[1],
                                'nullable': col[2] == 'YES',
                                'comment': col[3]  # Column comment
                            })

                        # Get table comment
                        table_comment_result = connection.execute(text(f"""
                            SELECT pgd.description AS table_comment
                            FROM pg_catalog.pg_statio_all_tables st
                            LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid AND pgd.objsubid = 0
                            WHERE st.relname = '{table}'
                        """))
                        table_comment = table_comment_result.fetchone()

                        schema_info[table] = {
                            'columns': columns,
                            'comment': table_comment[0] if table_comment else None
                        }
                elif dialect == 'sqlite':
                    # SQLite-specific schema query
                    result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                    tables = [row[0] for row in result.fetchall()]

                    # Exclude SQLite system tables
                    tables = [table for table in tables if not table.startswith('sqlite_')]

                    schema_info = {}

                    for table in tables:
                        # Validate table name to prevent SQL injection
                        # Only allow alphanumeric characters, underscores, and hyphens
                        if not re.match(r'^[a-zA-Z0-9_-]+$', table):
                            logger.warning(f"Skipping table with invalid name: {table}")
                            continue

                        # Get column information for each table in SQLite
                        columns_result = connection.execute(text(f"PRAGMA table_info('{table}')"))
                        columns = []
                        for col in columns_result.fetchall():
                            # col[1] is name, col[2] is type, col[3] indicates if not null (1 for not null, 0 for nullable)
                            columns.append({
                                'name': col[1],
                                'type': col[2],
                                'nullable': col[3] == 0,  # 0 in the notnull field means nullable
                                'comment': None  # SQLite doesn't support column comments natively
                            })

                        # For SQLite, try to extract potential comments from the CREATE TABLE statement
                        table_sql_result = connection.execute(text(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"))
                        table_sql_row = table_sql_result.fetchone()
                        table_comment = None
                        if table_sql_row:
                            # Try to extract comment from the CREATE TABLE statement
                            table_sql = table_sql_row[0]

                            # Look for comments in the format: CREATE TABLE ... -- table comment
                            # Split the SQL into lines and check the last non-empty line for a table comment
                            lines = [line.strip() for line in table_sql.split('\n') if line.strip()]
                            if lines:
                                last_line = lines[-1]
                                comment_match = re.search(r'--\s*(.+)$', last_line)
                                if comment_match:
                                    table_comment = comment_match.group(1).strip()

                            # Check for comments in column definitions like: column_name TYPE -- column comment
                            # This is a more complex regex to find column comments
                            for line in table_sql.split('\n'):
                                # Match column definitions that have comments after them
                                # Pattern: column_name TYPE ... -- comment
                                col_comment_match = re.search(r'^\s*["\']?(\w+)["\']?\s+.*--\s*(.+)$', line.strip())
                                if col_comment_match:
                                    col_name = col_comment_match.group(1)
                                    col_comment = col_comment_match.group(2).strip()
                                    # Update the comment for the matching column
                                    for col in columns:
                                        if col['name'] == col_name:
                                            col['comment'] = col_comment

                        schema_info[table] = {
                            'columns': columns,
                            'comment': table_comment
                        }
                else:
                    raise ValueError(f"Unsupported database dialect: {dialect}")

                # Update the cache
                self._schema_cache = schema_info
                self._schema_cache_time = current_time

                return schema_info

        except SQLAlchemyError as e:
            logger.error(f"Error getting schema dump: {str(e)}")
            # If there's an error retrieving the schema, clear the cache
            self._schema_cache = None
            raise

    def clear_schema_cache(self):
        """
        Clear the schema cache to force a fresh retrieval on the next call
        """
        self._schema_cache = None
        self._schema_cache_time = 0
        logger.info("Schema cache cleared")

    def execute_query(self, query):
        """
        Execute a SQL query and return the results
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                # Get column names
                columns = result.keys()
                # Get rows
                rows = result.fetchall()

                # Convert to list of dictionaries
                results = []
                for row in rows:
                    results.append({col: val for col, val in zip(columns, row)})

                return results

        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {str(e)}")
            raise

    def test_connection(self):
        """
        Test the database connection
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False


# Backward compatibility: Create a default instance
default_db_manager = DatabaseManager()
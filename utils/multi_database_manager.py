"""
Utility for managing multiple database connections in the AI Agent application.
This module provides functionality to add, configure, and manage multiple database connections.
"""

import os
import re
from typing import Dict, Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.settings import DATABASE_URL
import logging
import time

logger = logging.getLogger(__name__)


class MultiDatabaseManager:
    """
    Manages multiple database connections for the AI Agent application.
    """
    
    def __init__(self):
        self.databases: Dict[str, DatabaseManager] = {}
        # Add the default database if DATABASE_URL is configured
        if DATABASE_URL:
            self.add_database("default", DATABASE_URL)
    
    def add_database(self, name: str, database_url: str, **kwargs) -> bool:
        """
        Add a new database connection to the manager.
        
        Args:
            name: A unique identifier for the database
            database_url: The connection URL for the database
            **kwargs: Additional options for the database connection
            
        Returns:
            bool: True if the database was added successfully, False otherwise
        """
        if not self._is_valid_database_name(name):
            logger.error(f"Invalid database name: {name}")
            return False
            
        if name in self.databases:
            logger.warning(f"Database with name '{name}' already exists. Updating connection.")
        
        try:
            db_manager = DatabaseManager(database_url, **kwargs)
            # Test the connection before adding
            if db_manager.test_connection():
                self.databases[name] = db_manager
                logger.info(f"Successfully added database: {name}")
                return True
            else:
                logger.error(f"Failed to connect to database: {name}")
                return False
        except Exception as e:
            logger.error(f"Error adding database '{name}': {str(e)}")
            return False
    
    def remove_database(self, name: str) -> bool:
        """
        Remove a database connection from the manager.
        
        Args:
            name: The name of the database to remove
            
        Returns:
            bool: True if the database was removed successfully, False otherwise
        """
        if name not in self.databases:
            logger.warning(f"Database '{name}' does not exist in manager")
            return False
        
        del self.databases[name]
        logger.info(f"Successfully removed database: {name}")
        return True
    
    def get_database(self, name: str) -> Optional['DatabaseManager']:
        """
        Get a database manager instance by name.
        
        Args:
            name: The name of the database to retrieve
            
        Returns:
            DatabaseManager: The database manager instance, or None if not found
        """
        return self.databases.get(name)
    
    def list_databases(self) -> List[str]:
        """
        Get a list of all registered database names.
        
        Returns:
            List[str]: A list of database names
        """
        return list(self.databases.keys())
    
    def get_schema_dump(self, db_name: str, force_refresh: bool = False):
        """
        Get the schema dump for a specific database.
        
        Args:
            db_name: The name of the database to get schema for
            force_refresh: Whether to force a refresh of the schema cache
            
        Returns:
            The schema dump for the specified database
        """
        db_manager = self.get_database(db_name)
        if not db_manager:
            raise ValueError(f"Database '{db_name}' not found in manager")
        
        return db_manager.get_schema_dump(force_refresh=force_refresh)
    
    def execute_query(self, db_name: str, query: str):
        """
        Execute a query on a specific database.
        
        Args:
            db_name: The name of the database to execute the query on
            query: The SQL query to execute
            
        Returns:
            The results of the query
        """
        db_manager = self.get_database(db_name)
        if not db_manager:
            raise ValueError(f"Database '{db_name}' not found in manager")
        
        return db_manager.execute_query(query)
    
    def test_connection(self, db_name: str) -> bool:
        """
        Test the connection to a specific database.
        
        Args:
            db_name: The name of the database to test
            
        Returns:
            bool: True if the connection is successful, False otherwise
        """
        db_manager = self.get_database(db_name)
        if not db_manager:
            logger.error(f"Database '{db_name}' not found in manager")
            return False
        
        return db_manager.test_connection()
    
    def _is_valid_database_name(self, name: str) -> bool:
        """
        Validate that a database name is valid (alphanumeric + underscore/hyphen).
        
        Args:
            name: The database name to validate
            
        Returns:
            bool: True if the name is valid, False otherwise
        """
        if not name:
            return False
        # Allow alphanumeric characters, underscores, and hyphens
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))


class DatabaseManager:
    """
    Enhanced DatabaseManager that supports single database operations.
    This is a modified version of the original DatabaseManager to work with the MultiDatabaseManager.
    """
    
    def __init__(self, database_url: str, **kwargs):
        self.database_url = database_url
        self.engine = create_engine(self.database_url, **kwargs)
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
                    result = connection.execute(text(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                    ))
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
                        columns_query = f"""
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
                        """
                        columns_result = connection.execute(text(columns_query))

                        columns = []
                        for col in columns_result.fetchall():
                            columns.append({
                                'name': col[0],
                                'type': col[1],
                                'nullable': col[2] == 'YES',
                                'comment': col[3]  # Column comment
                            })

                        # Get table comment
                        table_comment_query = f"""
                            SELECT pgd.description AS table_comment
                            FROM pg_catalog.pg_statio_all_tables st
                            LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid AND pgd.objsubid = 0
                            WHERE st.relname = '{table}'
                        """
                        table_comment_result = connection.execute(text(table_comment_query))
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
                        # PRAGMA statements can't use text() wrapper, so we'll handle them separately
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


# Global instance of MultiDatabaseManager for easy access
multi_db_manager = MultiDatabaseManager()


def add_database_from_config():
    """
    Add databases from environment variables or configuration files.
    This function looks for environment variables in the format:
    - DB_{NAME}_TYPE
    - DB_{NAME}_USERNAME
    - DB_{NAME}_PASSWORD
    - DB_{NAME}_HOSTNAME
    - DB_{NAME}_PORT
    - DB_{NAME}_NAME
    - DB_{NAME}_URL
    """
    # Look for environment variables that define additional databases
    for key, value in os.environ.items():
        if key.startswith("DB_") and key.endswith("_URL"):
            # Extract the database name from the environment variable name
            db_name = key[3:-4]  # Remove "DB_" prefix and "_URL" suffix
            if db_name and db_name != "":  # Make sure we have a valid name
                multi_db_manager.add_database(db_name.lower(), value)

    # Also check for databases defined with individual components
    for key, value in os.environ.items():
        if key.startswith("DB_") and "_TYPE" in key:
            # Extract the database name from the environment variable name
            parts = key.split('_')
            if len(parts) >= 3:
                db_name = '_'.join(parts[1:-1])  # Everything between "DB_" and "_TYPE"
                if db_name and db_name != "":
                    # Construct the database URL from individual components
                    db_type = os.getenv(f"DB_{db_name}_TYPE")
                    db_username = os.getenv(f"DB_{db_name}_USERNAME")
                    db_password = os.getenv(f"DB_{db_name}_PASSWORD", "")
                    db_hostname = os.getenv(f"DB_{db_name}_HOSTNAME", "localhost")
                    db_port = os.getenv(f"DB_{db_name}_PORT", "5432")
                    db_name_env = os.getenv(f"DB_{db_name}_NAME")

                    if all([db_type, db_username, db_name_env]):
                        db_url = f"{db_type}://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name_env}"
                        multi_db_manager.add_database(db_name.lower(), db_url)


def reload_database_config():
    """
    Reload database configurations from environment variables.
    This function clears the existing databases and reloads them from the current environment.
    """
    # Clear all existing databases except the default one if it exists
    current_databases = list(multi_db_manager.databases.keys())

    # Remove all databases except the default one
    for db_name in current_databases:
        if db_name != "default":
            multi_db_manager.remove_database(db_name)

    # Re-add the default database if DATABASE_URL is configured
    from config.settings import DATABASE_URL
    if DATABASE_URL:
        multi_db_manager.add_database("default", DATABASE_URL)

    # Add databases from environment variables again
    add_database_from_config()


# Initialize databases from environment variables when module is loaded
add_database_from_config()
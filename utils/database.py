import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.settings import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url=None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url)
    
    def get_schema_dump(self):
        """
        Get a dump of the database schema (table names, column names, types, etc.)
        """
        try:
            with self.engine.connect() as connection:
                # Get all table names
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result.fetchall()]
                
                schema_info = {}
                
                for table in tables:
                    # Get column information for each table
                    columns_result = connection.execute(text(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = '{table}'
                        ORDER BY ordinal_position
                    """))
                    
                    columns = []
                    for col in columns_result.fetchall():
                        columns.append({
                            'name': col[0],
                            'type': col[1],
                            'nullable': col[2] == 'YES'
                        })
                    
                    schema_info[table] = columns
                
                return schema_info
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting schema dump: {str(e)}")
            raise
    
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
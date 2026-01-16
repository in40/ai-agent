#!/usr/bin/env python3
"""
Debug script to understand how the validation works
"""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.sql_executor import SQLExecutor
from database.utils.multi_database_manager import multi_db_manager
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def debug_validation():
    """
    Debug the validation process
    """
    print("Debugging validation process...")
    
    # Initialize the SQL executor
    executor = SQLExecutor()
    
    # Get the first available database
    db_names = multi_db_manager.list_databases()
    if not db_names:
        print("No databases available for testing")
        return False
        
    test_db = db_names[0]
    print(f"Using database: {test_db}")
    
    # Get schema to find a valid table and column
    schema = multi_db_manager.get_schema_dump(test_db)
    if not schema:
        print("No schema available in the database")
        return False
        
    # Get the first table and its first column
    table_name = next(iter(schema.keys()))
    table_info = schema[table_name]
    
    if isinstance(table_info, list):
        # Old format
        column_name = table_info[0]['name'] if table_info else None
    else:
        # New format
        columns = table_info.get('columns', [])
        column_name = columns[0]['name'] if columns else None
        
    if not column_name:
        print("No columns available in the table")
        return False
    
    print(f"Table: {table_name}, Column: {column_name}")
    
    # Test the problematic query
    query = f"SELECT t.non_existent_column FROM {table_name} t LIMIT 1"
    print(f"Testing query: {query}")
    
    # Call the validation function directly
    result = executor._validate_table_existence(query, test_db)
    print(f"Validation result: {result}")
    
    # Also test with a valid query
    valid_query = f"SELECT t.{column_name} FROM {table_name} t LIMIT 1"
    print(f"Testing valid query: {valid_query}")
    valid_result = executor._validate_table_existence(valid_query, test_db)
    print(f"Valid query validation result: {valid_result}")
    
    return True

if __name__ == "__main__":
    debug_validation()
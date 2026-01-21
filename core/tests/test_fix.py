#!/usr/bin/env python3
"""
Test script to verify the fix for SQL query validation.
This script tests that the SQL executor properly validates both table and column existence.
"""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.sql_executor import SQLExecutor
from database.utils.multi_database_manager import multi_db_manager
from config.settings import DATABASE_URL

def test_table_and_column_validation():
    """
    Test that the SQL executor properly validates both table and column existence
    """
    print("Testing table and column validation...")
    
    # Initialize the SQL executor
    executor = SQLExecutor()
    
    # Test 1: Valid table and column
    print("\nTest 1: Valid table and column")
    try:
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
            
        # Create a valid query
        valid_query = f"SELECT {column_name} FROM {table_name} LIMIT 1"
        print(f"Testing valid query: {valid_query}")
        
        # This should pass validation
        is_valid = executor._validate_table_existence(valid_query, test_db)
        print(f"Validation result: {is_valid}")
        if not is_valid:
            print("ERROR: Valid query failed validation!")
            return False
        else:
            print("SUCCESS: Valid query passed validation")
            
    except Exception as e:
        print(f"Error in Test 1: {e}")
        return False
    
    # Test 2: Invalid table name
    print("\nTest 2: Invalid table name")
    try:
        invalid_table_query = "SELECT name FROM non_existent_table LIMIT 1"
        print(f"Testing invalid table query: {invalid_table_query}")
        
        # This should fail validation
        is_valid = executor._validate_table_existence(invalid_table_query, test_db)
        print(f"Validation result: {is_valid}")
        if is_valid:
            print("ERROR: Invalid table query passed validation!")
            return False
        else:
            print("SUCCESS: Invalid table query failed validation as expected")
            
    except Exception as e:
        print(f"Error in Test 2: {e}")
        return False
    
    # Test 3: Invalid column name with table alias (this should be caught by validation)
    print("\nTest 3: Invalid column name with table alias")
    try:
        # Use a real table but a fake column with an alias (this is the pattern that caused the original error)
        invalid_column_query = f"SELECT t.non_existent_column FROM {table_name} t LIMIT 1"
        print(f"Testing invalid column query: {invalid_column_query}")

        # This should fail validation because we're using the qualified form "t.non_existent_column"
        is_valid = executor._validate_table_existence(invalid_column_query, test_db)
        print(f"Validation result: {is_valid}")
        if is_valid:
            print("ERROR: Invalid column query passed validation!")
            return False
        else:
            print("SUCCESS: Invalid column query failed validation as expected")

    except Exception as e:
        print(f"Error in Test 3: {e}")
        return False
    
    # Test 4: Query with table alias and valid column
    print("\nTest 4: Query with table alias and valid column")
    try:
        alias_query = f"SELECT t.{column_name} FROM {table_name} t LIMIT 1"
        print(f"Testing alias query: {alias_query}")
        
        # This should pass validation
        is_valid = executor._validate_table_existence(alias_query, test_db)
        print(f"Validation result: {is_valid}")
        if not is_valid:
            print("ERROR: Valid alias query failed validation!")
            return False
        else:
            print("SUCCESS: Valid alias query passed validation")
            
    except Exception as e:
        print(f"Error in Test 4: {e}")
        return False
    
    # Test 5: Query with table alias and invalid column
    print("\nTest 5: Query with table alias and invalid column")
    try:
        invalid_alias_query = f"SELECT t.non_existent_column FROM {table_name} t LIMIT 1"
        print(f"Testing invalid alias query: {invalid_alias_query}")
        
        # This should fail validation
        is_valid = executor._validate_table_existence(invalid_alias_query, test_db)
        print(f"Validation result: {is_valid}")
        if is_valid:
            print("ERROR: Invalid alias query passed validation!")
            return False
        else:
            print("SUCCESS: Invalid alias query failed validation as expected")
            
    except Exception as e:
        print(f"Error in Test 5: {e}")
        return False
    
    print("\nAll tests passed!")
    return True

if __name__ == "__main__":
    success = test_table_and_column_validation()
    if success:
        print("\n✓ All validation tests passed! The fix is working correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)
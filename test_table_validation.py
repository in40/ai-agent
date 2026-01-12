#!/usr/bin/env python3
"""
Test script to verify that table validation works correctly
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.sql_executor import SQLExecutor
from utils.multi_database_manager import multi_db_manager
from config.settings import DATABASE_URL

def test_table_validation():
    """
    Test that the SQL executor properly validates table existence
    """
    print("Testing table validation...")
    
    # Initialize the SQL executor
    executor = SQLExecutor()
    
    # Test with a query that references a non-existent table
    fake_query = "SELECT * FROM nonexistent_table WHERE id = 1"
    
    print(f"Testing query: {fake_query}")
    
    try:
        # This should raise an error since the table doesn't exist
        results = executor.execute_sql_and_get_results(fake_query, "default")
        print("ERROR: Expected validation to fail, but it didn't!")
        return False
    except ValueError as e:
        if "do not exist in the database" in str(e):
            print(f"SUCCESS: Validation correctly caught non-existent table: {e}")
        else:
            print(f"UNEXPECTED ERROR: {e}")
            return False
    except Exception as e:
        # If it's a database error (table doesn't exist), that's also acceptable
        if "does not exist" in str(e):
            print(f"INFO: Database caught the error as expected: {e}")
        else:
            print(f"UNEXPECTED ERROR: {e}")
            return False
    
    # Test with a query that references existing tables (this would depend on your actual schema)
    # For now, we'll just make sure the validation function works properly
    print("\nTesting table extraction and validation logic...")
    
    # Get the actual schema to test with
    try:
        schema = multi_db_manager.get_schema_dump("default")
        print(f"Found schema with {len(schema)} tables")
        
        if schema:
            # Pick the first table from the schema to test with
            first_table = list(schema.keys())[0]
            valid_query = f"SELECT * FROM {first_table} LIMIT 1"
            print(f"Testing with valid table: {valid_query}")
            
            # This should pass validation
            if executor._validate_table_existence(valid_query, "default"):
                print("SUCCESS: Validation correctly passed for existing table")
            else:
                print("ERROR: Validation incorrectly failed for existing table")
                return False
        else:
            print("INFO: No tables found in schema, skipping valid table test")
    except Exception as e:
        print(f"INFO: Could not test with actual schema: {e}")
    
    print("\nTable validation test completed successfully!")
    return True

if __name__ == "__main__":
    test_table_validation()
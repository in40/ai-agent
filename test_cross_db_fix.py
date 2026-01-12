#!/usr/bin/env python3
"""
Test script to verify the fix for cross-database query issue
"""

import os
import sys
from utils.multi_database_manager import multi_db_manager
from models.sql_executor import SQLExecutor
from langgraph_agent import run_enhanced_agent


def setup_test_databases():
    """Set up test databases with sample data"""
    print("Setting up test databases...")
    
    # Add a default database if not already present
    if "default" not in multi_db_manager.list_databases():
        # Use a simple SQLite database for testing
        multi_db_manager.add_database("default", "sqlite:///test_default.db")
    
    # Add an analytics database if not already present
    if "analytics" not in multi_db_manager.list_databases():
        # Use a simple SQLite database for testing
        multi_db_manager.add_database("analytics", "sqlite:///test_analytics.db")
    
    # Create sample tables in both databases
    db_executor = SQLExecutor()
    
    # Create contacts table in default database
    try:
        db_executor.db_manager.get_database("default").execute_query(
            "CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)"
        )
        # Insert sample data
        db_executor.db_manager.get_database("default").execute_query(
            "INSERT OR IGNORE INTO contacts VALUES (1, 'John Doe', '555-1234'), (2, 'Jane Smith', '555-5678')"
        )
    except Exception as e:
        print(f"Error setting up default database: {e}")
    
    # Create arrest_data table in analytics database
    try:
        db_executor.db_manager.get_database("analytics").execute_query(
            "CREATE TABLE IF NOT EXISTS arrest_data (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, race TEXT, sex TEXT)"
        )
        # Insert sample data
        db_executor.db_manager.get_database("analytics").execute_query(
            "INSERT OR IGNORE INTO arrest_data VALUES (1, 'John', 'Doe', 'Caucasian', 'Male'), (2, 'Jane', 'Smith', 'Asian', 'Female')"
        )
    except Exception as e:
        print(f"Error setting up analytics database: {e}")


def test_cross_db_query():
    """Test the cross-database query that was causing the issue"""
    print("\nTesting cross-database query...")
    
    # The query that was causing the original error
    problematic_query = """
    SELECT DISTINCT c."name", c."phone" 
    FROM "default"."contacts" c 
    JOIN "analytics"."arrest_data" ad 
    ON LOWER(c."name") LIKE CONCAT('%', LOWER(ad."first_name"), '%') 
    OR LOWER(c."name") LIKE CONCAT('%', LOWER(ad."last_name"), '%') 
    WHERE LOWER(ad."race") LIKE '%asian%' 
    AND LOWER(ad."sex") = 'female' 
    LIMIT 10
    """
    
    print(f"Running query: {problematic_query}")
    
    try:
        sql_executor = SQLExecutor()
        # This should now work with our fix
        results = sql_executor.execute_sql_and_get_results(problematic_query, "all_databases")
        print(f"Success! Got {len(results)} results")
        for result in results:
            print(f"  Result: {result}")
        return True
    except Exception as e:
        print(f"Error executing cross-database query: {e}")
        return False


def test_langgraph_agent():
    """Test the LangGraph agent with a request that generates a cross-database query"""
    print("\nTesting LangGraph agent with cross-database query request...")
    
    try:
        # This request should generate a query that joins tables from different databases
        result = run_enhanced_agent("Find contacts who are Asian females in the arrest records")
        print(f"Agent execution completed with response: {result['final_response']}")
        print(f"Generated SQL: {result['generated_sql']}")
        print(f"Number of results: {len(result['db_results']) if result['db_results'] else 0}")
        
        if result.get('execution_error'):
            print(f"Execution error: {result['execution_error']}")
            return False
        return True
    except Exception as e:
        print(f"Error running LangGraph agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Testing cross-database query fix...")
    
    # Setup test databases
    setup_test_databases()
    
    # Test the direct SQL execution
    success1 = test_cross_db_query()
    
    # Test the LangGraph agent
    success2 = test_langgraph_agent()
    
    print(f"\nTest Results:")
    print(f"Direct SQL execution: {'PASS' if success1 else 'FAIL'}")
    print(f"LangGraph agent: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\nAll tests passed! The cross-database query issue has been fixed.")
        return 0
    else:
        print("\nSome tests failed. The fix may need additional work.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
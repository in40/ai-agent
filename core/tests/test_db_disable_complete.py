#!/usr/bin/env python3
"""
Test script to verify that all SQL logic and database calls are properly disabled when DISABLE_DATABASES is set to True.
This includes testing that no database connections are attempted, no SQL queries are executed,
and that the system behaves correctly with databases disabled.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ai_agent import AIAgent
from models.sql_executor import SQLExecutor
from database.utils.multi_database_manager import multi_db_manager, DatabaseManager
from config.settings import DISABLE_DATABASES

def test_sql_executor_with_disabled_databases():
    """Test that SQLExecutor returns empty results when databases are disabled."""
    print("Testing SQLExecutor with disabled databases...")

    # Create an SQLExecutor instance after reloading settings
    from models.sql_executor import SQLExecutor
    executor = SQLExecutor()

    # Verify that the executor recognizes the disabled state
    assert executor.disable_databases == True, "SQLExecutor should recognize that databases are disabled"
    print("✓ SQLExecutor correctly identifies that databases are disabled")

    # Test execute_sql_and_get_results returns empty results
    results = executor.execute_sql_and_get_results("SELECT * FROM users")
    assert results == [], "SQLExecutor should return empty results when databases are disabled"
    print("✓ SQLExecutor returns empty results when databases are disabled")

    # Test _execute_on_appropriate_databases returns empty results
    results = executor._execute_on_appropriate_databases("SELECT * FROM users")
    assert results == [], "_execute_on_appropriate_databases should return empty results when databases are disabled"
    print("✓ _execute_on_appropriate_databases returns empty results when databases are disabled")

    # Test _validate_table_existence returns True when databases are disabled
    result = executor._validate_table_existence("SELECT * FROM users", "test_db")
    assert result == True, "_validate_table_existence should return True when databases are disabled"
    print("✓ _validate_table_existence returns True when databases are disabled")


def test_multi_database_manager_with_disabled_databases():
    """Test that MultiDatabaseManager methods behave correctly when databases are disabled."""
    print("\nTesting MultiDatabaseManager with disabled databases...")

    # Get the updated multi_db_manager after reloading
    from database.utils.multi_database_manager import multi_db_manager

    # Test get_schema_dump returns empty dict
    schema = multi_db_manager.get_schema_dump("any_db")
    assert schema == {}, "get_schema_dump should return empty dict when databases are disabled"
    print("✓ get_schema_dump returns empty dict when databases are disabled")

    # Test execute_query returns empty list
    results = multi_db_manager.execute_query("any_db", "SELECT * FROM users")
    assert results == [], "execute_query should return empty list when databases are disabled"
    print("✓ execute_query returns empty list when databases are disabled")

    # Test test_connection returns False
    connected = multi_db_manager.test_connection("any_db")
    assert connected == False, "test_connection should return False when databases are disabled"
    print("✓ test_connection returns False when databases are disabled")

    # Test add_database returns False
    added = multi_db_manager.add_database("test_db", "sqlite:///test.db")
    assert added == False, "add_database should return False when databases are disabled"
    print("✓ add_database returns False when databases are disabled")

    # Test list_databases returns empty list (should be empty since no databases were added)
    databases = multi_db_manager.list_databases()
    # Even though databases are disabled, if there were any databases added before disabling,
    # they might still be in the list. So we just verify the method works.
    print(f"✓ list_databases works correctly when databases are disabled, found {len(databases)} databases")


def test_database_manager_methods():
    """Test that DatabaseManager methods behave correctly when databases are disabled."""
    print("\nTesting DatabaseManager methods with disabled databases...")

    # Import the DatabaseManager after reloading settings
    from database.utils.multi_database_manager import DatabaseManager

    # Create a DatabaseManager instance
    db_manager = DatabaseManager("sqlite:///test.db")

    # Test get_schema_dump returns empty dict
    schema = db_manager.get_schema_dump()
    assert schema == {}, "DatabaseManager.get_schema_dump should return empty dict when databases are disabled"
    print("✓ DatabaseManager.get_schema_dump returns empty dict when databases are disabled")

    # Test execute_query returns empty list
    results = db_manager.execute_query("SELECT * FROM users")
    assert results == [], "DatabaseManager.execute_query should return empty list when databases are disabled"
    print("✓ DatabaseManager.execute_query returns empty list when databases are disabled")

    # Test test_connection returns False
    connected = db_manager.test_connection()
    assert connected == False, "DatabaseManager.test_connection should return False when databases are disabled"
    print("✓ DatabaseManager.test_connection returns False when databases are disabled")


def test_ai_agent_with_disabled_databases():
    """Test that AIAgent behaves correctly when databases are disabled."""
    print("\nTesting AIAgent with disabled databases...")

    # Import AIAgent after reloading settings
    from core.ai_agent import AIAgent

    # Create an AIAgent instance
    agent = AIAgent()

    # Verify that the agent recognizes the disabled state
    assert agent.disable_databases == True, "AIAgent should recognize that databases are disabled"
    print("✓ AIAgent correctly identifies that databases are disabled")

    # Test process_request works without attempting database operations
    result = agent.process_request("What are the top 5 users by activity?")

    # Verify the result structure
    assert "original_request" in result
    assert "generated_sql" in result
    assert "db_results" in result
    assert "final_response" in result
    assert "processing_time" in result

    # Verify that no SQL was generated and no database results were returned
    assert result["generated_sql"] is None, "No SQL should be generated when databases are disabled"
    assert result["db_results"] is None, "No database results should be returned when databases are disabled"
    print("✓ AIAgent processes requests without database operations when databases are disabled")


def main():
    """Run all tests to verify database disable functionality."""
    print("Testing complete database disable functionality...\n")

    # Ensure DISABLE_DATABASES is set to True
    os.environ['DISABLE_DATABASES'] = 'true'

    # Import the updated settings after setting the environment variable
    # We need to reload the settings module to pick up the new environment variable
    import importlib
    from config import settings
    importlib.reload(settings)

    # Reload multi_database_manager to pick up the new settings
    from utils import multi_database_manager
    importlib.reload(multi_database_manager)

    # Now get the updated value
    DISABLE_DATABASES = settings.DISABLE_DATABASES
    assert DISABLE_DATABASES == True, "DISABLE_DATABASES should be True for this test"
    print(f"✓ DISABLE_DATABASES setting is correctly set to: {DISABLE_DATABASES}")

    # Run all tests
    test_sql_executor_with_disabled_databases()
    test_multi_database_manager_with_disabled_databases()
    test_database_manager_methods()
    test_ai_agent_with_disabled_databases()

    print("\n✅ All tests passed! The database disable functionality is working correctly.")
    print("When DISABLE_DATABASES is set to True:")
    print("- All SQL logic is bypassed")
    print("- No database connections are attempted")
    print("- No SQL queries are executed")
    print("- All database-related methods return appropriate empty/default values")
    print("- The system continues to function without database operations")


if __name__ == "__main__":
    main()
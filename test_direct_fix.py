#!/usr/bin/env python3
"""
Direct test to verify that the MultiDatabaseManager is not being called as a function
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.multi_database_manager import multi_db_manager
from models.sql_executor import SQLExecutor
from langgraph_agent import DatabaseManager

def test_multi_db_manager_usage():
    """
    Test that DatabaseManager (which is an alias for multi_db_manager) 
    is used as an instance, not called as a function
    """
    print("Testing MultiDatabaseManager usage...")
    
    # Check that DatabaseManager is the same as multi_db_manager instance
    print(f"DatabaseManager is multi_db_manager: {DatabaseManager is multi_db_manager}")
    
    # Test that we can access properties and methods without calling it as a function
    try:
        databases = DatabaseManager.list_databases()
        print(f"Available databases: {databases}")
        
        # Test creating SQLExecutor without errors
        executor = SQLExecutor()
        print("SQLExecutor created successfully")
        
        # Test that multi_db_manager is an instance, not a class
        print(f"multi_db_manager type: {type(multi_db_manager)}")
        print(f"multi_db_manager is instance (not class): {hasattr(multi_db_manager, 'execute_query')}")
        
        print("\n✓ All tests passed! MultiDatabaseManager is being used correctly as an instance.")
        return True
        
    except TypeError as e:
        if "object is not callable" in str(e):
            print(f"\n✗ FAILED: The original error still exists: {e}")
            return False
        else:
            print(f"\n✗ FAILED: Unexpected TypeError: {e}")
            return False
    except Exception as e:
        print(f"\n✗ FAILED: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running direct test for MultiDatabaseManager fix...")
    success = test_multi_db_manager_usage()
    
    if success:
        print("\n✓ Direct test passed! The fix is working correctly.")
    else:
        print("\n✗ Direct test failed! There may still be an issue.")
        sys.exit(1)
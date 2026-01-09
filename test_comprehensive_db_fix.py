#!/usr/bin/env python3
"""
More comprehensive test to verify database configuration fixes.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_functionality():
    """Test basic database manager functionality."""
    print("Testing basic database manager functionality...")
    
    from utils.multi_database_manager import MultiDatabaseManager
    
    # Create a new instance for testing
    db_manager = MultiDatabaseManager()
    
    # Initially, it should only have the default database if DATABASE_URL is set
    initial_dbs = db_manager.list_databases()
    print(f"Initial databases: {initial_dbs}")
    
    # Add a test database
    success = db_manager.add_database("test_db", "sqlite:///:memory:")
    if success:
        print("✓ Successfully added test database")
    else:
        print("✗ Failed to add test database")
        
    # Check databases again
    dbs_after_add = db_manager.list_databases()
    print(f"Databases after adding test: {dbs_after_add}")
    
    if "test_db" in dbs_after_add:
        print("✓ Test database appears in the list")
    else:
        print("✗ Test database does not appear in the list")
        
    # Remove the test database
    success = db_manager.remove_database("test_db")
    if success:
        print("✓ Successfully removed test database")
    else:
        print("✗ Failed to remove test database")
        
    # Check databases after removal
    dbs_after_remove = db_manager.list_databases()
    print(f"Databases after removing test: {dbs_after_remove}")
    
    if "test_db" not in dbs_after_remove:
        print("✓ Test database was properly removed")
    else:
        print("✗ Test database still appears after removal")


def test_global_instance():
    """Test the global database manager instance."""
    print("\nTesting global database manager instance...")
    
    from utils.multi_database_manager import multi_db_manager
    
    # Get initial databases
    initial_dbs = multi_db_manager.list_databases()
    print(f"Global instance initial databases: {initial_dbs}")
    
    # Add a test database
    success = multi_db_manager.add_database("global_test", "sqlite:///:memory:")
    if success:
        print("✓ Successfully added global test database")
    else:
        print("✗ Failed to add global test database")
        
    # Check if it's in the list
    dbs_after_add = multi_db_manager.list_databases()
    if "global_test" in dbs_after_add:
        print("✓ Global test database appears in the list")
    else:
        print("✗ Global test database does not appear in the list")
        
    # Remove the test database
    success = multi_db_manager.remove_database("global_test")
    if success:
        print("✓ Successfully removed global test database")
    else:
        print("✗ Failed to remove global test database")


def test_reload_function():
    """Test the reload function."""
    print("\nTesting reload function...")
    
    from utils.multi_database_manager import multi_db_manager, reload_database_config
    
    # Save original environment
    original_env = dict(os.environ)
    
    try:
        # Add an environment variable for a new database
        os.environ["DB_RELOAD_TEST_URL"] = "sqlite:///:memory:"
        
        # Get initial databases
        initial_dbs = multi_db_manager.list_databases()
        print(f"Databases before reload: {initial_dbs}")
        
        # Reload configuration
        reload_database_config()
        
        # Get databases after reload
        dbs_after_reload = multi_db_manager.list_databases()
        print(f"Databases after reload: {dbs_after_reload}")
        
        if "reload_test" in dbs_after_reload:
            print("✓ Reload test database was loaded after reload")
        else:
            print("✗ Reload test database was not loaded after reload")
            
        # Clean up
        if "reload_test" in dbs_after_reload:
            multi_db_manager.remove_database("reload_test")
            
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
        
        # Reload to reset to original state
        reload_database_config()


if __name__ == "__main__":
    print("Running comprehensive database configuration tests...\n")
    
    test_basic_functionality()
    test_global_instance()
    test_reload_function()
    
    print("\nComprehensive tests completed!")
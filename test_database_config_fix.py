#!/usr/bin/env python3
"""
Test script to verify that the database configuration fixes work correctly.
"""

import os
import tempfile
from pathlib import Path

def test_database_reload():
    """Test that database configurations are properly reloaded."""
    print("Testing database configuration reload functionality...")
    
    # Import after potential changes to environment
    from utils.multi_database_manager import multi_db_manager, reload_database_config
    
    # Initially, there should only be the default database if DATABASE_URL is set
    initial_dbs = multi_db_manager.list_databases()
    print(f"Initial databases: {initial_dbs}")
    
    # Clear any additional databases that might exist
    for db_name in initial_dbs:
        if db_name != "default":
            multi_db_manager.remove_database(db_name)
    
    # Check databases again after cleanup
    dbs_after_cleanup = multi_db_manager.list_databases()
    print(f"Databases after cleanup: {dbs_after_cleanup}")
    
    # Add an environment variable for an additional database
    os.environ["DB_TEST_URL"] = "sqlite:///test.db"
    
    # Reload the configuration
    reload_database_config()
    
    # Check if the new database was loaded
    dbs_after_reload = multi_db_manager.list_databases()
    print(f"Databases after reload: {dbs_after_reload}")
    
    # Verify that the test database was added
    if "test" in dbs_after_reload:
        print("✓ Test database was successfully loaded after reload")
    else:
        print("✗ Test database was not loaded after reload")
        
    # Clean up: remove the test database and environment variable
    if "test" in dbs_after_reload:
        multi_db_manager.remove_database("test")
    if "DB_TEST_URL" in os.environ:
        del os.environ["DB_TEST_URL"]
    
    # Reload again to ensure clean state
    reload_database_config()
    
    final_dbs = multi_db_manager.list_databases()
    print(f"Final databases: {final_dbs}")
    
    print("Database reload test completed.")


def test_setup_config_integration():
    """Test that the setup config properly reloads databases after saving."""
    print("\nTesting setup config integration...")
    
    from utils.multi_database_manager import multi_db_manager, reload_database_config
    
    # Save original environment
    original_env = dict(os.environ)
    
    try:
        # Temporarily set up environment variables for additional databases
        os.environ["DB_ANALYTICS_URL"] = "postgresql://user:pass@localhost/analytics"
        
        # Call the reload function to simulate what happens after setup
        reload_database_config()
        
        # Check if the analytics database was loaded
        dbs = multi_db_manager.list_databases()
        print(f"Databases after simulating setup: {dbs}")
        
        if "analytics" in dbs:
            print("✓ Analytics database was loaded after simulated setup")
        else:
            print("✗ Analytics database was not loaded after simulated setup")
            
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
        
        # Reload to reset to original state
        reload_database_config()
    
    print("Setup config integration test completed.")


if __name__ == "__main__":
    print("Running database configuration fix tests...\n")
    
    test_database_reload()
    test_setup_config_integration()
    
    print("\nAll tests completed!")
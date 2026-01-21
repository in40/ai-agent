#!/usr/bin/env python3
"""
Test script to verify the multi-database functionality.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.utils.multi_database_manager import multi_db_manager
from database.utils.database_utility import validate_database_url

def test_multi_database_functionality():
    print("Testing Multi-Database Functionality")
    print("=" * 40)
    
    # Test URL validation
    print("\n1. Testing URL validation:")
    test_urls = [
        "sqlite:///test.db",
        "postgresql://user:pass@localhost:5432/mydb",
        "mysql://user:pass@localhost:3306/mydb",
        "invalid-url"
    ]
    
    for url in test_urls:
        is_valid = validate_database_url(url)
        print(f"   {url}: {'Valid' if is_valid else 'Invalid'}")
    
    # Test adding databases
    print("\n2. Testing database addition:")
    
    # Add a test SQLite database
    success = multi_db_manager.add_database("test_db", "sqlite:///test_db.sqlite")
    print(f"   Adding test_db: {'Success' if success else 'Failed'}")
    
    # Try to add a duplicate database
    success = multi_db_manager.add_database("test_db", "sqlite:///different_db.sqlite")
    print(f"   Adding duplicate test_db: {'Success' if success else 'Failed (expected)'}")
    
    # List databases
    print("\n3. Listing databases:")
    dbs = multi_db_manager.list_databases()
    for db in dbs:
        print(f"   - {db}")
    
    # Test removing a database
    print("\n4. Testing database removal:")
    success = multi_db_manager.remove_database("test_db")
    print(f"   Removing test_db: {'Success' if success else 'Failed'}")
    
    # List databases again
    print("\n5. Listing databases after removal:")
    dbs = multi_db_manager.list_databases()
    for db in dbs:
        print(f"   - {db}")
    
    print("\nMulti-database functionality test completed!")

if __name__ == "__main__":
    test_multi_database_functionality()
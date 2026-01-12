#!/usr/bin/env python3
"""
Test script to verify that the database alias mapping is working correctly.
This script verifies that the 'default' alias maps to 'contacts_db' real name.
"""

import os
from config.database_aliases import DatabaseAliasMapper

def test_default_to_contacts_db_mapping():
    """Test that 'default' alias maps to 'contacts_db' real name."""
    
    # Create a fresh mapper instance to ensure clean state
    mapper = DatabaseAliasMapper()
    
    # Test the mapping
    real_name = mapper.get_real_name("default")
    
    print(f"Mapping for 'default' alias: {real_name}")
    
    if real_name == "contacts_db":
        print("✅ SUCCESS: 'default' alias correctly maps to 'contacts_db'")
        return True
    else:
        print(f"❌ FAILURE: Expected 'contacts_db', got '{real_name}'")
        return False

def test_case_insensitive_mapping():
    """Test that the mapping works regardless of case."""
    
    mapper = DatabaseAliasMapper()
    
    test_cases = ["default", "DEFAULT", "Default", "DeFaUlT"]
    
    for alias in test_cases:
        real_name = mapper.get_real_name(alias)
        if real_name != "contacts_db":
            print(f"❌ FAILURE: Case sensitivity issue - '{alias}' maps to '{real_name}', expected 'contacts_db'")
            return False
    
    print("✅ SUCCESS: Case-insensitive mapping works correctly")
    return True

if __name__ == "__main__":
    print("Testing database alias mapping fix...")
    print("=" * 50)
    
    success1 = test_default_to_contacts_db_mapping()
    success2 = test_case_insensitive_mapping()
    
    print("=" * 50)
    if success1 and success2:
        print("🎉 All tests passed! The database alias mapping fix is working correctly.")
    else:
        print("💥 Some tests failed. Please check the implementation.")
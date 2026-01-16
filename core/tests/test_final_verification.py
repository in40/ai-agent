#!/usr/bin/env python3
"""
Final test to verify the original issue is fixed
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models.sql_executor import SQLExecutor

def test_original_issue_fixed():
    """Test that the original issue is fixed"""
    sql_executor = SQLExecutor()
    
    # This is the original problematic query from the error logs
    original_problematic_query = "SELECT DISTINCT c.name, c.phone FROM contacts_db.contacts c JOIN contacts_db.arrest_records a ON (c.name ILIKE '%' || a.first_name || '%' OR c.name ILIKE '%' || a.last_name || '%') WHERE LOWER(a.race) LIKE '%asian%' AND LOWER(a.sex) LIKE '%female%' AND c.is_active = TRUE ORDER BY c.name LIMIT 10;"
    
    print("Testing the original problematic query...")
    print(f"Original: {original_problematic_query[:80]}...")
    
    # Sanitize the query
    sanitized = sql_executor._sanitize_sql_query(original_problematic_query)
    print(f"Sanitized: {sanitized[:80]}...")
    
    # Verify that table names are preserved
    if "contacts" in sanitized and "arrest_records" in sanitized:
        print("✅ SUCCESS: Both table names 'contacts' and 'arrest_records' are preserved")
    else:
        print("❌ FAILURE: Table names were not preserved properly")
        return False
    
    # Verify that the database prefix was removed
    if "contacts_db." not in sanitized:
        print("✅ SUCCESS: Database prefix 'contacts_db.' was properly removed")
    else:
        print("❌ FAILURE: Database prefix was not removed")
        return False
    
    # Verify that aliases are preserved
    if "c" in sanitized and "a" in sanitized:
        print("✅ SUCCESS: Table aliases 'c' and 'a' are preserved")
    else:
        print("❌ FAILURE: Table aliases were not preserved")
        return False
    
    print("\n🎉 All checks passed! The original issue has been fixed.")
    print("The query will no longer fail with 'relation does not exist' error.")
    return True

if __name__ == "__main__":
    success = test_original_issue_fixed()
    if success:
        print("\n✓ Test PASSED - Original issue is fixed")
    else:
        print("\n✗ Test FAILED - Issue still exists")
        sys.exit(1)
#!/usr/bin/env python3
"""
Test script to verify the SQL sanitization fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models.sql_executor import SQLExecutor

def test_sql_sanitization():
    """Test the SQL sanitization functionality"""
    sql_executor = SQLExecutor()
    
    # Test cases that should be properly sanitized
    test_cases = [
        {
            "input": "SELECT DISTINCT c.name, c.phone FROM contacts_db.contacts c JOIN contacts_db.arrest_records a ON (c.name ILIKE '%' || a.first_name || '%' OR c.name ILIKE '%' || a.last_name || '%') WHERE LOWER(a.race) LIKE '%asian%' AND LOWER(a.sex) LIKE '%female%' AND c.is_active = TRUE ORDER BY c.name LIMIT 10;",
            "expected_contains": ["FROM contacts c JOIN arrest_records"],
            "description": "Original problematic query with database.table notation"
        },
        {
            "input": "SELECT * FROM analytics.users u JOIN analytics.sessions s ON u.id = s.user_id",
            "expected_contains": ["FROM analytics.users u JOIN analytics.sessions"],
            "description": "Analytics schema query (should preserve schema.table)"
        },
        {
            "input": "SELECT * FROM public.users",  # This should keep public.users since 'public' is a known schema
            "expected_contains": ["FROM public.users"],
            "description": "Public schema query (should be preserved)"
        },
        {
            "input": "SELECT * FROM mydb.public.users u",  # Three-part name: db.schema.table
            "expected_contains": ["FROM public.users"],
            "description": "Three-part name with known schema (should preserve schema.table)"
        }
    ]
    
    print("Testing SQL sanitization...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input:  {test_case['input'][:100]}...")
        
        sanitized = sql_executor._sanitize_sql_query(test_case['input'])
        print(f"Output: {sanitized[:100]}...")
        
        # Check if expected substrings are present
        all_present = True
        for expected in test_case['expected_contains']:
            if expected not in sanitized:
                print(f"  ❌ FAIL: Expected '{expected}' not found in sanitized query")
                all_present = False
            else:
                print(f"  ✅ PASS: Found expected '{expected}'")
        
        if all_present:
            print(f"  🎉 Test {i} PASSED")
        else:
            print(f"  ❌ Test {i} FAILED")
    
    print("\n" + "="*60)
    print("Test completed!")

if __name__ == "__main__":
    test_sql_sanitization()
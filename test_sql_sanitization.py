#!/usr/bin/env python3
"""
Test script to verify the SQL sanitization fix works correctly.
This script tests the _sanitize_sql_query method with various input cases.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from models.sql_executor import SQLExecutor

def test_sql_sanitization():
    """Test the SQL sanitization method with various inputs"""
    executor = SQLExecutor()
    
    test_cases = [
        # Original problematic case
        {
            "input": 'SELECT DISTINCT c."name", c."phone"\nFROM "default"."contacts" c\nJOIN "analytics"."arrest_data" a ON LOWER(c."name") = LOWER(CONCAT(a."first_name", \' \', a."last_name"))\nWHERE LOWER(a."race") = \'asian\' AND LOWER(a."sex") = \'female\'\nLIMIT 10;',
            "expected_contains": '"analytics"."arrest_data"',
            "description": "Original problematic query with schema prefix"
        },
        # Test with database.schema.table format
        {
            "input": 'SELECT * FROM "mydb"."public"."users" u JOIN "mydb"."analytics"."logs" l ON u.id = l.user_id',
            "expected_contains": '"public"."users"',
            "expected_contains_2": '"analytics"."logs"',
            "description": "Query with database.schema.table format"
        },
        # Test with simple schema.table format (should remain unchanged)
        {
            "input": 'SELECT * FROM "public"."users" u JOIN "analytics"."logs" l ON u.id = l.user_id',
            "expected_contains": '"public"."users"',
            "expected_contains_2": '"analytics"."logs"',
            "description": "Query with schema.table format (should remain unchanged)"
        },
        # Test with database.table format (should remove database prefix)
        {
            "input": 'SELECT * FROM "mydb"."users" u JOIN "mydb"."logs" l ON u.id = l.user_id',
            "expected_contains": 'FROM "users"',
            "expected_contains_2": 'JOIN "logs"',
            "description": "Query with database.table format (should remove database prefix)"
        },
        # Test with unquoted identifiers
        {
            "input": 'SELECT * FROM mydb.public.users u JOIN mydb.analytics.logs l ON u.id = l.user_id',
            "expected_contains": 'FROM public.users',
            "expected_contains_2": 'JOIN analytics.logs',
            "description": "Query with unquoted database.schema.table format"
        }
    ]
    
    print("Testing SQL sanitization...")
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input:  {test_case['input']}")
        
        sanitized = executor._sanitize_sql_query(test_case['input'])
        print(f"Output: {sanitized}")
        
        # Check if expected content is in the sanitized query
        if "expected_contains_2" in test_case:
            # Check for two expected substrings
            contains_1 = test_case['expected_contains'] in sanitized
            contains_2 = test_case['expected_contains_2'] in sanitized
            passed = contains_1 and contains_2
            print(f"Expected to contain: '{test_case['expected_contains']}' AND '{test_case['expected_contains_2']}'")
            print(f"Result: {'PASS' if passed else 'FAIL'}")
        else:
            # Check for one expected substring
            contains = test_case['expected_contains'] in sanitized
            passed = contains
            print(f"Expected to contain: '{test_case['expected_contains']}'")
            print(f"Result: {'PASS' if passed else 'FAIL'}")
        
        if not passed:
            all_passed = False
    
    print(f"\nOverall result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = test_sql_sanitization()
    sys.exit(0 if success else 1)
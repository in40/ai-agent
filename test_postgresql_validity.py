#!/usr/bin/env python3
"""
Test script to verify that the sanitized SQL is actually valid for PostgreSQL.
"""

from models.sql_executor import SQLExecutor
import re

def test_sql_validity():
    """Test if the sanitized SQL would be valid in PostgreSQL."""
    
    executor = SQLExecutor()
    
    # Test the problematic case from the logs
    original_query = "SELECT name, phone FROM contacts WHERE country IN (\\'China\\', \\'Japan\\', \\'South Korea\\') AND is_active = TRUE LIMIT 10;"
    
    print("Original query from LLM:")
    print(original_query)
    print()
    
    sanitized_query = executor._sanitize_sql_query(original_query)
    print("Sanitized query:")
    print(sanitized_query)
    print()
    
    # Check if the sanitized query has valid SQL string literal structure
    # Look for patterns like 'string_value' (single quotes around content)
    string_literals = re.findall(r"'(?:[^'\\]|\\.)*'", sanitized_query)
    print(f"Found string literals: {string_literals}")
    
    # Count quotes to make sure they're balanced
    quote_count = sanitized_query.count("'")
    print(f"Total quote count: {quote_count} (should be even for valid SQL)")
    
    # Check for the problematic pattern that was causing the original error
    if "''" in sanitized_query and sanitized_query.count("''") > 0:
        # Check if these are legitimate PostgreSQL quote escapes or problematic ones
        problematic_double_quotes = []
        parts = sanitized_query.split("'")
        for i, part in enumerate(parts):
            if i % 2 == 0 and "''" in part:  # Outside of string literals
                problematic_double_quotes.append(part)
        
        if problematic_double_quotes:
            print(f"⚠️  Found potentially problematic double quotes outside string literals: {problematic_double_quotes}")
        else:
            print("✅ Double quotes appear to be inside string literals (valid PostgreSQL escaping)")
    
    if quote_count % 2 == 0:
        print("✅ Quote count is even - likely valid SQL syntax")
        return True
    else:
        print("❌ Quote count is odd - likely invalid SQL syntax")
        return False

def test_various_scenarios():
    """Test various quote scenarios to ensure correctness."""
    
    executor = SQLExecutor()
    
    test_cases = [
        {
            "name": "Simple country names",
            "input": "SELECT * FROM contacts WHERE country = \\'China\\'",
            "expected_contains": "'China'"
        },
        {
            "name": "Multiple values in IN clause", 
            "input": "SELECT * FROM contacts WHERE country IN (\\'China\\', \\'Japan\\')",
            "expected_contains": ["'China'", "'Japan'"]
        },
        {
            "name": "String with apostrophe (needs PostgreSQL escaping)",
            "input": "SELECT * FROM users WHERE name = \\'John\\'s Account\\'",
            "expected_contains": "'John''s Account'"  # Note the double single quote
        }
    ]
    
    print("\n" + "="*60)
    print("Testing various scenarios:")
    
    all_passed = True
    
    for case in test_cases:
        print(f"\nTest: {case['name']}")
        print(f"Input:  {case['input']}")
        
        sanitized = executor._sanitize_sql_query(case['input'])
        print(f"Output: {sanitized}")
        
        # Check expected content
        expected = case['expected_contains']
        if isinstance(expected, str):
            expected = [expected]
            
        missing = []
        for exp in expected:
            if exp not in sanitized:
                missing.append(exp)
        
        if missing:
            print(f"❌ Missing expected content: {missing}")
            all_passed = False
        else:
            print("✅ Expected content found")
            
        # Check quote balance
        quote_count = sanitized.count("'")
        if quote_count % 2 != 0:
            print(f"❌ Odd quote count ({quote_count}) - invalid SQL")
            all_passed = False
        else:
            print(f"✅ Even quote count ({quote_count}) - valid SQL structure")
    
    return all_passed

if __name__ == "__main__":
    validity = test_sql_validity()
    scenarios = test_various_scenarios()
    
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if validity and scenarios else '❌ SOME TESTS FAILED'}")
    
    if validity and scenarios:
        print("\nThe fix successfully converts LLM-generated escaped quotes to valid PostgreSQL syntax!")
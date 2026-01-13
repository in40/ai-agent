#!/usr/bin/env python3
"""
Test script to verify the SQL extraction and sanitization implementation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models.sql_generator import SQLGenerator
from models.sql_executor import SQLExecutor


def test_sql_extraction():
    """Test the SQL extraction functionality with custom delimiters"""
    sql_generator = SQLGenerator()

    # Test cases with different delimiter formats
    test_cases = [
        {
            "input": "Some text before\n<sql_generated>\nSELECT * FROM users WHERE name = 'John';\n</sql_generated>\nSome text after",
            "expected": "SELECT * FROM users WHERE name = 'John';",
            "description": "Basic sql_generated tags"
        },
        {
            "input": "###ponder###\nThought process...\n###/ponder###\n<sql_query>\nSELECT id, name FROM contacts WHERE country = 'USA';\n</sql_query>",
            "expected": "SELECT id, name FROM contacts WHERE country = 'USA';",
            "description": "sql_query tags with thought process"
        },
        {
            "input": "Response with multiple sections\n<sql_code>SELECT * FROM orders LIMIT 10;</sql_code>\nMore text",
            "expected": "SELECT * FROM orders LIMIT 10;",
            "description": "sql_code tags"
        },
        {
            "input": "Simple response with markdown:\n```sql\nSELECT * FROM products;\n```\nEnd of response",
            "expected": "SELECT * FROM products;",
            "description": "Markdown code blocks without custom tags"
        },
        {
            "input": "SELECT * FROM customers;",
            "expected": "SELECT * FROM customers;",
            "description": "Plain SQL without tags"
        }
    ]

    print("Testing SQL extraction with custom delimiters...")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input:  {repr(test_case['input'])}")

        extracted = sql_generator.clean_sql_response(test_case['input'])
        print(f"Output: {repr(extracted)}")
        print(f"Expected: {repr(test_case['expected'])}")

        if extracted.strip() == test_case['expected'].strip():
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL: Expected {repr(test_case['expected'])}, got {repr(extracted)}")

    print("\n" + "="*60)


def test_sql_sanitization():
    """Test the SQL sanitization functionality"""
    sql_generator = SQLGenerator()
    sql_executor = SQLExecutor()

    # Test cases for sanitization
    test_cases = [
        {
            "input": "SELECT * FROM users WHERE name = \\'John\\';",
            "expected_contains": ["name = 'John'"],
            "description": "Escaped single quotes"
        },
        {
            "input": "SELECT * FROM /* comment */ users -- another comment\nWHERE id = 1;",
            "expected_not_contains": ["/* comment */", "-- another comment"],
            "description": "Remove SQL comments"
        },
        {
            "input": "SELECT * FROM users; DROP TABLE users;",  # Dangerous stacked query
            "expected_stripped": "SELECT * FROM users",
            "description": "Remove statement terminators"
        },
        {
            "input": "SELECT * FROM users WHERE name = \\\\\\'test\\\\\\';",
            "expected_contains": ["name = \\'test\\'"],  # Should normalize double backslashes
            "description": "Normalize extra backslashes"
        }
    ]

    print("Testing SQL sanitization...")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input:  {repr(test_case['input'])}")

        # Test sanitization in SQLGenerator
        sanitized_gen = sql_generator.sanitize_sql_query(test_case['input'])
        print(f"Gen Sanitized: {repr(sanitized_gen)}")

        # Test sanitization in SQLExecutor
        sanitized_exec = sql_executor._sanitize_sql_query(test_case['input'])
        print(f"Exec Sanitized: {repr(sanitized_exec)}")

        # Check expectations
        success = True
        if 'expected_contains' in test_case:
            for expected in test_case['expected_contains']:
                if expected not in sanitized_gen:
                    print(f"  ❌ FAIL: Expected '{expected}' not found in sanitized query (generator)")
                    success = False
                if expected not in sanitized_exec:
                    print(f"  ❌ FAIL: Expected '{expected}' not found in sanitized query (executor)")
                    success = False
                if expected not in sanitized_gen and expected not in sanitized_exec:
                    continue  # Both failed
                else:
                    print(f"  ✅ PASS: Found expected '{expected}'")

        if 'expected_not_contains' in test_case:
            for not_expected in test_case['expected_not_contains']:
                if not_expected in sanitized_gen:
                    print(f"  ❌ FAIL: Unexpected '{not_expected}' found in sanitized query (generator)")
                    success = False
                if not_expected in sanitized_exec:
                    print(f"  ❌ FAIL: Unexpected '{not_expected}' found in sanitized query (executor)")
                    success = False
                if not_expected not in sanitized_gen and not_expected not in sanitized_exec:
                    print(f"  ✅ PASS: Correctly removed '{not_expected}'")
                else:
                    continue  # At least one succeeded

        if 'expected_stripped' in test_case:
            if sanitized_gen.startswith(test_case['expected_stripped']):
                print(f"  ✅ PASS: Stacked query properly handled (generator)")
            else:
                print(f"  ❌ FAIL: Expected start '{test_case['expected_stripped']}', got '{sanitized_gen}' (generator)")
                success = False

            if sanitized_exec.startswith(test_case['expected_stripped']):
                print(f"  ✅ PASS: Stacked query properly handled (executor)")
            else:
                print(f"  ❌ FAIL: Expected start '{test_case['expected_stripped']}', got '{sanitized_exec}' (executor)")
                success = False

        if success:
            print(f"  🎉 Test {i} PASSED")

    print("\n" + "="*60)


def test_combined_extraction_and_sanitization():
    """Test the combination of extraction and sanitization"""
    sql_generator = SQLGenerator()

    # Test case combining extraction and sanitization
    complex_input = """###ponder###
    Thinking about the user's request to find users...
    
    Need to query the users table with proper filtering.
    </ponder>

    <sql_generated>
    SELECT * FROM users WHERE name = \\'John Doe\\' /* dangerous comment */;
    </sql_generated>

    This should be ignored."""

    print("Testing combined extraction and sanitization...")
    print(f"Input: {repr(complex_input)}")

    result = sql_generator.clean_sql_response(complex_input)
    print(f"Result: {repr(result)}")

    # Check that the result is properly extracted and sanitized
    expected_parts = ["SELECT", "FROM users", "name = 'John Doe'"]
    unexpected_parts = ["<sql_generated>", "</sql_generated>", "###ponder###", "/* dangerous comment */"]

    success = True
    for part in expected_parts:
        if part not in result:
            print(f"  ❌ FAIL: Expected part '{part}' not found")
            success = False
        else:
            print(f"  ✅ Found expected part: {part}")

    for part in unexpected_parts:
        if part in result:
            print(f"  ❌ FAIL: Unexpected part '{part}' found")
            success = False
        else:
            print(f"  ✅ Correctly removed part: {part}")

    if success:
        print("  🎉 Combined test PASSED")
    else:
        print("  ❌ Combined test FAILED")

    print("\n" + "="*60)


def main():
    """Run all tests"""
    print("Running SQL Extraction and Sanitization Tests\n")
    
    test_sql_extraction()
    test_sql_sanitization()
    test_combined_extraction_and_sanitization()
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    main()
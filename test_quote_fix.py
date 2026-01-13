#!/usr/bin/env python3
"""
Test script to verify the fix for escaped single quotes in SQL queries.
"""

from models.sql_executor import SQLExecutor
from utils.multi_database_manager import multi_db_manager

def test_quote_sanitization():
    """Test that escaped single quotes are properly converted for PostgreSQL."""

    executor = SQLExecutor()

    # Test the problematic query from the error logs - with actual backslash escapes
    problematic_query = "SELECT name, phone FROM contacts WHERE country IN (\\'China\\', \\'Japan\\', \\'South Korea\\', \\'India\\', \\'Vietnam\\', \\'Philippines\\', \\'Thailand\\', \\'Indonesia\\', \\'Malaysia\\', \\'Singapore\\', \\'Taiwan\\', \\'Hong Kong\\') AND is_active = TRUE LIMIT 10;"

    print("Original query:")
    print(problematic_query)
    print("\n" + "="*50 + "\n")

    # Sanitize the query
    sanitized_query = executor._sanitize_sql_query(problematic_query)

    print("Sanitized query:")
    print(sanitized_query)
    print("\n" + "="*50 + "\n")

    # Expected result: escaped quotes should be converted to PostgreSQL-style double quotes
    expected_query = "SELECT name, phone FROM contacts WHERE country IN (''China'', ''Japan'', ''South Korea'', ''India'', ''Vietnam'', ''Philippines'', ''Thailand'', ''Indonesia'', ''Malaysia'', ''Singapore'', ''Taiwan'', ''Hong Kong'') AND is_active = TRUE LIMIT 10;"

    print("Expected query:")
    print(expected_query)
    print("\n" + "="*50 + "\n")

    # Check if the conversion worked
    if "''China''" in sanitized_query and "''Japan''" in sanitized_query:
        print("✅ SUCCESS: Escaped single quotes were properly converted!")
    else:
        print("❌ FAILURE: Escaped single quotes were not properly converted.")

    # Show the difference
    print("Comparison:")
    print(f"Before: ...country IN (\\'China\\',...")
    print(f"After:  ...country IN (''China'',...")


def test_other_escape_sequences():
    """Test that other escape sequences are handled properly."""
    
    executor = SQLExecutor()
    
    # Test query with various escape sequences
    test_query = "SELECT * FROM users WHERE name = \'John\\'s Account\' AND description = \'Line1\\nLine2\\tTabbed\'"
    
    print("\n" + "="*50)
    print("Testing other escape sequences:")
    print("Original query:")
    print(test_query)
    
    sanitized_query = executor._sanitize_sql_query(test_query)
    
    print("\nSanitized query:")
    print(sanitized_query)
    
    # Check if the conversions worked
    success_checks = [
        ("''John''s Account''" in sanitized_query, "Single quote escaping"),
        ("\n" in sanitized_query, "Newline conversion"),
        ("\t" in sanitized_query, "Tab conversion")
    ]
    
    for check, desc in success_checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")


if __name__ == "__main__":
    print("Testing SQL quote sanitization fix...\n")
    test_quote_sanitization()
    test_other_escape_sequences()
    print("\nTesting completed!")
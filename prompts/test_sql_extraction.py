#!/usr/bin/env python3
"""
Test script to verify that SQL extraction and validation work correctly
"""
import re
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sql_generator_model import SQLGenerator


def test_sql_extraction():
    """Test the clean_sql_response method with various input formats"""
    generator = SQLGenerator()
    
    print("Testing SQL extraction methods...")
    
    # Test 1: SQL with the new tags
    response1 = """Some reasoning here...
###ponder###
Some more thoughts...
###/ponder###
<sql_to_use>SELECT * FROM users WHERE name = 'John';</sql_to_use>"""
    
    result1 = generator.clean_sql_response(response1)
    print(f"Test 1 - SQL with tags: '{result1}'")
    assert result1 == "SELECT * FROM users WHERE name = 'John';", f"Expected 'SELECT * FROM users WHERE name = 'John';', got '{result1}'"
    
    # Test 2: SQL with markdown blocks
    response2 = """Some reasoning here...
###ponder###
Some more thoughts...
###/ponder###
```sql
SELECT first_name, last_name FROM customers;
```"""
    
    result2 = generator.clean_sql_response(response2)
    print(f"Test 2 - SQL with markdown: '{result2}'")
    expected2 = "SELECT first_name, last_name FROM customers;"
    assert result2.strip() == expected2, f"Expected '{expected2}', got '{result2}'"
    
    # Test 3: SQL with markdown blocks and reasoning after
    response3 = """Some reasoning here...
###ponder###
Some more thoughts...
###/ponder###
```sql
SELECT 
    ar.first_name,
    ar.last_name,
    ar.race,
    ar.sex,
    c.phone
FROM arrest_records ar
LEFT JOIN contacts c ON c.name = ar.first_name || ' ' || ar.last_name
WHERE ar.race = 'Asian' AND ar.sex = 'Female'
LIMIT 10;
```

More reasoning after the SQL..."""
    
    result3 = generator.clean_sql_response(response3)
    print(f"Test 3 - Complex SQL with markdown: '{result3}'")
    expected3 = """SELECT 
    ar.first_name,
    ar.last_name,
    ar.race,
    ar.sex,
    c.phone
FROM arrest_records ar
LEFT JOIN contacts c ON c.name = ar.first_name || ' ' || ar.last_name
WHERE ar.race = 'Asian' AND ar.sex = 'Female'
LIMIT 10;"""
    assert result3.strip() == expected3.strip(), f"Expected '{expected3}', got '{result3}'"
    
    # Test 4: SQL without tags but present after reasoning (fallback)
    response4 = """Some reasoning here...
###ponder###
This is my reasoning about the query.
The user wants to find contacts with updated dates.
I should use the updated_at column.
###/ponder###
SELECT * FROM contacts WHERE updated_at > '2023-01-01';"""

    result4 = generator.clean_sql_response(response4)
    print(f"Test 4 - SQL without tags but after reasoning: '{result4}'")
    expected4 = "SELECT * FROM contacts WHERE updated_at > '2023-01-01';"
    assert result4.strip() == expected4, f"Expected '{expected4}', got '{result4}'"
    
    print("All SQL extraction tests passed!")


def test_validation_logic():
    """Test the validation logic to ensure it doesn't flag column names with harmful keywords"""
    print("\nTesting validation logic...")
    
    # Import the validation function from the main agent file
    import importlib.util
    spec = importlib.util.spec_from_file_location("langgraph_agent_main", "/root/qwen_test/ai_agent/prompts/langgraph_agent_main.py")
    agent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_module)
    
    # Mock state for testing
    class MockState(dict):
        def get(self, key, default=None):
            return super().get(key, default)
    
    # Test 1: Valid SELECT query with column containing 'update' (should pass)
    state1 = MockState({
        "sql_query": "SELECT first_name, last_name, updated_at FROM users WHERE updated_at > '2023-01-01';",
        "disable_sql_blocking": False,
        "schema_dump": {}
    })
    
    try:
        result1 = agent_module.validate_sql_node(state1)
        validation_error1 = result1.get("validation_error")
        print(f"Test 1 - Query with 'updated_at' column: validation_error = {validation_error1}")
        assert validation_error1 is None, f"Query with 'updated_at' column should pass validation, but got error: {validation_error1}"
        print("  ✓ Query with 'updated_at' column passed validation")
    except Exception as e:
        print(f"  ✗ Error during validation: {e}")
        raise
    
    # Test 2: Valid SELECT query with column containing 'update' in the name (should pass)
    state2 = MockState({
        "sql_query": "SELECT user_id, update_frequency FROM user_settings;",
        "disable_sql_blocking": False,
        "schema_dump": {}
    })
    
    try:
        result2 = agent_module.validate_sql_node(state2)
        validation_error2 = result2.get("validation_error")
        print(f"Test 2 - Query with 'update_frequency' column: validation_error = {validation_error2}")
        assert validation_error2 is None, f"Query with 'update_frequency' column should pass validation, but got error: {validation_error2}"
        print("  ✓ Query with 'update_frequency' column passed validation")
    except Exception as e:
        print(f"  ✗ Error during validation: {e}")
        raise
    
    # Test 3: Actual UPDATE command (should fail)
    state3 = MockState({
        "sql_query": "UPDATE users SET name = 'New Name' WHERE id = 1;",
        "disable_sql_blocking": False,
        "schema_dump": {}
    })
    
    try:
        result3 = agent_module.validate_sql_node(state3)
        validation_error3 = result3.get("validation_error")
        print(f"Test 3 - Actual UPDATE command: validation_error = {validation_error3}")
        assert validation_error3 is not None, "Actual UPDATE command should fail validation"
        assert "update" in validation_error3.lower(), f"Error message should mention 'update', got: {validation_error3}"
        print("  ✓ Actual UPDATE command was correctly flagged")
    except Exception as e:
        print(f"  ✗ Error during validation: {e}")
        raise
    
    # Test 4: Valid query with qualified names containing 'update' (should pass)
    state4 = MockState({
        "sql_query": "SELECT u.name, p.updated_at FROM users u JOIN profiles p ON u.id = p.user_id;",
        "disable_sql_blocking": False,
        "schema_dump": {}
    })
    
    try:
        result4 = agent_module.validate_sql_node(state4)
        validation_error4 = result4.get("validation_error")
        print(f"Test 4 - Query with qualified 'updated_at' column: validation_error = {validation_error4}")
        assert validation_error4 is None, f"Query with qualified 'updated_at' column should pass validation, but got error: {validation_error4}"
        print("  ✓ Query with qualified 'updated_at' column passed validation")
    except Exception as e:
        print(f"  ✗ Error during validation: {e}")
        raise
    
    print("All validation logic tests passed!")


def main():
    """Run all tests"""
    print("Running SQL extraction and validation tests...\n")
    
    try:
        test_sql_extraction()
        test_validation_logic()
        print("\n🎉 All tests passed! The changes work correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
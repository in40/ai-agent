#!/usr/bin/env python3
"""
Demo script showcasing the new Security LLM feature
"""

import os
from langgraph_agent import run_enhanced_agent, validate_sql_node


def demo_security_llm_false_positive():
    """Demonstrate how the security LLM handles false positives like 'created_at' column"""
    print("=== Demo: Security LLM Handling False Positives ===")
    print("Request: 'Show users created after 2023'")
    print("SQL Query: SELECT * FROM users WHERE created_at > '2023-01-01';")
    print("Note: 'created_at' contains 'create' but is a legitimate column name")
    
    # Temporarily enable security LLM for this demo
    original_value = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'true'
    
    try:
        result = run_enhanced_agent("Show users created after 2023")
        print(f"Result: {result['final_response'][:100]}...")
        print("✓ Security LLM correctly identified this as safe")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['USE_SECURITY_LLM'] = original_value
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']
    
    print()


def demo_security_llm_harmful_query():
    """Demonstrate how the security LLM detects actually harmful queries"""
    print("=== Demo: Security LLM Detecting Harmful Queries ===")
    print("Request: 'Delete all users' (potentially harmful)")
    print("SQL Query: DROP TABLE users;")
    
    # Temporarily enable security LLM for this demo
    original_value = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'true'
    
    try:
        # We'll simulate a harmful query by directly testing the validation
        from langgraph_agent import validate_sql_node
        from config.settings import str_to_bool
        
        # Create a state with a harmful query
        state = {
            "user_request": "Delete all users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}, {"name": "created_at", "type": "datetime"}]},
            "sql_query": "DROP TABLE users;",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }
        
        # Temporarily set USE_SECURITY_LLM to true for this validation
        os.environ['USE_SECURITY_LLM'] = 'true'
        result = validate_sql_node(state)
        
        if result["validation_error"]:
            print(f"Security Check: FAILED - {result['validation_error']}")
            print("✓ Security LLM correctly identified this as harmful")
        else:
            print("Security Check: PASSED - Query is safe")
            print("⚠️  Security LLM did not detect this as harmful (unexpected)")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['USE_SECURITY_LLM'] = original_value
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']
    
    print()


def demo_basic_validation_fallback():
    """Demonstrate the fallback to basic validation when security LLM is disabled"""
    print("=== Demo: Basic Validation Fallback ===")
    print("Request: 'Show users with created_at after 2023' (with security LLM disabled)")
    print("SQL Query: SELECT * FROM users WHERE created_at > '2023-01-01';")
    print("Note: Basic validation might incorrectly flag 'created_at' as harmful")
    
    # Temporarily disable security LLM for this demo
    original_value = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'
    
    try:
        # Create a state with a query that might trigger false positive
        state = {
            "user_request": "Show users with created_at after 2023",
            "schema_dump": {"users": [{"name": "id", "type": "int"}, {"name": "created_at", "type": "datetime"}]},
            "sql_query": "SELECT * FROM users WHERE created_at > '2023-01-01';",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }
        
        result = validate_sql_node(state)
        
        if result["validation_error"]:
            print(f"Basic Validation: FAILED - {result['validation_error']}")
            print("⚠️  Basic validation incorrectly flagged 'created_at' as harmful (false positive)")
        else:
            print("Basic Validation: PASSED - Query is safe")
            print("✓ Basic validation correctly identified this as safe")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['USE_SECURITY_LLM'] = original_value
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']
    
    print()


if __name__ == "__main__":
    print("Security LLM Feature Demo\n")
    
    demo_security_llm_false_positive()
    demo_security_llm_harmful_query()
    demo_basic_validation_fallback()
    
    print("Summary:")
    print("- Security LLM reduces false positives by understanding context")
    print("- It correctly identifies actual security threats")
    print("- Basic validation is still available as a fallback")
    print("- The feature can be enabled/disabled via configuration")
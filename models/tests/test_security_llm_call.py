#!/usr/bin/env python3
"""
Test script to verify that the security LLM is actually called when requested
"""

import os
from unittest.mock import patch, Mock
from langgraph_agent.langgraph_agent import validate_sql_node


def test_security_llm_called_when_enabled():
    """Test that the security LLM is called when USE_SECURITY_LLM is enabled"""
    print("=== Test: Security LLM Called When Enabled ===")
    
    # Temporarily enable security LLM
    original_value = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'true'

    try:
        # Create a state with a query
        state = {
            "user_request": "Show users created after 2023",
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

        # Mock the SecuritySQLDetector to track if it's instantiated
        with patch('langgraph_agent.SecuritySQLDetector') as mock_security_detector_class:
            mock_detector_instance = Mock()
            mock_detector_instance.is_query_safe.return_value = (True, "Query is safe")
            mock_security_detector_class.return_value = mock_detector_instance

            # Call the validation function
            result = validate_sql_node(state)

            # Check if SecuritySQLDetector was instantiated (meaning security LLM was used)
            mock_security_detector_class.assert_called_once()
            mock_detector_instance.is_query_safe.assert_called_once()
            
            print("✓ Security LLM was instantiated and called as expected")
            print(f"✓ Query was validated and result: {result['validation_error']}")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['USE_SECURITY_LLM'] = original_value
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']

    print()


def test_security_llm_not_called_when_disabled():
    """Test that the security LLM is not called when USE_SECURITY_LLM is disabled"""
    print("=== Test: Security LLM Not Called When Disabled ===")
    
    # Temporarily disable security LLM
    original_value = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        # Create a state with a query that would normally trigger basic validation
        state = {
            "user_request": "Show users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "SELECT * FROM users;",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        # Mock the SecuritySQLDetector to track if it's instantiated
        with patch('langgraph_agent.SecuritySQLDetector') as mock_security_detector_class:
            # Call the validation function
            result = validate_sql_node(state)

            # Check that SecuritySQLDetector was NOT instantiated (meaning security LLM was not used)
            mock_security_detector_class.assert_not_called()
            
            print("✓ Security LLM was not instantiated when disabled")
            print(f"✓ Query was validated using basic validation: {result['validation_error'] is None}")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['USE_SECURITY_LLM'] = original_value
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']

    print()


def test_security_llm_called_with_correct_parameters():
    """Test that the security LLM is called with the correct parameters"""
    print("=== Test: Security LLM Called With Correct Parameters ===")
    
    # Temporarily enable security LLM
    original_value = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'true'

    try:
        # Create a state with a query
        test_query = "SELECT * FROM users WHERE created_at > '2023-01-01';"
        test_schema = {"users": [{"name": "id", "type": "int"}, {"name": "created_at", "type": "datetime"}]}
        
        state = {
            "user_request": "Show users created after 2023",
            "schema_dump": test_schema,
            "sql_query": test_query,
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        # Mock the SecuritySQLDetector to track the parameters passed to is_query_safe
        with patch('langgraph_agent.SecuritySQLDetector') as mock_security_detector_class:
            mock_detector_instance = Mock()
            mock_detector_instance.is_query_safe.return_value = (True, "Query is safe")
            mock_security_detector_class.return_value = mock_detector_instance

            # Call the validation function
            result = validate_sql_node(state)

            # Check that is_query_safe was called with the correct parameters
            mock_detector_instance.is_query_safe.assert_called_once_with(test_query, test_schema)
            
            print("✓ Security LLM was called with correct SQL query and schema")
            call_args = mock_detector_instance.is_query_safe.call_args
            print(f"✓ SQL Query passed: {call_args[0][0]}")
            print(f"✓ Schema passed: {call_args[0][1]}")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['USE_SECURITY_LLM'] = original_value
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']

    print()


if __name__ == "__main__":
    print("Testing Security LLM Call Verification\n")
    
    test_security_llm_called_when_enabled()
    test_security_llm_not_called_when_disabled()
    test_security_llm_called_with_correct_parameters()
    
    print("All tests passed! Security LLM is properly called when requested.")
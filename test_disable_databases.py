#!/usr/bin/env python3
"""
Test script to verify the disable databases functionality.
"""

import os
import sys
from unittest.mock import patch, MagicMock

def test_disable_databases_flag():
    """Test that the DISABLE_DATABASES flag is properly read from environment"""
    print("Testing DISABLE_DATABASES flag...")
    
    # Test default value (should be False)
    from config.settings import DISABLE_DATABASES as default_value
    print(f"Default DISABLE_DATABASES value: {default_value}")
    assert default_value is False, "Default value should be False"
    
    # Test with environment variable set to True
    os.environ['DISABLE_DATABASES'] = 'true'
    # Need to reload the module to pick up the new environment variable
    import importlib
    import config.settings
    importlib.reload(config.settings)
    from config.settings import DISABLE_DATABASES as true_value
    print(f"DISABLE_DATABASES with 'true': {true_value}")
    assert true_value is True, "Value should be True when environment is 'true'"
    
    # Test with environment variable set to False
    os.environ['DISABLE_DATABASES'] = 'false'
    importlib.reload(config.settings)
    from config.settings import DISABLE_DATABASES as false_value
    print(f"DISABLE_DATABASES with 'false': {false_value}")
    assert false_value is False, "Value should be False when environment is 'false'"

    # Actually test with 'n' to get False
    os.environ['DISABLE_DATABASES'] = 'n'
    importlib.reload(config.settings)
    from config.settings import DISABLE_DATABASES as false_value_correct
    print(f"DISABLE_DATABASES with 'n': {false_value_correct}")
    assert false_value_correct is False, "Value should be False when environment is 'n'"
    
    # Reset environment
    if 'DISABLE_DATABASES' in os.environ:
        del os.environ['DISABLE_DATABASES']
        
    print("✓ DISABLE_DATABASES flag tests passed!")


def test_ai_agent_without_databases():
    """Test AI Agent initialization when databases are disabled"""
    print("\nTesting AI Agent initialization with databases disabled...")

    # Set environment to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'

    # Need to reload modules to pick up the new environment variable
    import importlib
    import config.settings
    importlib.reload(config.settings)

    # Import after setting environment and reloading
    import ai_agent
    importlib.reload(ai_agent)
    from ai_agent import AIAgent

    # Create agent with databases disabled
    agent = AIAgent()

    # Check that database components are None
    assert agent.db_manager is None, "db_manager should be None when databases are disabled"
    assert agent.sql_executor is None, "sql_executor should be None when databases are disabled"

    print("✓ AI Agent initialization with databases disabled passed!")

    # Reset environment
    if 'DISABLE_DATABASES' in os.environ:
        del os.environ['DISABLE_DATABASES']


def test_ai_agent_process_request_without_databases():
    """Test AI Agent process_request when databases are disabled"""
    print("\nTesting AI Agent process_request with databases disabled...")

    # Set environment to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'

    # Need to reload modules to pick up the new environment variable
    import importlib
    import config.settings
    importlib.reload(config.settings)

    # Import after setting environment and reloading
    import ai_agent
    importlib.reload(ai_agent)
    from ai_agent import AIAgent

    # Create agent with databases disabled
    agent = AIAgent()

    # Mock the response generator to return a predictable response
    agent.response_generator.generate_natural_language_response = MagicMock(return_value="Mocked response")

    # Process a request
    result = agent.process_request("Test request")

    # Verify that the result has the expected structure
    assert result['original_request'] == "Test request"
    assert result['generated_sql'] is None, "SQL should be None when databases are disabled"
    assert result['db_results'] is None, "DB results should be None when databases are disabled"
    assert result['final_response'] == "Mocked response", "Response should come from response generator"

    print("✓ AI Agent process_request with databases disabled passed!")

    # Reset environment
    if 'DISABLE_DATABASES' in os.environ:
        del os.environ['DISABLE_DATABASES']


def test_langgraph_agent_without_databases():
    """Test LangGraph agent execution with databases disabled"""
    print("\nTesting LangGraph agent execution with databases disabled...")

    # Set environment to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'

    # Need to reload modules to pick up the new environment variable
    import importlib
    import config.settings
    importlib.reload(config.settings)

    # Import after setting environment and reloading
    import langgraph_agent
    importlib.reload(langgraph_agent)
    from langgraph_agent import run_enhanced_agent

    # Run the agent with a test request
    result = run_enhanced_agent("Test request")

    # Verify that database-related fields are appropriately set
    assert result['original_request'] == "Test request"
    assert result['generated_sql'] is None or result['sql_generation_error'] is not None, \
        "Either SQL should be None or there should be a generation error when databases are disabled"
    assert result['db_results'] == [] or result['db_results'] is None, \
        "DB results should be empty when databases are disabled"

    print("✓ LangGraph agent execution with databases disabled passed!")

    # Reset environment
    if 'DISABLE_DATABASES' in os.environ:
        del os.environ['DISABLE_DATABASES']


def test_main_with_disabled_databases():
    """Test main function behavior with disabled databases"""
    print("\nTesting main function with disabled databases...")
    
    # Set environment to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'
    
    # Import after setting environment
    import importlib
    import config.settings
    importlib.reload(config.settings)
    
    # Import main after reloading settings
    import main
    
    # Verify that DISABLE_DATABASES is True in main
    assert main.DISABLE_DATABASES is True, "DISABLE_DATABASES should be True in main"
    
    print("✓ Main function with disabled databases test passed!")
    
    # Reset environment
    if 'DISABLE_DATABASES' in os.environ:
        del os.environ['DISABLE_DATABASES']


def run_all_tests():
    """Run all tests for the disable databases functionality"""
    print("Running tests for disable databases functionality...\n")
    
    test_disable_databases_flag()
    test_ai_agent_without_databases()
    test_ai_agent_process_request_without_databases()
    test_langgraph_agent_without_databases()
    test_main_with_disabled_databases()
    
    print("\n🎉 All tests for disable databases functionality passed!")


if __name__ == "__main__":
    run_all_tests()
#!/usr/bin/env python3
"""
Simple test script to verify the disable databases functionality.
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
    
    print("✓ DISABLE_DATABASES flag test passed!")


def test_ai_agent_without_databases_via_env():
    """Test AI Agent behavior when databases are disabled via environment"""
    print("\nTesting AI Agent behavior with databases disabled via environment...")
    
    # Temporarily set environment variable
    original_env = os.environ.get('DISABLE_DATABASES')
    os.environ['DISABLE_DATABASES'] = 'true'
    
    # Import after setting environment
    import importlib
    import config.settings
    importlib.reload(config.settings)
    
    # Import and create agent
    from ai_agent import AIAgent
    agent = AIAgent()
    
    # Check that database components are None
    assert agent.db_manager is None, "db_manager should be None when databases are disabled"
    assert agent.sql_executor is None, "sql_executor should be None when databases are disabled"
    
    print("✓ AI Agent behavior with databases disabled test passed!")
    
    # Restore original environment
    if original_env is not None:
        os.environ['DISABLE_DATABASES'] = original_env
    else:
        if 'DISABLE_DATABASES' in os.environ:
            del os.environ['DISABLE_DATABASES']


def test_ai_agent_process_request_without_databases():
    """Test AI Agent process_request when databases are disabled"""
    print("\nTesting AI Agent process_request with databases disabled...")
    
    # Temporarily set environment variable
    original_env = os.environ.get('DISABLE_DATABASES')
    os.environ['DISABLE_DATABASES'] = 'true'
    
    # Import after setting environment
    import importlib
    import config.settings
    importlib.reload(config.settings)
    
    # Import and create agent
    from ai_agent import AIAgent
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
    
    print("✓ AI Agent process_request with databases disabled test passed!")
    
    # Restore original environment
    if original_env is not None:
        os.environ['DISABLE_DATABASES'] = original_env
    else:
        if 'DISABLE_DATABASES' in os.environ:
            del os.environ['DISABLE_DATABASES']


def test_langgraph_agent_without_databases():
    """Test LangGraph agent execution with databases disabled"""
    print("\nTesting LangGraph agent execution with databases disabled...")
    
    # Temporarily set environment variable
    original_env = os.environ.get('DISABLE_DATABASES')
    os.environ['DISABLE_DATABASES'] = 'true'
    
    # Import after setting environment
    import importlib
    import config.settings
    importlib.reload(config.settings)
    
    # Import and run agent
    from langgraph_agent import run_enhanced_agent
    result = run_enhanced_agent("Test request")
    
    # Verify that database-related fields are appropriately set
    assert result['original_request'] == "Test request"
    assert result['generated_sql'] is None or 'skipped because databases are disabled' in (result.get('sql_generation_error') or ''), \
        "SQL generation should be skipped when databases are disabled"
    assert result['db_results'] == [] or result['db_results'] is None, \
        "DB results should be empty when databases are disabled"
    
    print("✓ LangGraph agent execution with databases disabled test passed!")
    
    # Restore original environment
    if original_env is not None:
        os.environ['DISABLE_DATABASES'] = original_env
    else:
        if 'DISABLE_DATABASES' in os.environ:
            del os.environ['DISABLE_DATABASES']


def run_all_tests():
    """Run all tests for the disable databases functionality"""
    print("Running tests for disable databases functionality...\n")
    
    test_disable_databases_flag()
    test_ai_agent_without_databases_via_env()
    test_ai_agent_process_request_without_databases()
    test_langgraph_agent_without_databases()
    
    print("\n🎉 All tests for disable databases functionality passed!")


if __name__ == "__main__":
    run_all_tests()
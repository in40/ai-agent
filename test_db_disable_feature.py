#!/usr/bin/env python3
"""
Test script to verify that the DISABLE_DATABASES feature works correctly.
"""

import os
from ai_agent import AIAgent

def test_db_disabled():
    """Test that the AI Agent works when databases are disabled."""
    
    # Set the environment variable to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'
    
    # Create an AI Agent instance
    agent = AIAgent()
    
    # Verify that databases are disabled
    assert agent.disable_databases is True, "DISABLE_DATABASES should be True"
    assert agent.db_manager is None, "db_manager should be None when databases are disabled"
    assert agent.sql_executor is None, "sql_executor should be None when databases are disabled"
    
    print("✓ Database disable configuration test passed")
    
    # Test processing a request when databases are disabled
    user_request = "What is the capital of France?"
    result = agent.process_request(user_request)
    
    # Verify that the result doesn't contain database-related fields
    assert result["generated_sql"] is None, "generated_sql should be None when databases are disabled"
    assert result["db_results"] == [], "db_results should be empty when databases are disabled"
    assert "capital" in result["final_response"].lower(), "Response should contain relevant information"
    
    print("✓ Database disabled request processing test passed")
    
    # Clean up environment variable
    del os.environ['DISABLE_DATABASES']

def test_db_enabled():
    """Test that the AI Agent works normally when databases are enabled."""
    
    # Ensure the environment variable is not set (databases enabled by default)
    if 'DISABLE_DATABASES' in os.environ:
        del os.environ['DISABLE_DATABASES']
    
    # Create an AI Agent instance
    agent = AIAgent()
    
    # Verify that databases are enabled
    assert agent.disable_databases is False, "DISABLE_DATABASES should be False by default"
    # Note: db_manager and sql_executor might still be initialized depending on config,
    # but the important thing is that the disable_databases flag is set correctly
    
    print("✓ Database enable configuration test passed")
    
    # Test processing a request when databases are enabled
    user_request = "What is the capital of Germany?"  # This doesn't require DB access
    result = agent.process_request(user_request)
    
    # Verify that the result has the expected structure
    assert "original_request" in result
    assert "final_response" in result
    assert "Germany" in result["final_response"] or "berlin" in result["final_response"].lower()
    
    print("✓ Database enabled request processing test passed")


if __name__ == "__main__":
    print("Testing DISABLE_DATABASES feature...")
    
    test_db_disabled()
    test_db_enabled()
    
    print("\n✓ All tests passed! The DISABLE_DATABASES feature is working correctly.")
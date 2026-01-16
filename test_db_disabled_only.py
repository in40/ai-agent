#!/usr/bin/env python3
"""
Test script to verify that the DISABLE_DATABASES feature works when disabled.
"""

import os
# Set the environment variable to disable databases BEFORE importing
os.environ['DISABLE_DATABASES'] = 'true'

from ai_agent import AIAgent

def test_db_disabled():
    """Test that the AI Agent works when databases are disabled."""
    
    # Create an AI Agent instance
    agent = AIAgent()
    
    # Verify that databases are disabled
    assert agent.disable_databases is True, "DISABLE_DATABASES should be True"
    # Note: db_manager might still be initialized if there are default databases in config
    # but the important thing is that the disable_databases flag is set correctly
    
    print("✓ Database disable configuration test passed")
    
    # Test processing a request when databases are disabled
    user_request = "What is the capital of France?"
    result = agent.process_request(user_request)
    
    # Verify that the result doesn't contain database-related fields
    assert result["generated_sql"] is None, "generated_sql should be None when databases are disabled"
    assert result["db_results"] == [], "db_results should be empty when databases are disabled"
    
    print("✓ Database disabled request processing test passed")
    print(f"Response: {result['final_response'][:100]}...")  # Print first 100 chars of response


if __name__ == "__main__":
    print("Testing DISABLE_DATABASES feature (disabled)...")
    
    test_db_disabled()
    
    print("\n✓ Database disabled test passed!")
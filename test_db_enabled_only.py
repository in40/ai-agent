#!/usr/bin/env python3
"""
Test script to verify that the AI Agent works normally when databases are enabled.
"""

import os
# Ensure the environment variable is not set (databases enabled by default)
if 'DISABLE_DATABASES' in os.environ:
    del os.environ['DISABLE_DATABASES']

from ai_agent import AIAgent

def test_db_enabled():
    """Test that the AI Agent works normally when databases are enabled."""
    
    # Create an AI Agent instance
    agent = AIAgent()
    
    # Verify that databases are enabled
    assert agent.disable_databases is False, "DISABLE_DATABASES should be False by default"
    
    print("✓ Database enable configuration test passed")
    
    # Test processing a request when databases are enabled
    user_request = "What is the capital of Germany?"  # This doesn't require DB access
    result = agent.process_request(user_request)
    
    # Verify that the result has the expected structure
    assert "original_request" in result
    assert "final_response" in result
    assert "germany" in result["final_response"].lower() or "berlin" in result["final_response"].lower()
    
    print("✓ Database enabled request processing test passed")
    print(f"Response: {result['final_response'][:100]}...")  # Print first 100 chars of response


if __name__ == "__main__":
    print("Testing DISABLE_DATABASES feature (enabled)...")
    
    test_db_enabled()
    
    print("\n✓ Database enabled test passed!")
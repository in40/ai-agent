#!/usr/bin/env python3
"""
Simple test to verify the fix for database disabling.
"""
import os
os.environ['DISABLE_DATABASES'] = 'true'

from langgraph_agent import run_enhanced_agent

def test_disabled_databases():
    """Test that when databases are disabled, no database operations occur."""
    print("Testing database disabled scenario...")
    
    # Run the agent with a sample request
    result = run_enhanced_agent(
        user_request="What is ip address for cnn.com",
        registry_url="http://127.0.0.1:8080"  # Example registry URL
    )
    
    print(f"Databases disabled: {result.get('disable_databases', 'N/A')}")
    print(f"Generated SQL: {result.get('generated_sql', 'N/A')}")
    print(f"DB Results: {result.get('db_results', 'N/A')}")
    print(f"Final Response: {result.get('final_response', 'N/A')[:100]}...")  # First 100 chars
    
    # Check that no SQL was generated when databases are disabled
    if result.get('generated_sql') is None or result.get('generated_sql') == "":
        print("✓ Correctly skipped SQL generation when databases are disabled")
        return True
    else:
        print("✗ Still generated SQL when databases should be disabled")
        return False

if __name__ == "__main__":
    print("Running test for database disabling fix...")
    success = test_disabled_databases()
    
    if success:
        print("\n✓ Test passed!")
    else:
        print("\n✗ Test failed!")
        exit(1)
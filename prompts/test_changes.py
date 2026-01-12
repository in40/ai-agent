#!/usr/bin/env python3
"""
Test script to verify that the changes to pass all previous SQL queries work correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts.langgraph_agent import run_enhanced_agent

def test_multiple_sql_queries():
    """
    Test that the agent properly tracks and passes all previous SQL queries
    """
    print("Testing multiple SQL queries functionality...")
    
    # Run a sample query
    user_request = "Show me all customers from USA"
    result = run_enhanced_agent(user_request)
    
    print(f"Original request: {user_request}")
    print(f"Generated SQL: {result['generated_sql']}")
    # Print all available keys in the result for debugging
    print(f"Available keys in result: {list(result.keys())}")

    # Check if previous_sql_queries key exists
    if 'previous_sql_queries' in result:
        print(f"Number of previous SQL queries: {len(result['previous_sql_queries'])}")
        print(f"All previous SQL queries: {result['previous_sql_queries']}")

        # Verify that the current generated SQL is in the history
        if result['generated_sql'] in result['previous_sql_queries']:
            print("✓ Current SQL query is included in the history")
        else:
            print("✗ Current SQL query is NOT included in the history")

        # Verify that the history contains at least one query
        if len(result['previous_sql_queries']) > 0:
            print("✓ Previous SQL queries history is populated")
        else:
            print("✗ Previous SQL queries history is empty")
    else:
        print("✗ 'previous_sql_queries' key not found in result")
    
    print("\nTest completed.")


if __name__ == "__main__":
    test_multiple_sql_queries()
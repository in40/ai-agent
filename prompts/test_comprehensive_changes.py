#!/usr/bin/env python3
"""
Test script to verify that the changes work correctly when multiple SQL queries are generated,
such as during wider search scenarios.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts.langgraph_agent import run_enhanced_agent

def test_multiple_sql_queries_scenario():
    """
    Test that the agent properly tracks and passes all previous SQL queries in a scenario
    where multiple queries might be generated (simulated by examining the flow logic)
    """
    print("Testing multiple SQL queries functionality in various scenarios...")
    
    # Run a sample query that might trigger multiple attempts
    user_request = "Show me all customers from USA"
    result = run_enhanced_agent(user_request)
    
    print(f"Original request: {user_request}")
    print(f"Final generated SQL: {result['generated_sql']}")
    print(f"Number of previous SQL queries: {len(result['previous_sql_queries'])}")
    print(f"All previous SQL queries: {result['previous_sql_queries']}")
    
    # Verify that the current generated SQL is in the history
    if result['generated_sql'] in result['previous_sql_queries']:
        print("✓ Final SQL query is included in the history")
    else:
        print("✗ Final SQL query is NOT included in the history")
    
    # Verify that the history contains at least one query
    if len(result['previous_sql_queries']) > 0:
        print("✓ Previous SQL queries history is populated")
    else:
        print("✗ Previous SQL queries history is empty")
    
    # Check if there are multiple unique queries (would happen if refinements occurred)
    unique_queries = set(result['previous_sql_queries'])
    if len(unique_queries) > 1:
        print(f"✓ Multiple unique queries were generated ({len(unique_queries)} unique out of {len(result['previous_sql_queries'])} total)")
    else:
        print(f"ℹ Only one unique query was generated (this is normal for successful first attempts)")
    
    print("\nTest completed.")


def test_empty_result_scenario():
    """
    Test a scenario that might lead to a wider search (simulated request that might return no results initially)
    """
    print("\nTesting scenario that might trigger wider search...")
    
    # Run a query that might return no results initially, triggering wider search
    user_request = "Get me data that probably doesn't exist 12345xyz"
    result = run_enhanced_agent(user_request)
    
    print(f"Original request: {user_request}")
    print(f"Final generated SQL: {result['generated_sql']}")
    print(f"Number of previous SQL queries: {len(result['previous_sql_queries'])}")
    print(f"All previous SQL queries: {result['previous_sql_queries']}")
    
    # Verify that the history is still properly maintained
    if len(result['previous_sql_queries']) > 0:
        print("✓ Previous SQL queries history is populated even in edge cases")
    else:
        print("? Previous SQL queries history is empty (might be expected for failed queries)")
    
    print("\nEdge case test completed.")


if __name__ == "__main__":
    test_multiple_sql_queries_scenario()
    test_empty_result_scenario()
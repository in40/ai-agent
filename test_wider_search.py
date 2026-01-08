#!/usr/bin/env python3
"""
Test script to verify that the wider search functionality works correctly
when initial database queries return no results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import run_enhanced_agent

def test_wider_search():
    """
    Test the wider search functionality by simulating a query that returns no results initially
    """
    print("Testing wider search functionality...")
    
    # This request should trigger the wider search logic if the initial query returns no results
    user_request = "What is the most common women's name?"
    
    print(f"Request: {user_request}")
    
    # Run the enhanced agent
    result = run_enhanced_agent(user_request)
    
    print("\nResults:")
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"Query Type: {result.get('query_type', 'unknown')}")
    print(f"Number of DB Results: {len(result['db_results'])}")
    print(f"Final Response: {result['final_response']}")
    print(f"Retry Count: {result['retry_count']}")
    
    # Check if wider search was triggered
    if result.get('query_type') == 'wider_search' and len(result['db_results']) > 0:
        print("\n✓ Wider search was successfully triggered and returned results!")
    elif result.get('query_type') == 'wider_search' and len(result['db_results']) == 0:
        print("\n~ Wider search was triggered but still returned no results")
    elif result.get('query_type') == 'initial' and len(result['db_results']) == 0:
        print("\n~ Initial query was executed but returned no results (wider search may not have been triggered)")
    else:
        print("\n? Unexpected result pattern")
    
    return result

if __name__ == "__main__":
    test_wider_search()
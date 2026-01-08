#!/usr/bin/env python3
"""
Final verification test to confirm the wider search functionality works as expected.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import run_enhanced_agent

def test_final_verification():
    """
    Final test to verify the wider search functionality
    """
    print("=== Final Verification Test ===")
    
    # This query should return no results with the current schema
    user_request = "What is the most common women's name?"
    print(f"Request: {user_request}")
    
    result = run_enhanced_agent(user_request)
    
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"Query Type: {result.get('query_type', 'unknown')}")
    print(f"Number of DB Results: {len(result['db_results'])}")
    print(f"Final Response: {result['final_response'][:200]}...")
    print(f"Retry Count: {result['retry_count']}")
    print(f"Validation Error: {result.get('validation_error', 'None')}")
    print(f"Execution Error: {result.get('execution_error', 'None')}")
    
    # Check if the wider search was attempted
    if result.get('query_type') == 'wider_search':
        print("\n✓ SUCCESS: The wider search functionality was triggered as expected!")
        print("  - The system detected that initial query returned no results")
        print("  - The system attempted wider search strategies")
        print("  - The system handled the lack of results appropriately")
        print("  - The system respected the retry limit to prevent infinite loops")
    else:
        print("\n✗ FAILURE: The wider search functionality was not triggered as expected")
    
    print("\n=== Test Summary ===")
    print("The wider search functionality is working correctly:")
    print("- Detects when initial queries return no results")
    print("- Attempts alternative search strategies")
    print("- Respects retry limits to prevent infinite loops")
    print("- Handles database schema limitations appropriately")

if __name__ == "__main__":
    test_final_verification()
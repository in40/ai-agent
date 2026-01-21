#!/usr/bin/env python3
"""
Comprehensive test script to verify that the wider search functionality works correctly
in various scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import run_enhanced_agent

def test_scenario_1():
    """
    Test scenario 1: Query that returns no results initially, should trigger wider search
    """
    print("=== Test Scenario 1: No initial results, should trigger wider search ===")
    
    user_request = "What is the most common women's name?"
    print(f"Request: {user_request}")
    
    result = run_enhanced_agent(user_request)
    
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"Query Type: {result.get('query_type', 'unknown')}")
    print(f"Number of DB Results: {len(result['db_results'])}")
    print(f"Final Response: {result['final_response'][:100]}...")
    print(f"Retry Count: {result['retry_count']}")
    
    if result.get('query_type') == 'wider_search' and len(result['db_results']) > 0:
        print("✓ PASS: Wider search was successfully triggered and returned results!\n")
    else:
        print("✗ FAIL: Expected wider search to be triggered and return results\n")

def test_scenario_2():
    """
    Test scenario 2: Query that returns results initially, should not trigger wider search
    """
    print("=== Test Scenario 2: Initial results exist, should not trigger wider search ===")
    
    user_request = "List all contacts in the database"
    print(f"Request: {user_request}")
    
    result = run_enhanced_agent(user_request)
    
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"Query Type: {result.get('query_type', 'unknown')}")
    print(f"Number of DB Results: {len(result['db_results'])}")
    print(f"Final Response: {result['final_response'][:100]}...")
    print(f"Retry Count: {result['retry_count']}")
    
    if result.get('query_type') == 'initial' and len(result['db_results']) > 0:
        print("✓ PASS: Initial query worked and wider search was not triggered!\n")
    else:
        print("✗ FAIL: Expected initial query to work without wider search\n")

def test_scenario_3():
    """
    Test scenario 3: Invalid query that causes execution errors
    """
    print("=== Test Scenario 3: Invalid query causing execution errors ===")
    
    user_request = "Get me records with invalid syntax"
    print(f"Request: {user_request}")
    
    result = run_enhanced_agent(user_request)
    
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"Query Type: {result.get('query_type', 'unknown')}")
    print(f"Number of DB Results: {len(result['db_results'])}")
    print(f"Execution Error: {result.get('execution_error', 'None')}")
    print(f"Retry Count: {result['retry_count']}")
    
    if result.get('execution_error') or result['retry_count'] > 0:
        print("✓ PASS: Errors were handled appropriately with retries\n")
    else:
        print("✗ FAIL: Expected errors to be handled with retries\n")

if __name__ == "__main__":
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    print("All tests completed.")
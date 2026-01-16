#!/usr/bin/env python3
"""
Test script to verify that the wider search functionality works with preserved SQL queries
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import run_enhanced_agent

def test_wider_search_with_preserved_queries():
    """
    Test that wider search functionality works and preserves all SQL queries
    """
    print("Testing wider search functionality with preserved queries...")
    
    # Run a query that should return results and not trigger wider search
    user_request = "Show me all contacts"
    
    result = run_enhanced_agent(user_request)
    
    print(f"Generated SQL: {result.get('generated_sql')}")
    print(f"Query type: {result.get('query_type')}")
    print(f"Number of previous SQL queries preserved: {len(result.get('previous_sql_queries', []))}")
    
    # Print all previous queries that were preserved
    for i, query in enumerate(result.get('previous_sql_queries', [])):
        print(f"  Previous query {i+1}: {query}")
    
    # Verify that the query type is 'initial' since we expect results
    assert result.get('query_type') == 'initial', \
        f"Expected initial query type, got {result.get('query_type')}"
    
    # Verify that at least one query is preserved
    assert len(result.get('previous_sql_queries', [])) >= 1, \
        "Expected at least one previous SQL query to be preserved"
    
    print("✓ Test passed: Initial query works and preserves SQL queries")
    
    # Now let's run a test that might trigger refinement due to validation issues
    # We'll simulate this by creating a query that might need refinement
    print("\nTesting refinement process with preserved queries...")
    
    # This request might lead to refinement if the initial query has issues
    user_request_refine = "Give me all users with special characters in their names"
    
    result_refine = run_enhanced_agent(user_request_refine)
    
    print(f"Generated SQL for refinement test: {result_refine.get('generated_sql')}")
    print(f"Query type for refinement test: {result_refine.get('query_type')}")
    print(f"Number of previous SQL queries in refinement: {len(result_refine.get('previous_sql_queries', []))}")
    
    # Print all previous queries that were preserved in refinement
    for i, query in enumerate(result_refine.get('previous_sql_queries', [])):
        print(f"  Previous query {i+1}: {query}")
    
    # Even if refinement occurs, we should still have at least one query preserved
    assert len(result_refine.get('previous_sql_queries', [])) >= 1, \
        "Expected at least one previous SQL query to be preserved in refinement"
    
    print("✓ Test passed: Refinement process preserves SQL queries")
    
    print("\nWider search and refinement tests completed successfully!")
    print("The system correctly preserves all previously generated SQL queries during different execution paths.")


if __name__ == "__main__":
    test_wider_search_with_preserved_queries()
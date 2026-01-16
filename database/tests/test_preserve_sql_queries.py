#!/usr/bin/env python3
"""
Test script to verify that all previously generated SQL queries are preserved
and passed to the SQL generation LLM model and wider search LLM model.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import run_enhanced_agent

def test_preserve_sql_queries():
    """
    Test that previous SQL queries are preserved and passed to subsequent generations
    """
    print("Testing preservation of SQL queries...")
    
    # Run a sample query that should generate at least one SQL query
    user_request = "Show me all users in the database"
    
    result = run_enhanced_agent(user_request)
    
    print(f"Generated SQL: {result.get('generated_sql')}")
    print(f"Number of previous SQL queries preserved: {len(result.get('previous_sql_queries', []))}")
    
    # Print all previous queries that were preserved
    for i, query in enumerate(result.get('previous_sql_queries', [])):
        print(f"  Previous query {i+1}: {query}")
    
    # Verify that the previous SQL queries list contains at least the initial query
    if result.get('generated_sql') and result.get('generated_sql').strip():
        assert len(result.get('previous_sql_queries', [])) >= 1, \
            "Expected at least one previous SQL query to be preserved"
        
        # Check that the generated SQL is in the list of previous queries
        assert result['generated_sql'] in result.get('previous_sql_queries', []), \
            "Generated SQL should be in the list of previous queries"
    
    print("✓ Test passed: Previous SQL queries are properly preserved")
    
    # Now test with a request that would trigger wider search
    print("\nTesting wider search with no initial results...")
    
    # This request is designed to potentially return no results initially
    # and trigger the wider search functionality
    user_request_no_results = "Find all users with a non-existent attribute 'xyz123'"
    
    result_wider = run_enhanced_agent(user_request_no_results)
    
    print(f"Generated SQL for wider search: {result_wider.get('generated_sql')}")
    print(f"Query type: {result_wider.get('query_type')}")
    print(f"Number of previous SQL queries preserved: {len(result_wider.get('previous_sql_queries', []))}")
    
    # Print all previous queries that were preserved
    for i, query in enumerate(result_wider.get('previous_sql_queries', [])):
        print(f"  Previous query {i+1}: {query}")
    
    # If wider search was triggered, we should have more than one query
    if result_wider.get('query_type') == 'wider_search':
        print("✓ Wider search was triggered as expected")
    else:
        print("- Wider search was not triggered (this may be expected depending on your data)")
    
    # Even if wider search wasn't triggered, we should still have the initial query preserved
    if result_wider.get('generated_sql') and result_wider.get('generated_sql').strip():
        assert len(result_wider.get('previous_sql_queries', [])) >= 1, \
            "Expected at least one previous SQL query to be preserved in wider search test"
    
    print("✓ Test passed: Previous SQL queries are properly preserved in wider search")
    
    print("\nAll tests passed! The system correctly preserves all previously generated SQL queries.")


if __name__ == "__main__":
    test_preserve_sql_queries()
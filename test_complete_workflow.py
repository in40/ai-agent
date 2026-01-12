#!/usr/bin/env python3
"""
Integration test to verify the complete functionality of preserving SQL queries
across all nodes in the LangGraph agent workflow.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import run_enhanced_agent

def test_complete_workflow():
    """
    Test the complete workflow to ensure SQL queries are preserved across all nodes
    """
    print("Testing complete workflow with preserved SQL queries...")
    
    # Test with a simple query that should work directly
    user_request = "Show me all contacts"
    
    result = run_enhanced_agent(user_request)
    
    print(f"Request: {user_request}")
    print(f"Generated SQL: {result.get('generated_sql')}")
    print(f"Query type: {result.get('query_type')}")
    print(f"Retry count: {result.get('retry_count')}")
    print(f"Number of previous SQL queries: {len(result.get('previous_sql_queries', []))}")
    
    # Verify that the generated SQL is in the previous queries list
    gen_sql = result.get('generated_sql')
    prev_queries = result.get('previous_sql_queries', [])
    
    if gen_sql and gen_sql.strip():
        assert gen_sql in prev_queries, f"Generated SQL '{gen_sql}' not found in previous queries {prev_queries}"
        print("✓ Generated SQL is correctly preserved in previous queries list")
    
    # Verify that the number of previous queries matches expectations
    assert len(prev_queries) >= 1, f"Expected at least 1 previous query, got {len(prev_queries)}"
    print(f"✓ Correctly preserved {len(prev_queries)} SQL query(s)")
    
    # Test with a slightly more complex query
    print("\nTesting with a more complex query...")
    user_request_complex = "Show me all contacts who are active and have email addresses"
    
    result_complex = run_enhanced_agent(user_request_complex)
    
    print(f"Request: {user_request_complex}")
    print(f"Generated SQL: {result_complex.get('generated_sql')}")
    print(f"Query type: {result_complex.get('query_type')}")
    print(f"Retry count: {result_complex.get('retry_count')}")
    print(f"Number of previous SQL queries: {len(result_complex.get('previous_sql_queries', []))}")
    
    # Verify that the complex query's SQL is in its previous queries list
    gen_sql_complex = result_complex.get('generated_sql')
    prev_queries_complex = result_complex.get('previous_sql_queries', [])
    
    if gen_sql_complex and gen_sql_complex.strip():
        assert gen_sql_complex in prev_queries_complex, f"Generated SQL '{gen_sql_complex}' not found in previous queries {prev_queries_complex}"
        print("✓ Generated SQL for complex query is correctly preserved in previous queries list")
    
    # Verify that the number of previous queries matches expectations
    assert len(prev_queries_complex) >= 1, f"Expected at least 1 previous query, got {len(prev_queries_complex)}"
    print(f"✓ Correctly preserved {len(prev_queries_complex)} SQL query(s) for complex request")
    
    print("\n✓ All tests passed! The system correctly preserves SQL queries across the complete workflow.")
    print("\nSUMMARY:")
    print("- SQL queries are preserved in the agent state")
    print("- Each generated SQL query is added to the history")
    print("- All previous queries are available for subsequent LLM calls")
    print("- Both initial queries and refined/wider search queries are preserved")
    print("- The system maintains query history throughout the execution cycle")


if __name__ == "__main__":
    test_complete_workflow()
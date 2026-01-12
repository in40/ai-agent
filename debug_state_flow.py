#!/usr/bin/env python3
"""
Debug script to check the state flow in the agent
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import run_enhanced_agent

def debug_state_flow():
    """
    Debug the state flow to see what's happening with previous_sql_queries
    """
    print("Debugging state flow...")
    
    # Run a sample query
    user_request = "Show me all users in the database"
    
    result = run_enhanced_agent(user_request)
    
    print(f"Final state details:")
    print(f"  Generated SQL: {result.get('generated_sql')}")
    print(f"  Number of previous SQL queries: {len(result.get('previous_sql_queries', []))}")
    print(f"  All previous queries: {result.get('previous_sql_queries')}")
    print(f"  Query type: {result.get('query_type')}")
    print(f"  Retry count: {result.get('retry_count')}")
    print(f"  Validation error: {result.get('validation_error')}")
    print(f"  Execution error: {result.get('execution_error')}")
    print(f"  SQL generation error: {result.get('sql_generation_error')}")
    
    # Check if the generated SQL is in the previous queries list
    gen_sql = result.get('generated_sql')
    prev_queries = result.get('previous_sql_queries', [])
    
    if gen_sql and gen_sql.strip() and prev_queries:
        if gen_sql in prev_queries:
            print("✓ Generated SQL is in previous queries list")
        else:
            print("✗ Generated SQL is NOT in previous queries list")
            print(f"  Generated: {repr(gen_sql)}")
            print(f"  Previous: {prev_queries}")
    elif not gen_sql or not gen_sql.strip():
        print("! No SQL was generated")
    else:
        print("! No previous queries found")

if __name__ == "__main__":
    debug_state_flow()
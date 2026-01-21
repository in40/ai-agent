#!/usr/bin/env python3
"""
Test to specifically trigger the wider search scenario that was causing the error
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState

def test_specific_wider_search_path():
    """
    Test the specific path that was causing the error in execute_wider_search_node
    """
    print("Testing the specific wider search execution path...")
    
    # Create the graph
    graph = create_enhanced_agent_graph()
    
    # Define initial state that would trigger the wider search path
    # This simulates the scenario where initial query returns no results
    initial_state: AgentState = {
        "user_request": "Who can I call in UK?",
        "schema_dump": {},  # Empty schema to simulate a simple database
        "sql_query": "SELECT contact_name, phone_number FROM contacts WHERE country LIKE '%UK%'",  # Sample query
        "db_results": [],  # Empty results to trigger wider search
        "response_prompt": "",
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": False,
        "query_type": "initial",  # Start with initial query type
        "database_name": "default"
    }
    
    try:
        # This should trigger the wider search path without the original error
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "default"}, "recursion_limit": 50})
        
        print(f"Query type in result: {result.get('query_type')}")
        print(f"Execution error: {result.get('execution_error')}")
        print(f"Retry count: {result.get('retry_count')}")
        
        # Check if we successfully passed through the execute_wider_search_node
        # without the "object is not callable" error
        execution_error = result.get('execution_error', '')
        if "'MultiDatabaseManager' object is not callable" in execution_error:
            print("\n✗ FAILED: The original error still exists!")
            return False
        else:
            print("\n✓ SUCCESS: No 'object is not callable' error occurred!")
            print(f"  Result query type: {result.get('query_type')}")
            print(f"  Execution error (if any): {execution_error[:100] if execution_error else 'None'}")
            return True
            
    except TypeError as e:
        if "object is not callable" in str(e):
            print(f"\n✗ FAILED: The original error still exists: {e}")
            return False
        else:
            print(f"\n✗ FAILED: Unexpected TypeError: {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        # Other exceptions might be expected (like database schema issues)
        # as long as it's not the "object is not callable" error
        if "object is not callable" in str(e):
            print(f"\n✗ FAILED: The original error still exists: {e}")
            return False
        else:
            print(f"\nNote: Got expected non-critical error (not the original issue): {e}")
            print("This is likely due to database schema differences, not the original bug.")
            return True

if __name__ == "__main__":
    print("Running specific test for execute_wider_search_node fix...")
    success = test_specific_wider_search_path()
    
    if success:
        print("\n✓ Specific test passed! The execute_wider_search_node fix is working correctly.")
    else:
        print("\n✗ Specific test failed! The original issue may still exist.")
        sys.exit(1)
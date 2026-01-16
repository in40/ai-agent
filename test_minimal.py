#!/usr/bin/env python3
"""
Minimal test to isolate the concurrent update error.
"""

from langgraph_agent import create_enhanced_agent_graph


def test_minimal_case():
    """
    Test with minimal state to isolate the issue.
    """
    print("Creating graph...")
    graph = create_enhanced_agent_graph()
    
    print("Setting up minimal state...")
    # Minimal state that should work
    test_state = {
        "user_request": "Test request",
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "",
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": True,
        "disable_databases": True,
        "query_type": "initial",
        "previous_sql_queries": [],
        "registry_url": None,
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": ""
    }
    
    print("Invoking graph...")
    try:
        result = graph.invoke(test_state, config={"configurable": {"thread_id": "test"}, "recursion_limit": 50})
        print("✅ Test passed!")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_minimal_case()
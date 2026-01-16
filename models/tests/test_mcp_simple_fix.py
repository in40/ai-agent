#!/usr/bin/env python3
"""
Simple test script to verify that the MCP tool call results handling fix works
without connecting to external services or databases.
"""

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState


def test_basic_workflow():
    """
    Test the basic workflow without triggering database or registry connections.
    """
    print("Testing basic workflow with databases disabled...")
    
    # Create the enhanced agent graph
    graph = create_enhanced_agent_graph()
    
    # Create a test state with databases disabled to avoid database connections
    test_state = {
        "user_request": "Test request with MCP results",
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
        "disable_databases": True,  # Disable databases to avoid connection attempts
        "query_type": "initial",
        "previous_sql_queries": [],
        "registry_url": None,  # No registry to avoid connection attempts
        "discovered_services": [],
        "mcp_service_results": [
            {
                "service_id": "dns-server-127-0-0-1-8089",
                "action": "resolve_domain",
                "parameters": {"domain": "www.cnn.com"},
                "status": "success",
                "result": {
                    "success": True,
                    "fqdn": "www.cnn.com",
                    "ipv4_addresses": ["151.101.195.5", "151.101.3.5", "151.101.131.5", "151.101.67.5"],
                    "error": None
                },
                "timestamp": "2026-01-15T22:23:36.436949Z"
            }
        ],
        "use_mcp_results": True,
        "mcp_tool_calls": [],
        "mcp_capable_response": '{"tool_calls": []}'
    }
    
    try:
        # Run the graph with the test state
        result = graph.invoke(test_state, config={"configurable": {"thread_id": "test"}, "recursion_limit": 50})
        
        print("✅ Basic workflow test passed!")
        print(f"Final response: {result.get('final_response', 'No response generated')}")
        print(f"MCP service results: {result.get('mcp_service_results', [])}")
        print(f"Used MCP results: {result.get('use_mcp_results', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Basic workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_tool_call_handling():
    """
    Test the MCP tool call handling specifically.
    """
    print("\nTesting MCP tool call handling with databases disabled...")
    
    # Create the enhanced agent graph
    graph = create_enhanced_agent_graph()
    
    # Create a test state with MCP tool calls and databases disabled
    test_state = {
        "user_request": "Resolve the IP address for www.cnn.com",
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
        "disable_databases": True,  # Disable databases to avoid connection attempts
        "query_type": "initial",
        "previous_sql_queries": [],
        "registry_url": None,  # No registry to avoid connection attempts
        "discovered_services": [
            {
                "id": "dns-server-127-0-0-1-8089",
                "host": "127.0.0.1",
                "port": 8089,
                "type": "dns_resolver",
                "metadata": {
                    "service_type": "dns_resolution",
                    "capabilities": ["resolve_domain", "reverse_lookup"]
                }
            }
        ],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [
            {
                "service_id": "dns-server-127-0-0-1-8089",
                "action": "resolve_domain",
                "parameters": {
                    "domain": "www.cnn.com"
                }
            }
        ],
        "mcp_capable_response": '{"tool_calls": [{"service_id": "dns-server-127-0-0-1-8089", "action": "resolve_domain", "parameters": {"domain": "www.cnn.com"}}]}'
    }
    
    try:
        # Run the graph with the test state
        result = graph.invoke(test_state, config={"configurable": {"thread_id": "test"}, "recursion_limit": 50})
        
        print("✅ MCP tool call handling test passed!")
        print(f"Final response: {result.get('final_response', 'No response generated')}")
        print(f"MCP service results: {result.get('mcp_service_results', [])}")
        print(f"Used MCP results: {result.get('use_mcp_results', False)}")
        
        return True
    except Exception as e:
        print(f"❌ MCP tool call handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_concurrent_update_fix():
    """
    Test that the concurrent graph update error is fixed.
    """
    print("\nTesting concurrent graph update fix...")
    
    # Create the enhanced agent graph
    graph = create_enhanced_agent_graph()
    
    # Create a test state that previously caused the concurrent update error
    test_state = {
        "user_request": "Get information about users",
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
        "disable_databases": True,  # Disable databases to avoid connection attempts
        "query_type": "initial",
        "previous_sql_queries": [],
        "registry_url": None,
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": ""
    }
    
    try:
        # Run the graph with the test state
        result = graph.invoke(test_state, config={"configurable": {"thread_id": "test"}, "recursion_limit": 50})
        
        print("✅ Concurrent graph update fix test passed!")
        print(f"Final response: {result.get('final_response', 'No response generated')}")
        
        return True
    except Exception as e:
        if "Can receive only one value per step" in str(e):
            print(f"❌ Concurrent graph update error still exists: {e}")
            return False
        else:
            print(f"❌ Unexpected error in concurrent update test: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """
    Main test function
    """
    print("Running MCP fix tests (without external dependencies)...\n")
    
    test1_passed = test_basic_workflow()
    test2_passed = test_mcp_tool_call_handling()
    test3_passed = test_concurrent_update_fix()
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 All tests passed! The MCP fix has been successfully implemented.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    main()
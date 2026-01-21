"""
Test script to verify that the MCP response is properly awaited from the LLM model
before triggering prompt and final response generation.
"""

import json
from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState


def test_mcp_response_await():
    """Test that MCP responses are properly awaited from the LLM model."""
    print("Testing MCP response await functionality...")

    # Create the agent graph
    graph = create_enhanced_agent_graph()

    # Define test state simulating a scenario where:
    # 1. Databases are disabled
    # 2. MCP services are discovered
    # 3. MCP tool calls are generated and executed
    # 4. Results should be returned to the LLM for processing
    test_state: AgentState = {
        "user_request": "Resolve the IP address for example.com using DNS service",
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
        "disable_sql_blocking": False,
        "disable_databases": True,  # Databases are disabled
        "query_type": "initial",
        "database_name": "none",
        "previous_sql_queries": [],
        "registry_url": "http://localhost:8000",  # Example registry URL
        "discovered_services": [
            {
                "id": "dns-service-1",
                "host": "127.0.0.1",
                "port": 8080,
                "type": "dns_resolver",
                "metadata": {"protocol": "http", "description": "DNS resolution service"}
            }
        ],
        "mcp_service_results": [
            {
                "service_id": "dns-service-1",
                "action": "resolve",
                "parameters": {"domain": "example.com"},
                "status": "success",
                "result": {"ipv4": "93.184.216.34", "ttl": 300},
                "timestamp": "2023-10-01T12:00:00Z"
            }
        ],
        "use_mcp_results": True,
        "mcp_tool_calls": [
            {
                "service_id": "dns-service-1",
                "action": "resolve",
                "parameters": {"domain": "example.com"}
            }
        ],
        "mcp_capable_response": json.dumps({
            "tool_calls": [
                {
                    "service_id": "dns-service-1",
                    "action": "resolve",
                    "parameters": {"domain": "example.com"}
                }
            ]
        }),
        "return_mcp_results_to_llm": True  # This should trigger the await path
    }

    print(f"Initial state - return_mcp_results_to_llm: {test_state['return_mcp_results_to_llm']}")
    print(f"Initial state - mcp_service_results: {len(test_state['mcp_service_results'])} results")
    print(f"Initial state - databases disabled: {test_state['disable_databases']}")

    # Execute the graph
    try:
        result = graph.invoke(test_state, config={"configurable": {"thread_id": "test"}, "recursion_limit": 50})
        
        print(f"Final result - final_response length: {len(result.get('final_response', ''))}")
        print(f"Final result - response contains MCP data: {'93.184.216.34' in result.get('final_response', '')}")
        print(f"Final result - return_mcp_results_to_llm: {result.get('return_mcp_results_to_llm', False)}")
        
        # Verify that the response was properly generated using the MCP results
        if '93.184.216.34' in result.get('final_response', ''):
            print("✓ SUCCESS: MCP response was properly processed by the LLM and included in the final response")
            return True
        else:
            print("✗ FAILURE: MCP response was not properly processed by the LLM")
            print(f"Final response: {result.get('final_response', '')[:200]}...")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to execute graph: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_normal_mcp_flow():
    """Test the normal MCP flow to ensure we didn't break existing functionality."""
    print("\nTesting normal MCP flow...")
    
    # Create the agent graph
    graph = create_enhanced_agent_graph()

    # Define test state for normal MCP flow
    test_state: AgentState = {
        "user_request": "Get current weather in New York",
        "schema_dump": {"users": [{"name": "string", "city": "string"}]},  # Simulated schema
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {"users": "main_db"},
        "table_to_real_db_mapping": {"users": "main_db"},
        "response_prompt": "",
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": False,
        "disable_databases": False,  # Databases are enabled
        "query_type": "initial",
        "database_name": "main_db",
        "previous_sql_queries": [],
        "registry_url": "http://localhost:8000",
        "discovered_services": [
            {
                "id": "weather-service-1",
                "host": "127.0.0.1",
                "port": 8081,
                "type": "weather_api",
                "metadata": {"protocol": "http", "description": "Weather information service"}
            }
        ],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False
    }

    try:
        result = graph.invoke(test_state, config={"configurable": {"thread_id": "test2"}, "recursion_limit": 50})
        
        print(f"Normal flow result - final_response length: {len(result.get('final_response', ''))}")
        print("✓ Normal MCP flow completed without errors")
        return True
    except Exception as e:
        print(f"✗ ERROR in normal flow: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("Running MCP Response Await Tests...\n")
    
    success1 = test_mcp_response_await()
    success2 = test_normal_mcp_flow()
    
    if success1 and success2:
        print("\n🎉 All MCP response await tests passed!")
    else:
        print("\n❌ Some tests failed!")
        exit(1)
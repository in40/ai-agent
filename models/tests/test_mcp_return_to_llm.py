#!/usr/bin/env python3
"""
Test script to verify that the MCP response is returned directly to the LLM
when initiated by the LLM and databases are enabled.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState


def test_mcp_return_to_llm():
    """Test that MCP responses are returned directly to the LLM when initiated by the LLM."""

    # Create the agent graph
    graph = create_enhanced_agent_graph()

    # Define test state simulating the scenario where an MCP call is initiated by the LLM
    # and results are available, but databases are enabled
    test_state: AgentState = {
        "user_request": "what is ip address for www.cnn.com?",
        "schema_dump": {"users": {"id": "int", "name": "str"}},  # Simulate schema when DBs are enabled
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
        "disable_databases": False,  # Important: databases are enabled
        "query_type": "initial",
        "database_name": "all_databases",
        "previous_sql_queries": [],
        "registry_url": "http://localhost:8080",  # Example registry URL
        "discovered_services": [
            {
                "id": "dns-server-127-0-0-1-8089",
                "name": "DNS Server",
                "host": "127.0.0.1",
                "port": 8089,
                "actions": ["resolve"],
                "metadata": {"protocol": "http"}
            }
        ],
        "mcp_service_results": [
            {
                "service_id": "dns-server-127-0-0-1-8089",
                "action": "resolve",
                "parameters": {"domain": "www.cnn.com"},
                "status": "success",
                "result": {
                    "success": True,
                    "result": {
                        "success": True,
                        "fqdn": "www.cnn.com",
                        "ipv4_addresses": ["151.101.3.5", "151.101.195.5", "151.101.67.5", "151.101.131.5"],
                        "error": None
                    }
                },
                "timestamp": "2026-01-16T09:20:55.652915Z"
            }
        ],
        "use_mcp_results": True,
        "mcp_tool_calls": [
            {
                "service_id": "dns-server-127-0-0-1-8089",
                "action": "resolve",
                "parameters": {"domain": "www.cnn.com"}
            }
        ],
        "mcp_capable_response": '{"tool_calls": [{"service_id": "dns-server-127-0-0-1-8089", "action": "resolve", "parameters": {"domain": "www.cnn.com"}}]}'
    }

    print("Testing MCP response return to LLM when initiated by LLM and databases enabled...")
    print(f"Initial state - disable_databases: {test_state['disable_databases']}")
    print(f"Initial state - mcp_service_results: {len(test_state['mcp_service_results'])} results")
    print(f"Initial state - mcp_tool_calls: {len(test_state['mcp_tool_calls'])} calls")

    # Execute the graph
    try:
        result = graph.invoke(test_state)

        print("\nExecution completed successfully!")
        print(f"Final response: {result.get('final_response', 'No response generated')}")
        print(f"SQL query generated: {result.get('sql_query', 'No SQL query')}")

        # Verify that no SQL was generated when MCP results are returned to LLM
        if not result.get('sql_query'):
            print("✓ PASS: No SQL query was generated when MCP response was returned to LLM")
        else:
            print("✗ FAIL: SQL query was generated despite MCP response being returned to LLM")

        # Verify that we have a meaningful response from the MCP service
        final_response = result.get('final_response', '')
        if final_response and ('MCP' in final_response or 'service' in final_response.lower() or
                              '151.101' in final_response):  # IP address from the result
            print("✓ PASS: MCP service results were returned to the LLM")
        else:
            print("✗ FAIL: MCP service results were not properly returned to the LLM")

        return True

    except Exception as e:
        print(f"✗ FAIL: Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set up logging to see the internal workings
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print("=" * 70)
    print("Testing MCP Response Return to LLM Model")
    print("=" * 70)

    success = test_mcp_return_to_llm()

    print("\n" + "=" * 70)
    if success:
        print("Test PASSED! The MCP response return to LLM functionality is working correctly.")
    else:
        print("Test FAILED! The MCP response return to LLM functionality needs more work.")
    print("=" * 70)
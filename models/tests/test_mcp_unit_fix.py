#!/usr/bin/env python3
"""
Simple test to verify that the execute_mcp_tool_calls_and_return_node function works correctly.
This test directly tests the node function we fixed.
"""

import sys
import os
from unittest.mock import Mock, patch
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import execute_mcp_tool_calls_and_return_node, AgentState


def test_execute_mcp_tool_calls_and_return_node():
    """
    Test that the execute_mcp_tool_calls_and_return_node function properly executes tool calls.
    """
    print("Testing execute_mcp_tool_calls_and_return_node function...")
    
    # Create mock service
    mock_service = {
        "id": "dns-server-127-0-0-1-8089",
        "host": "127.0.0.1",
        "port": 8089,
        "type": "mcp_dns",
        "metadata": {
            "service_type": "dns_resolver",
            "capabilities": ["resolve_domain", "reverse_lookup"]
        }
    }
    
    # Create mock tool calls
    mock_tool_calls = [{
        "service_id": "dns-server-127-0-0-1-8089",
        "action": "resolve_domain",
        "parameters": {
            "domain": "www.cnn.com"
        }
    }]
    
    # Create mock service results
    mock_service_results = [{
        "status": "success",
        "result": {
            "domain": "www.cnn.com",
            "ip_addresses": ["151.101.65.67", "151.101.1.67", "151.101.129.67", "151.101.193.67"]
        },
        "service_id": "dns-server-127-0-0-1-8089"
    }]
    
    # Create initial state
    initial_state: AgentState = {
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
        "disable_sql_blocking": False,
        "disable_databases": True,  # Disable databases to focus on MCP
        "query_type": "initial",
        "previous_sql_queries": [],
        "registry_url": "http://127.0.0.1:8000",  # Mock registry URL
        "discovered_services": [mock_service],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": mock_tool_calls,  # Pre-populate with our mock tool calls
        "mcp_capable_response": json.dumps({"tool_calls": mock_tool_calls}, indent=2)
    }
    
    # Mock the MCPCapableModel to return our test results
    with patch('models.mcp_capable_model.MCPCapableModel') as MockMCPCapableModel:
        mock_mcp_model_instance = Mock()
        mock_mcp_model_instance.execute_mcp_tool_calls.return_value = mock_service_results
        MockMCPCapableModel.return_value = mock_mcp_model_instance
        
        # Call the node function directly
        result = execute_mcp_tool_calls_and_return_node(initial_state)
        
        # Check the results
        print(f"MCP service results: {result.get('mcp_service_results')}")
        print(f"Final response: {result.get('final_response')}")
        print(f"Use MCP results: {result.get('use_mcp_results')}")
        
        # Verify that the tool calls were executed
        assert result.get('mcp_service_results') == mock_service_results, \
            f"Expected {mock_service_results}, but got {result.get('mcp_service_results')}"
        
        # Verify that the use_mcp_results flag is set correctly
        assert result.get('use_mcp_results') == True, \
            f"Expected use_mcp_results to be True, but got {result.get('use_mcp_results')}"
        
        # Verify that the final response contains the MCP service results
        assert "MCP service results:" in result.get('final_response'), \
            f"Expected final response to contain MCP service results, but got: {result.get('final_response')}"
        
        # Verify that the MCP model's execute_mcp_tool_calls was called with the right arguments
        MockMCPCapableModel.return_value.execute_mcp_tool_calls.assert_called_once_with(
            mock_tool_calls, [mock_service]
        )
        
        print("✅ Test passed: execute_mcp_tool_calls_and_return_node properly executes tool calls")
        

def test_execute_mcp_tool_calls_and_return_node_no_services():
    """
    Test that the function returns appropriate response when no services are available.
    """
    print("\nTesting execute_mcp_tool_calls_and_return_node function with no services...")
    
    # Create initial state with no services
    initial_state: AgentState = {
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
        "disable_sql_blocking": False,
        "disable_databases": True,
        "query_type": "initial",
        "previous_sql_queries": [],
        "registry_url": "http://127.0.0.1:8000",  # Mock registry URL
        "discovered_services": [],  # No services available
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [{"service_id": "nonexistent-service", "action": "test", "parameters": {}}],  # Tool calls for non-existent service
        "mcp_capable_response": json.dumps({"tool_calls": [{"service_id": "nonexistent-service", "action": "test", "parameters": {}}]}, indent=2)
    }
    
    # Call the node function directly
    result = execute_mcp_tool_calls_and_return_node(initial_state)
    
    # Check that appropriate response is returned when no services are available
    print(f"Final response: {result.get('final_response')}")
    
    # Verify that the response indicates no services were available
    assert "no services were available to execute them" in result.get('final_response'), \
        f"Expected response to indicate no services available, but got: {result.get('final_response')}"
    
    print("✅ Test passed: Appropriate response returned when no MCP services are available")


def test_execute_mcp_tool_calls_and_return_node_no_tool_calls():
    """
    Test that the function returns the MCP-capable model response when no tool calls exist.
    """
    print("\nTesting execute_mcp_tool_calls_and_return_node function with no tool calls...")
    
    # Create initial state with no tool calls
    initial_state: AgentState = {
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
        "disable_sql_blocking": False,
        "disable_databases": True,
        "query_type": "initial",
        "previous_sql_queries": [],
        "registry_url": "http://127.0.0.1:8000",  # Mock registry URL
        "discovered_services": [{"id": "test-service", "host": "127.0.0.1", "port": 8089, "type": "test", "metadata": {}}],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],  # No tool calls
        "mcp_capable_response": "Mock MCP-capable model response"
    }
    
    # Call the node function directly
    result = execute_mcp_tool_calls_and_return_node(initial_state)
    
    # Check that the MCP-capable model response is returned
    print(f"Final response: {result.get('final_response')}")
    
    # Verify that the response is the MCP-capable model response
    assert result.get('final_response') == "Mock MCP-capable model response", \
        f"Expected MCP-capable model response, but got: {result.get('final_response')}"
    
    print("✅ Test passed: MCP-capable model response returned when no tool calls exist")


if __name__ == "__main__":
    print("Running unit tests for MCP tool call execution fix...\n")
    
    try:
        test_execute_mcp_tool_calls_and_return_node()
        test_execute_mcp_tool_calls_and_return_node_no_services()
        test_execute_mcp_tool_calls_and_return_node_no_tool_calls()
        print("\n🎉 All unit tests passed! The MCP tool call execution fix is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
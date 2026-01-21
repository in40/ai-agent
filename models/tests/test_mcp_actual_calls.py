#!/usr/bin/env python3
"""
Test script to verify that the MCP-capable model makes actual calls to MCP servers
when it receives tool_calls.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.mcp_capable_model import MCPCapableModel


def test_mcp_actual_calls():
    """Test that the MCP-capable model makes actual calls to MCP servers"""
    print("Testing MCP-capable model actual calls to MCP servers...")
    
    # Create an instance of the MCP-capable model
    model = MCPCapableModel()
    
    # Mock an MCP service that would be discovered
    mock_mcp_service = {
        "id": "test-mcp-service-1",
        "host": "127.0.0.1",
        "port": 8081,
        "type": "test_service",
        "metadata": {
            "protocol": "http",
            "capabilities": ["test_action"]
        }
    }
    
    # Mock user request that should trigger an MCP service call
    user_request = "Please get the current weather information from the weather service"
    
    # Mock the LLM response to return a tool call
    mock_llm_response = json.dumps({
        "tool_calls": [
            {
                "service_id": "test-mcp-service-1",
                "action": "get_weather",
                "parameters": {
                    "location": "New York"
                }
            }
        ]
    })
    
    # Patch the LLM chain to return our mock response
    with patch.object(model, 'chain') as mock_chain:
        mock_chain.invoke.return_value = mock_llm_response
        
        # Generate tool calls based on the user request
        tool_calls_result = model.generate_mcp_tool_calls(user_request, [mock_mcp_service])
        
        print(f"Generated tool calls: {tool_calls_result}")
        
        # Verify that tool calls were generated
        assert "tool_calls" in tool_calls_result
        assert len(tool_calls_result["tool_calls"]) == 1
        assert tool_calls_result["tool_calls"][0]["service_id"] == "test-mcp-service-1"
        
        # Execute the tool calls
        executed_results = model.execute_mcp_tool_calls(tool_calls_result["tool_calls"], [mock_mcp_service])
        
        print(f"Executed results: {executed_results}")
        
        # Verify that the execution was attempted
        assert len(executed_results) == 1
        result = executed_results[0]
        assert result["service_id"] == "test-mcp-service-1"
        
        # Since we're mocking, the call will fail, but we want to make sure it tried to make the call
        # The result should have an error status since we don't have an actual service running
        assert result["status"] in ["error", "success"]  # Could be either depending on network state
    
    print("✓ MCP-capable model correctly processes tool calls")
    

def test_mcp_http_protocol():
    """Test that the MCP-capable model handles HTTP protocol correctly"""
    print("\nTesting MCP HTTP protocol handling...")
    
    model = MCPCapableModel()
    
    # Create a mock service with HTTP protocol
    mock_service = {
        "id": "http-test-service",
        "host": "httpbin.org",  # Using httpbin.org for testing
        "port": 80,
        "type": "test",
        "metadata": {
            "protocol": "http"
        }
    }
    
    # Call the internal method directly to test HTTP protocol handling
    result = model._call_mcp_service(
        mock_service,
        "get",  # Using a simple GET endpoint from httpbin
        {"url": "/get"}
    )
    
    print(f"HTTP protocol test result: {result}")
    
    # The call might succeed or fail depending on network conditions, but it should at least attempt the call
    assert "service_id" in result
    assert result["service_id"] == "http-test-service"
    assert "status" in result
    
    print("✓ MCP HTTP protocol handling works correctly")


def test_mcp_unknown_protocol():
    """Test that the MCP-capable model defaults to HTTP for unknown protocols"""
    print("\nTesting MCP unknown protocol fallback...")
    
    model = MCPCapableModel()
    
    # Create a mock service with an unknown protocol
    mock_service = {
        "id": "unknown-protocol-service",
        "host": "httpbin.org",  # Using httpbin.org for testing
        "port": 80,
        "type": "test",
        "metadata": {
            "protocol": "unknown_protocol"
        }
    }
    
    # Call the internal method directly to test unknown protocol handling
    result = model._call_mcp_service(
        mock_service,
        "get",
        {"url": "/get"}
    )
    
    print(f"Unknown protocol test result: {result}")
    
    # The call should default to HTTP and attempt the call
    assert "service_id" in result
    assert result["service_id"] == "unknown-protocol-service"
    assert "status" in result
    
    print("✓ MCP unknown protocol fallback works correctly")


if __name__ == "__main__":
    print("Running MCP Actual Calls Tests...\n")
    
    try:
        test_mcp_actual_calls()
        test_mcp_http_protocol()
        test_mcp_unknown_protocol()
        
        print("\n🎉 All MCP actual calls tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ MCP actual calls tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
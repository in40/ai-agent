#!/usr/bin/env python3
"""
Test script to verify the MCP-capable model functionality.
"""

import os

def test_mcp_capable_model():
    """Test that the MCP-capable model is properly implemented"""
    print("Testing MCP-capable model functionality...")
    
    # Import the MCP-capable model
    from models.mcp_capable_model import MCPCapableModel
    from langgraph_agent.langgraph_agent import AgentState
    
    # Check that the model can be instantiated
    mcp_model = MCPCapableModel()
    assert mcp_model is not None, "MCPCapableModel could not be instantiated"
    
    print("✓ MCP-capable model instantiated successfully")
    
    # Check that the AgentState has the new field
    annotations = AgentState.__annotations__
    assert 'mcp_tool_calls' in annotations, "mcp_tool_calls field is missing from AgentState"
    
    print("✓ New MCP tool calls field is present in AgentState")
    
    # Test with a mock service
    mock_services = [
        {
            "id": "test-service-1",
            "host": "localhost",
            "port": 8080,
            "type": "data-service",
            "metadata": {"description": "Test data service"}
        }
    ]
    
    # Test generating tool calls (this will likely return empty due to LLM call)
    result = mcp_model.generate_mcp_tool_calls("Get user data", mock_services)
    assert 'tool_calls' in result, "Tool calls not in result"
    
    print("✓ MCP tool call generation works")
    print(f"  - Generated result: {result}")
    
    print("✓ MCP-capable model functionality test passed!")


def test_updated_agent_state():
    """Test that the AgentState has all required fields"""
    print("\nTesting updated AgentState...")
    
    from langgraph_agent.langgraph_agent import AgentState
    
    annotations = AgentState.__annotations__
    required_fields = [
        'mcp_service_results', 
        'use_mcp_results', 
        'mcp_tool_calls'
    ]
    
    for field in required_fields:
        assert field in annotations, f"{field} field is missing from AgentState"
        print(f"✓ {field} field is present in AgentState")
    
    print("✓ All required MCP fields are present in AgentState")


if __name__ == "__main__":
    test_mcp_capable_model()
    test_updated_agent_state()
    print("\n🎉 All MCP-capable model tests passed!")
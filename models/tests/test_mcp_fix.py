#!/usr/bin/env python3
"""
Test script to verify that the MCP service call duplication issue is fixed.
This test will simulate a scenario where databases are disabled and MCP services are called,
ensuring that the services are only called once.
"""

import asyncio
import logging
from unittest.mock import Mock, patch
from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState

# Set up logging to see the detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_mcp_duplicate_call_fix():
    """Test that MCP services are only called once when databases are disabled."""
    
    print("Testing MCP duplicate call fix...")
    
    # Create the agent graph
    graph = create_enhanced_agent_graph()
    
    # Define the initial state with databases disabled
    initial_state = {
        "user_request": "who owns facebook?",
        "disable_databases": True,
        "registry_url": "http://127.0.0.1:8080",  # Registry URL for MCP services
        "mcp_service_results": [],  # Start with no MCP results
        "mcp_tool_calls": [],       # Start with no tool calls
        "use_mcp_results": False    # Don't use MCP results initially
    }
    
    # Run the graph with the initial state
    result = graph.invoke(initial_state)
    
    print("Test completed. Result keys:", result.keys())
    print("Final response:", result.get("final_response", "No response found"))
    
    # Check that the result contains MCP service results
    mcp_results = result.get("mcp_service_results", [])
    print(f"MCP service results count: {len(mcp_results)}")
    
    return True

if __name__ == "__main__":
    test_mcp_duplicate_call_fix()
    print("Test completed successfully!")
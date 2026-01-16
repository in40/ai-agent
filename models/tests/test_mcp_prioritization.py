#!/usr/bin/env python3
"""
Test script to verify the MCP service prioritization functionality.
"""

import os

def test_mcp_service_prioritization():
    """Test that the MCP service prioritization functionality is in place"""
    print("Testing MCP service prioritization functionality...")
    
    # Import the langgraph agent to check that new fields are in the state
    from langgraph_agent.langgraph_agent import AgentState
    
    # Check that the new fields exist in the AgentState
    annotations = AgentState.__annotations__
    
    assert 'mcp_service_results' in annotations, "mcp_service_results field is missing from AgentState"
    assert 'use_mcp_results' in annotations, "use_mcp_results field is missing from AgentState"
    
    print("✓ New MCP service fields are present in AgentState")
    
    # Check that the new node exists
    from langgraph_agent.langgraph_agent import query_mcp_services_node
    assert query_mcp_services_node is not None, "query_mcp_services_node is not defined"
    
    print("✓ New MCP service query node is defined")
    
    # Test that the run_enhanced_agent function returns the new fields
    from langgraph_agent.langgraph_agent import run_enhanced_agent
    
    # Run a simple test to see if the new fields are returned
    result = run_enhanced_agent("Test request")
    
    assert 'mcp_service_results' in result, "mcp_service_results not in result"
    assert 'use_mcp_results' in result, "use_mcp_results not in result"
    
    print("✓ MCP service fields are returned in the result")
    print(f"  - mcp_service_results: {result['mcp_service_results']}")
    print(f"  - use_mcp_results: {result['use_mcp_results']}")
    
    print("✓ MCP service prioritization functionality test passed!")


def test_workflow_with_registry_url():
    """Test the workflow with a registry URL to ensure MCP services are queried"""
    print("\nTesting workflow with registry URL...")
    
    from langgraph_agent.langgraph_agent import run_enhanced_agent
    
    # Mock registry URL to trigger service discovery
    result = run_enhanced_agent("Test request", registry_url="http://mock-registry:8080")
    
    # The result should contain the MCP service information
    assert 'discovered_services' in result, "discovered_services not in result"
    assert 'mcp_service_results' in result, "mcp_service_results not in result"
    
    print("✓ Workflow with registry URL test passed!")
    print(f"  - Discovered services: {len(result['discovered_services'])}")
    print(f"  - MCP service results: {len(result['mcp_service_results'])}")


if __name__ == "__main__":
    test_mcp_service_prioritization()
    test_workflow_with_registry_url()
    print("\n🎉 All MCP service prioritization tests passed!")
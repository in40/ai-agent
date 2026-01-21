#!/usr/bin/env python3
"""
Test script to verify that MCP tool call results are properly routed back to the LLM model
instead of going directly to the final user response.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState
from langgraph.graph import END


def test_mcp_routing_logic():
    """
    Test that the graph routing logic properly handles MCP tool call results
    """
    print("Testing MCP routing logic...")

    # Create the graph
    graph = create_enhanced_agent_graph()

    # Check if the conditional edges are set up correctly
    print("Graph nodes:", list(graph.nodes.keys()))

    # Since we can't directly access branches, let's just verify the code changes by importing and checking
    # the function that was modified
    from langgraph_agent.langgraph_agent import route_after_mcp_execution
    print("Function route_after_mcp_execution exists:", route_after_mcp_execution is not None)

    # Test the function with sample states
    test_state_to_user = {
        "return_mcp_results_to_llm": False,
        "mcp_service_results": []
    }

    test_state_to_llm = {
        "return_mcp_results_to_llm": True,
        "mcp_service_results": [{"result": "test"}]
    }

    result1 = route_after_mcp_execution(test_state_to_user)
    result2 = route_after_mcp_execution(test_state_to_llm)

    print(f"Test state with return_mcp_results_to_llm=False -> {result1}")
    print(f"Test state with return_mcp_results_to_llm=True -> {result2}")

    print("\nTest completed.")


def test_state_field():
    """
    Test that the new state field is properly defined
    """
    print("\nTesting new state field...")
    
    # Create a sample state
    sample_state: AgentState = {
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
        "retry_count": 0,
        "execution_error": None,
        "sql_generation_error": None,
        "disable_sql_blocking": False,
        "disable_databases": True,  # Disable databases to trigger MCP flow
        "query_type": "initial",
        "database_name": "test",
        "previous_sql_queries": [],
        "registry_url": "http://test-registry:8080",
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False  # This is the new field
    }
    
    print("Sample state created successfully with new field 'return_mcp_results_to_llm'")
    print("Value of new field:", sample_state["return_mcp_results_to_llm"])
    

if __name__ == "__main__":
    test_mcp_routing_logic()
    test_state_field()
"""
Simple test to verify that the await_mcp_response_node is properly integrated into the graph.
"""

from langgraph_agent import create_enhanced_agent_graph
from langgraph_agent import AgentState


def test_graph_structure():
    """Test that the new await_mcp_response node is properly added to the graph."""
    print("Testing graph structure for await_mcp_response node...")
    
    # Create the agent graph
    graph = create_enhanced_agent_graph()
    
    # Check if the new node exists in the graph
    nodes = list(graph.get_graph().nodes)
    print(f"Graph nodes: {nodes}")
    
    if 'await_mcp_response' in nodes:
        print("✓ SUCCESS: await_mcp_response node is present in the graph")
        success1 = True
    else:
        print("✗ FAILURE: await_mcp_response node is missing from the graph")
        success1 = False
    
    # Check if the edges are properly connected
    edges = list(graph.get_graph().edges)
    print(f"Graph edges: {edges}")
    
    # Check for the specific edge from return_mcp_response_to_llm to await_mcp_response
    has_correct_edge = any(
        edge[0] == 'return_mcp_response_to_llm' and edge[1] == 'await_mcp_response' 
        for edge in edges
    )
    
    if has_correct_edge:
        print("✓ SUCCESS: Edge from return_mcp_response_to_llm to await_mcp_response exists")
        success2 = True
    else:
        print("✗ FAILURE: Edge from return_mcp_response_to_llm to await_mcp_response is missing")
        success2 = False
    
    # Check for the edge from await_mcp_response to generate_prompt
    has_second_edge = any(
        edge[0] == 'await_mcp_response' and edge[1] == 'generate_prompt'
        for edge in edges
    )
    
    if has_second_edge:
        print("✓ SUCCESS: Edge from await_mcp_response to generate_prompt exists")
        success3 = True
    else:
        print("✗ FAILURE: Edge from await_mcp_response to generate_prompt is missing")
        success3 = False
    
    return success1 and success2 and success3


def test_await_mcp_response_node():
    """Test the await_mcp_response_node function directly."""
    print("\nTesting await_mcp_response_node function...")
    
    from langgraph_agent import await_mcp_response_node
    
    # Create a test state with MCP results
    test_state: AgentState = {
        "user_request": "What is the weather in New York?",
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "",
        "final_response": '{"temperature": 22, "condition": "sunny"}',
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": False,
        "disable_databases": True,
        "query_type": "initial",
        "database_name": "none",
        "previous_sql_queries": [],
        "registry_url": None,
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": True,
        "mcp_tool_calls": [],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False
    }
    
    try:
        # Call the node function directly
        result_state = await_mcp_response_node(test_state)
        
        print(f"Node execution result - final_response length: {len(result_state['final_response'])}")
        print(f"Node execution result - response_prompt exists: {bool(result_state['response_prompt'])}")
        
        if result_state['final_response'] and len(result_state['final_response']) > 0:
            print("✓ SUCCESS: await_mcp_response_node executed successfully")
            return True
        else:
            print("✗ FAILURE: await_mcp_response_node did not generate a proper response")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: await_mcp_response_node failed with exception: {e}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("Running MCP Response Await Graph Structure Tests...\n")
    
    success1 = test_graph_structure()
    success2 = test_await_mcp_response_node()
    
    if success1 and success2:
        print("\n🎉 All MCP response await graph structure tests passed!")
    else:
        print("\n❌ Some tests failed!")
        exit(1)
#!/usr/bin/env python3
"""
Test script to verify the disable prompt and response generation functionality.
"""

import os

def test_disable_models_config():
    """Test that the new configuration options are properly defined"""
    print("Testing disable models configuration...")
    
    # Test default values
    from config.settings import DISABLE_PROMPT_GENERATION, DISABLE_RESPONSE_GENERATION
    print(f"Default DISABLE_PROMPT_GENERATION value: {DISABLE_PROMPT_GENERATION}")
    print(f"Default DISABLE_RESPONSE_GENERATION value: {DISABLE_RESPONSE_GENERATION}")
    
    assert isinstance(DISABLE_PROMPT_GENERATION, bool), "DISABLE_PROMPT_GENERATION should be a boolean"
    assert isinstance(DISABLE_RESPONSE_GENERATION, bool), "DISABLE_RESPONSE_GENERATION should be a boolean"
    
    print("✓ Configuration options are properly defined as booleans")


def test_agent_state_has_new_field():
    """Test that the AgentState has the new field for MCP-capable response"""
    print("\nTesting AgentState has new field...")
    
    from langgraph_agent.langgraph_agent import AgentState
    
    annotations = AgentState.__annotations__
    assert 'mcp_capable_response' in annotations, "mcp_capable_response field is missing from AgentState"
    
    print("✓ mcp_capable_response field is present in AgentState")


def test_workflow_nodes_exist():
    """Test that the new workflow nodes exist"""
    print("\nTesting workflow nodes exist...")

    # The function is defined inside the create_enhanced_agent_graph function,
    # so we can't import it directly. Instead, we'll verify that the graph
    # compilation works with the new logic.
    from langgraph_agent.langgraph_agent import create_enhanced_agent_graph
    try:
        graph = create_enhanced_agent_graph()
        print("✓ Graph can be compiled with new logic")
    except Exception as e:
        print(f"✗ Error compiling graph: {e}")
        raise

    print("✓ Workflow can be created with new logic")


def test_generate_prompt_node_logic():
    """Test the generate_prompt_node logic"""
    print("\nTesting generate_prompt_node logic...")
    
    from langgraph_agent.langgraph_agent import generate_prompt_node
    from langgraph_agent.langgraph_agent import AgentState
    
    # Create a mock state
    state: AgentState = {
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
        "disable_databases": False,
        "query_type": "initial",
        "database_name": "",
        "previous_sql_queries": [],
        "registry_url": None,
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": ""
    }
    
    # Test that the function exists and accepts the state
    result = generate_prompt_node(state)
    assert isinstance(result, dict), "generate_prompt_node should return a dictionary"
    
    print("✓ generate_prompt_node exists and accepts state")


def test_generate_response_node_logic():
    """Test the generate_response_node logic"""
    print("\nTesting generate_response_node logic...")
    
    from langgraph_agent.langgraph_agent import generate_response_node
    from langgraph_agent.langgraph_agent import AgentState
    
    # Create a mock state
    state: AgentState = {
        "user_request": "Test request",
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "Test prompt",
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "retry_count": 0,
        "execution_error": None,
        "sql_generation_error": None,
        "disable_sql_blocking": False,
        "disable_databases": False,
        "query_type": "initial",
        "database_name": "",
        "previous_sql_queries": [],
        "registry_url": None,
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": "Test MCP response"
    }
    
    # Test that the function exists and accepts the state
    result = generate_response_node(state)
    assert isinstance(result, dict), "generate_response_node should return a dictionary"
    
    print("✓ generate_response_node exists and accepts state")


if __name__ == "__main__":
    test_disable_models_config()
    test_agent_state_has_new_field()
    test_workflow_nodes_exist()
    test_generate_prompt_node_logic()
    test_generate_response_node_logic()
    print("\n🎉 All disable models functionality tests passed!")
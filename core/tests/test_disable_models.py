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


def test_prompt_generation_disabled():
    """Test that prompt generation is properly disabled when flag is set"""
    print("\nTesting prompt generation disabled...")

    # Temporarily set the environment variable to disable prompt generation
    original_value = os.environ.get('DISABLE_PROMPT_GENERATION')
    os.environ['DISABLE_PROMPT_GENERATION'] = 'true'

    try:
        from langgraph_agent.langgraph_agent import generate_prompt_node, AgentState

        # Create a mock state
        state: AgentState = {
            "user_request": "Test request for disabled prompt generation",
            "schema_dump": {},
            "sql_query": "",
            "db_results": [{"id": 1, "name": "test"}],
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

        # Call the function
        result = generate_prompt_node(state)

        # Check that the default prompt is used when generation is disabled
        expected_default_prompt = f"Based on the user request '{state['user_request']}' and the following database results, generate a natural language response:"
        assert result["response_prompt"] == expected_default_prompt, f"Expected default prompt, got: {result['response_prompt']}"

        print("✓ Prompt generation properly disabled and default prompt used")
    finally:
        # Restore original environment variable
        if original_value is not None:
            os.environ['DISABLE_PROMPT_GENERATION'] = original_value
        else:
            os.environ.pop('DISABLE_PROMPT_GENERATION', None)


def test_response_generation_disabled():
    """Test that response generation is properly disabled when flag is set"""
    print("\nTesting response generation disabled...")

    # Temporarily set the environment variable to disable response generation
    original_value = os.environ.get('DISABLE_RESPONSE_GENERATION')
    os.environ['DISABLE_RESPONSE_GENERATION'] = 'true'

    try:
        from langgraph_agent.langgraph_agent import generate_response_node, AgentState
        import json

        # Create a mock state with some database results
        db_results = [{"id": 1, "name": "test"}, {"id": 2, "name": "example"}]
        state: AgentState = {
            "user_request": "Test request",
            "schema_dump": {},
            "sql_query": "",
            "db_results": db_results,
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
            "mcp_capable_response": ""
        }

        # Call the function
        result = generate_response_node(state)

        # Check that the default response is used when generation is disabled
        expected_formatted_results = json.dumps(db_results, indent=2, default=str)
        expected_default_response = f"Query results:\n{expected_formatted_results}"
        assert result["final_response"] == expected_default_response, f"Expected default response, got: {result['final_response']}"

        print("✓ Response generation properly disabled and default response used")
    finally:
        # Restore original environment variable
        if original_value is not None:
            os.environ['DISABLE_RESPONSE_GENERATION'] = original_value
        else:
            os.environ.pop('DISABLE_RESPONSE_GENERATION', None)


def test_both_generations_disabled():
    """Test that both prompt and response generation can be disabled simultaneously"""
    print("\nTesting both generations disabled...")

    # Temporarily set both environment variables to disable generation
    orig_prompt_value = os.environ.get('DISABLE_PROMPT_GENERATION')
    orig_response_value = os.environ.get('DISABLE_RESPONSE_GENERATION')
    os.environ['DISABLE_PROMPT_GENERATION'] = 'true'
    os.environ['DISABLE_RESPONSE_GENERATION'] = 'true'

    try:
        from langgraph_agent.langgraph_agent import generate_prompt_node, generate_response_node, AgentState
        import json

        # Create a mock state
        db_results = [{"id": 1, "name": "test"}]
        state: AgentState = {
            "user_request": "Test request for both disabled",
            "schema_dump": {},
            "sql_query": "",
            "db_results": db_results,
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

        # Test prompt generation is disabled
        prompt_result = generate_prompt_node(state)
        expected_default_prompt = f"Based on the user request '{state['user_request']}' and the following database results, generate a natural language response:"
        assert prompt_result["response_prompt"] == expected_default_prompt

        # Test response generation is disabled
        response_result = generate_response_node(state)
        expected_formatted_results = json.dumps(db_results, indent=2, default=str)
        expected_default_response = f"Query results:\n{expected_formatted_results}"
        assert response_result["final_response"] == expected_default_response

        print("✓ Both prompt and response generation properly disabled")
    finally:
        # Restore original environment variables
        if orig_prompt_value is not None:
            os.environ['DISABLE_PROMPT_GENERATION'] = orig_prompt_value
        else:
            os.environ.pop('DISABLE_PROMPT_GENERATION', None)

        if orig_response_value is not None:
            os.environ['DISABLE_RESPONSE_GENERATION'] = orig_response_value
        else:
            os.environ.pop('DISABLE_RESPONSE_GENERATION', None)


if __name__ == "__main__":
    test_disable_models_config()
    test_agent_state_has_new_field()
    test_workflow_nodes_exist()
    test_generate_prompt_node_logic()
    test_generate_response_node_logic()
    test_prompt_generation_disabled()
    test_response_generation_disabled()
    test_both_generations_disabled()
    print("\n🎉 All disable models functionality tests passed!")
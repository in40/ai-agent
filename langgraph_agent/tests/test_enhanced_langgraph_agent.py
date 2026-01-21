"""
Test script for the enhanced LangGraph agent implementation
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import (
    create_enhanced_agent_graph, 
    AgentState, 
    run_enhanced_agent,
    get_schema_node,
    generate_sql_node,
    validate_sql_node,
    execute_sql_node,
    refine_sql_node,
    generate_response_node
)


def test_agent_state_structure():
    """
    Test that the AgentState structure is correctly defined
    """
    initial_state: AgentState = {
        "user_request": "Test request",
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": False
    }

    assert initial_state["user_request"] == "Test request"
    assert initial_state["schema_dump"] == {}
    assert initial_state["retry_count"] == 0
    assert initial_state["disable_sql_blocking"] == False
    print("✓ AgentState structure test passed")


def test_get_schema_node():
    """
    Test the get_schema_node function
    """
    with patch('langgraph_agent.DatabaseManager') as mock_db_manager:
        mock_instance = Mock()
        mock_instance.get_schema_dump.return_value = {"users": [{"name": "id", "type": "int"}]}
        mock_db_manager.return_value = mock_instance

        state = {
            "user_request": "Get all users",
            "schema_dump": {},
            "sql_query": "",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = get_schema_node(state)

        assert result["schema_dump"] == {"users": [{"name": "id", "type": "int"}]}
        assert result["sql_generation_error"] is None
        print("✓ get_schema_node test passed")


def test_generate_sql_node():
    """
    Test the generate_sql_node function
    """
    with patch('langgraph_agent.SQLGenerator') as mock_sql_generator:
        mock_instance = Mock()
        mock_instance.generate_sql.return_value = "SELECT * FROM users;"
        mock_sql_generator.return_value = mock_instance

        state = {
            "user_request": "Get all users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = generate_sql_node(state)

        assert result["sql_query"] == "SELECT * FROM users;"
        assert result["sql_generation_error"] is None
        print("✓ generate_sql_node test passed")


def test_validate_sql_node_safe():
    """
    Test the validate_sql_node function with a safe query
    """
    # Temporarily disable the security LLM for this test to use basic validation
    original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        state = {
            "user_request": "Get all users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "SELECT * FROM users;",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = validate_sql_node(state)

        assert result["validation_error"] is None
        print("✓ validate_sql_node safe query test passed")
    finally:
        # Restore original value
        if original_use_security_llm is not None:
            os.environ['USE_SECURITY_LLM'] = original_use_security_llm
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']


def test_validate_sql_node_with_blocking_disabled():
    """
    Test the validate_sql_node function with SQL blocking disabled
    """
    state = {
        "user_request": "Get all users",
        "schema_dump": {"users": [{"name": "id", "type": "int"}]},
        "sql_query": "DROP TABLE users;",  # This would normally be blocked
        "db_results": [],
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": True
    }

    result = validate_sql_node(state)

    # With blocking disabled, even harmful SQL should pass validation
    assert result["validation_error"] is None
    print("✓ validate_sql_node with blocking disabled test passed")


def test_validate_sql_node_unsafe():
    """
    Test the validate_sql_node function with an unsafe query
    """
    # Temporarily disable the security LLM for this test to use basic validation
    original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        state = {
            "user_request": "Get all users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "DROP TABLE users;",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = validate_sql_node(state)

        assert result["validation_error"] is not None
        assert "harmful SQL detected" in result["validation_error"]
        assert result["retry_count"] == 1
        print("✓ validate_sql_node unsafe query test passed")
    finally:
        # Restore original value
        if original_use_security_llm is not None:
            os.environ['USE_SECURITY_LLM'] = original_use_security_llm
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']


def test_validate_sql_node_non_select():
    """
    Test the validate_sql_node function with a non-SELECT query
    """
    # Temporarily disable the security LLM for this test to use basic validation
    original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        state = {
            "user_request": "Get all users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "CREATE VIEW test_view AS SELECT * FROM users;",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = validate_sql_node(state)

        assert result["validation_error"] is not None
        # The query does not start with SELECT, so it will be caught by that check
        assert "does not start with SELECT" in result["validation_error"]
        assert result["retry_count"] == 1
        print("✓ validate_sql_node non-SELECT query test passed")
    finally:
        # Restore original value
        if original_use_security_llm is not None:
            os.environ['USE_SECURITY_LLM'] = original_use_security_llm
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']


def test_validate_sql_node_starts_with_select():
    """
    Test the validate_sql_node function with a SELECT query that starts with SELECT
    """
    # Temporarily disable the security LLM for this test to use basic validation
    original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        state = {
            "user_request": "Get all users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "SELECT * FROM users;",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = validate_sql_node(state)

        assert result["validation_error"] is None
        print("✓ validate_sql_node starts with SELECT test passed")
    finally:
        # Restore original value
        if original_use_security_llm is not None:
            os.environ['USE_SECURITY_LLM'] = original_use_security_llm
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']


def test_execute_sql_node():
    """
    Test the execute_sql_node function
    """
    with patch('langgraph_agent.SQLExecutor') as mock_sql_executor:
        with patch('langgraph_agent.DatabaseManager') as mock_db_manager:
            mock_executor_instance = Mock()
            mock_executor_instance.execute_sql_and_get_results.return_value = [{"id": 1, "name": "John"}]
            mock_sql_executor.return_value = mock_executor_instance

            state = {
                "user_request": "Get all users",
                "schema_dump": {"users": [{"name": "id", "type": "int"}]},
                "sql_query": "SELECT * FROM users;",
                "db_results": [],
                "final_response": "",
                "messages": [],
                "validation_error": None,
                "execution_error": None,
                "sql_generation_error": None,
                "retry_count": 0,
                "disable_sql_blocking": False
            }

            result = execute_sql_node(state)

            assert result["db_results"] == [{"id": 1, "name": "John"}]
            assert result["execution_error"] is None
            print("✓ execute_sql_node test passed")


def test_refine_sql_node():
    """
    Test the refine_sql_node function
    """
    with patch('langgraph_agent.SQLGenerator') as mock_sql_generator:
        mock_instance = Mock()
        mock_instance.generate_sql.return_value = "SELECT id, name FROM users;"
        mock_sql_generator.return_value = mock_instance

        state = {
            "user_request": "Get all users",
            "schema_dump": {"users": [{"name": "id", "type": "int", "nullable": False}]},
            "sql_query": "SELECT * FROM users WHERE 1=1; -- problematic query",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": "Potentially dangerous SQL pattern detected: --",
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 1,
            "disable_sql_blocking": False
        }

        result = refine_sql_node(state)

        # Since we're mocking the SQLGenerator, the result should be the mocked value
        assert result["sql_query"] == "SELECT id, name FROM users;"
        assert result["validation_error"] is None
        assert result["execution_error"] is None
        assert result["sql_generation_error"] is None
        print("✓ refine_sql_node test passed")


def test_generate_response_node():
    """
    Test the generate_response_node function
    """
    with patch('langgraph_agent.PromptGenerator') as mock_prompt_gen:
        with patch('langgraph_agent.ResponseGenerator') as mock_resp_gen:
            mock_prompt_instance = Mock()
            mock_prompt_instance.generate_prompt_for_response_llm.return_value = "Formatted prompt"
            mock_prompt_gen.return_value = mock_prompt_instance

            mock_resp_instance = Mock()
            mock_resp_instance.generate_natural_language_response.return_value = "Here are the users: John"
            mock_resp_gen.return_value = mock_resp_instance

            state = {
                "user_request": "Get all users",
                "schema_dump": {"users": [{"name": "id", "type": "int"}]},
                "sql_query": "SELECT * FROM users;",
                "db_results": [{"id": 1, "name": "John"}],
                "final_response": "",
                "messages": [],
                "validation_error": None,
                "execution_error": None,
                "sql_generation_error": None,
                "retry_count": 0,
                "disable_sql_blocking": False
            }

            result = generate_response_node(state)

            assert result["final_response"] == "Here are the users: John"
            print("✓ generate_response_node test passed")


def test_create_enhanced_agent_graph():
    """
    Test that the enhanced agent graph can be created without errors
    """
    graph = create_enhanced_agent_graph()
    assert graph is not None
    print("✓ create_enhanced_agent_graph test passed")


def test_run_enhanced_agent():
    """
    Test the run_enhanced_agent convenience function
    """
    # Mock all the dependencies to avoid actual database calls
    with patch('langgraph_agent.DatabaseManager') as mock_db_manager:
        with patch('langgraph_agent.SQLGenerator') as mock_sql_generator:
            with patch('langgraph_agent.SQLExecutor') as mock_sql_executor:
                with patch('langgraph_agent.PromptGenerator') as mock_prompt_gen:
                    with patch('langgraph_agent.ResponseGenerator') as mock_resp_gen:
                        # Setup mocks
                        mock_db_instance = Mock()
                        mock_db_instance.get_schema_dump.return_value = {"users": [{"name": "id", "type": "int", "nullable": False}]}
                        mock_db_manager.return_value = mock_db_instance

                        mock_sql_gen_instance = Mock()
                        mock_sql_gen_instance.generate_sql.return_value = "SELECT * FROM users;"
                        mock_sql_generator.return_value = mock_sql_gen_instance

                        mock_sql_exec_instance = Mock()
                        mock_sql_exec_instance.execute_sql_and_get_results.return_value = [{"id": 1, "name": "John"}]
                        mock_sql_executor.return_value = mock_sql_exec_instance

                        mock_prompt_instance = Mock()
                        mock_prompt_instance.generate_prompt_for_response_llm.return_value = "Formatted prompt"
                        mock_prompt_gen.return_value = mock_prompt_instance

                        mock_resp_instance = Mock()
                        mock_resp_instance.generate_natural_language_response.return_value = "Here are the users: John"
                        mock_resp_gen.return_value = mock_resp_instance

                        # Run the agent
                        result = run_enhanced_agent("Get all users")

                        # Verify the result
                        assert result["original_request"] == "Get all users"
                        assert result["generated_sql"] == "SELECT * FROM users;"
                        assert result["db_results"] == [{"id": 1, "name": "John"}]
                        assert result["final_response"] == "Here are the users: John"
                        assert "execution_log" in result
                        assert len(result["execution_log"]) >= 2  # At least start and end events
                        print("✓ run_enhanced_agent test passed")


def test_run_enhanced_agent_with_sql_blocking_disabled():
    """
    Test the run_enhanced_agent convenience function with SQL blocking disabled
    """
    # Mock all the dependencies to avoid actual database calls
    with patch('langgraph_agent.DatabaseManager') as mock_db_manager:
        with patch('langgraph_agent.SQLGenerator') as mock_sql_generator:
            with patch('langgraph_agent.SQLExecutor') as mock_sql_executor:
                with patch('langgraph_agent.PromptGenerator') as mock_prompt_gen:
                    with patch('langgraph_agent.ResponseGenerator') as mock_resp_gen:
                        # Setup mocks
                        mock_db_instance = Mock()
                        mock_db_instance.get_schema_dump.return_value = {"users": [{"name": "id", "type": "int", "nullable": False}]}
                        mock_db_manager.return_value = mock_db_instance

                        mock_sql_gen_instance = Mock()
                        # Return a potentially harmful query to test that blocking is disabled
                        mock_sql_gen_instance.generate_sql.return_value = "DROP TABLE users;"
                        mock_sql_generator.return_value = mock_sql_gen_instance

                        mock_sql_exec_instance = Mock()
                        mock_sql_exec_instance.execute_sql_and_get_results.return_value = []
                        mock_sql_executor.return_value = mock_sql_exec_instance

                        mock_prompt_instance = Mock()
                        mock_prompt_instance.generate_prompt_for_response_llm.return_value = "Formatted prompt"
                        mock_prompt_gen.return_value = mock_prompt_instance

                        mock_resp_instance = Mock()
                        mock_resp_instance.generate_natural_language_response.return_value = "Query executed"
                        mock_resp_gen.return_value = mock_resp_instance

                        # Run the agent with SQL blocking disabled
                        result = run_enhanced_agent("Drop users table", disable_sql_blocking=True)

                        # Verify the result - the harmful query should be allowed through
                        assert result["original_request"] == "Drop users table"
                        assert result["generated_sql"] == "DROP TABLE users;"
                        assert result["final_response"] == "Query executed"
                        assert "execution_log" in result
                        print("✓ run_enhanced_agent with SQL blocking disabled test passed")


def test_security_llm_false_positive_detection():
    """
    Test that the security LLM correctly identifies false positives like 'created_at' column
    """
    # Mock the security detector to return safe for queries with 'created_at'
    with patch('langgraph_agent.SecuritySQLDetector') as mock_security_detector_class:
        mock_detector_instance = Mock()
        mock_detector_instance.is_query_safe.return_value = (True, "Column name 'created_at' is not a security risk")
        mock_security_detector_class.return_value = mock_detector_instance

        # Temporarily enable the security LLM
        original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
        os.environ['USE_SECURITY_LLM'] = 'true'

        try:
            state = {
                "user_request": "Get all users created after 2023",
                "schema_dump": {"users": [{"name": "id", "type": "int"}, {"name": "created_at", "type": "datetime"}]},
                "sql_query": "SELECT * FROM users WHERE created_at > '2023-01-01';",
                "db_results": [],
                "final_response": "",
                "messages": [],
                "validation_error": None,
                "execution_error": None,
                "sql_generation_error": None,
                "retry_count": 0,
                "disable_sql_blocking": False
            }

            result = validate_sql_node(state)

            # With security LLM enabled, it should recognize 'created_at' as safe
            assert result["validation_error"] is None
            print("✓ security LLM correctly handles false positive test passed")
        finally:
            # Restore original value
            if original_use_security_llm is not None:
                os.environ['USE_SECURITY_LLM'] = original_use_security_llm
            else:
                if 'USE_SECURITY_LLM' in os.environ:
                    del os.environ['USE_SECURITY_LLM']


def test_security_llm_harmful_query_detection():
    """
    Test that the security LLM correctly identifies actually harmful queries
    """
    # Mock the security detector to return unsafe for harmful queries
    with patch('langgraph_agent.SecuritySQLDetector') as mock_security_detector_class:
        mock_detector_instance = Mock()
        mock_detector_instance.is_query_safe.return_value = (False, "DROP command detected as security risk")
        mock_security_detector_class.return_value = mock_detector_instance

        # Temporarily enable the security LLM
        original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
        os.environ['USE_SECURITY_LLM'] = 'true'

        try:
            state = {
                "user_request": "Delete all users",
                "schema_dump": {"users": [{"name": "id", "type": "int"}, {"name": "created_at", "type": "datetime"}]},
                "sql_query": "DROP TABLE users;",
                "db_results": [],
                "final_response": "",
                "messages": [],
                "validation_error": None,
                "execution_error": None,
                "sql_generation_error": None,
                "retry_count": 0,
                "disable_sql_blocking": False
            }

            result = validate_sql_node(state)

            # With security LLM enabled, it should catch the harmful query
            assert result["validation_error"] is not None
            assert "Security LLM detected potential security issue" in result["validation_error"]
            print("✓ security LLM correctly detects harmful query test passed")
        finally:
            # Restore original value
            if original_use_security_llm is not None:
                os.environ['USE_SECURITY_LLM'] = original_use_security_llm
            else:
                if 'USE_SECURITY_LLM' in os.environ:
                    del os.environ['USE_SECURITY_LLM']


def test_error_handling_in_run_enhanced_agent():
    """
    Test error handling in the run_enhanced_agent function
    """
    # Mock to simulate an error in SQL generation
    with patch('langgraph_agent.DatabaseManager') as mock_db_manager:
        with patch('langgraph_agent.SQLGenerator') as mock_sql_generator:
            # Setup mocks
            mock_db_instance = Mock()
            mock_db_instance.get_schema_dump.return_value = {"users": [{"name": "id", "type": "int", "nullable": False}]}
            mock_db_manager.return_value = mock_db_instance

            mock_sql_gen_instance = Mock()
            mock_sql_gen_instance.generate_sql.side_effect = Exception("SQL generation failed")
            mock_sql_generator.return_value = mock_sql_gen_instance

            # Run the agent with SQL blocking enabled to prevent infinite loops in tests
            result = run_enhanced_agent("Get all users", disable_sql_blocking=False)

            # Verify the result includes error information
            assert result["original_request"] == "Get all users"
            assert result["generated_sql"] == ""
            assert result["sql_generation_error"] is not None
            assert "SQL generation failed" in result["sql_generation_error"]
            assert "execution_log" in result
            print("✓ error handling test passed")


def test_validate_sql_node_hex_escape_detection():
    """
    Test the validate_sql_node function detects hexadecimal escape sequences
    """
    # Temporarily disable the security LLM for this test to use basic validation
    original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        state = {
            "user_request": "Get users with hex escape",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "SELECT * FROM users WHERE name = '\\x41';",  # Hex escape for 'A'
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = validate_sql_node(state)

        assert result["validation_error"] is not None
        assert "Hexadecimal escape sequences detected" in result["validation_error"]
        assert result["retry_count"] == 1
        print("✓ validate_sql_node hex escape detection test passed")
    finally:
        # Restore original value
        if original_use_security_llm is not None:
            os.environ['USE_SECURITY_LLM'] = original_use_security_llm
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']


def test_validate_sql_node_binary_literal_detection():
    """
    Test the validate_sql_node function detects binary literals
    """
    # Temporarily disable the security LLM for this test to use basic validation
    original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        state = {
            "user_request": "Get users with binary literal",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "SELECT * FROM users WHERE flags = b'1010';",  # Binary literal
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = validate_sql_node(state)

        assert result["validation_error"] is not None
        assert "Binary literals detected" in result["validation_error"]
        assert result["retry_count"] == 1
        print("✓ validate_sql_node binary literal detection test passed")
    finally:
        # Restore original value
        if original_use_security_llm is not None:
            os.environ['USE_SECURITY_LLM'] = original_use_security_llm
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']


def test_validate_sql_node_with_clause_allowed():
    """
    Test the validate_sql_node function allows WITH clauses
    """
    # Temporarily disable the security LLM for this test to use basic validation
    original_use_security_llm = os.environ.get('USE_SECURITY_LLM')
    os.environ['USE_SECURITY_LLM'] = 'false'

    try:
        state = {
            "user_request": "Get users with CTE",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]},
            "sql_query": "WITH recent_users AS (SELECT * FROM users WHERE created_at > '2023-01-01') SELECT * FROM recent_users;",
            "db_results": [],
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False
        }

        result = validate_sql_node(state)

        assert result["validation_error"] is None
        print("✓ validate_sql_node WITH clause allowed test passed")
    finally:
        # Restore original value
        if original_use_security_llm is not None:
            os.environ['USE_SECURITY_LLM'] = original_use_security_llm
        else:
            if 'USE_SECURITY_LLM' in os.environ:
                del os.environ['USE_SECURITY_LLM']


def run_all_tests():
    """
    Run all tests
    """
    print("Running tests for enhanced LangGraph agent...")

    test_agent_state_structure()
    test_get_schema_node()
    test_generate_sql_node()
    test_validate_sql_node_safe()
    test_validate_sql_node_unsafe()
    test_validate_sql_node_non_select()
    test_validate_sql_node_starts_with_select()
    test_validate_sql_node_with_blocking_disabled()
    test_execute_sql_node()
    test_refine_sql_node()
    test_generate_response_node()
    test_create_enhanced_agent_graph()
    test_run_enhanced_agent()
    test_run_enhanced_agent_with_sql_blocking_disabled()
    test_security_llm_false_positive_detection()
    test_security_llm_harmful_query_detection()
    test_error_handling_in_run_enhanced_agent()
    test_validate_sql_node_hex_escape_detection()
    test_validate_sql_node_binary_literal_detection()
    test_validate_sql_node_with_clause_allowed()

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    run_all_tests()
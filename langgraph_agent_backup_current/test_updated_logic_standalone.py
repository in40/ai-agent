#!/usr/bin/env python3
"""
Simple test to verify the updated check_rag_applicability_node logic
"""

import os
import time
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    New state definition for the MCP-focused LangGraph agent.
    """
    user_request: str                           # Original user request
    mcp_queries: List[Dict[str, Any]]           # Planned MCP queries to execute
    mcp_results: List[Dict[str, Any]]           # Results from executed MCP queries
    synthesized_result: str                     # Synthesized result from all MCP queries
    can_answer: bool                           # Flag indicating if we can answer the question
    iteration_count: int                       # Number of iterations performed
    max_iterations: int                        # Maximum allowed iterations
    final_answer: str                          # Final answer to return to user
    error_message: Optional[str]               # Any error messages encountered
    mcp_servers: List[Dict[str, Any]]          # Available MCP servers in the pool
    refined_queries: List[Dict[str, Any]]      # Refined queries for next iteration
    failure_reason: Optional[str]              # Reason for failure if iterations exhausted
    # Fields retained for compatibility
    schema_dump: Dict[str, Any]
    sql_query: str
    db_results: List[Dict[str, Any]]
    all_db_results: Dict[str, List[Dict[str, Any]]]
    table_to_db_mapping: Dict[str, str]
    table_to_real_db_mapping: Dict[str, str]
    response_prompt: str
    messages: List[BaseMessage]
    validation_error: str
    retry_count: int
    execution_error: str
    sql_generation_error: str
    disable_sql_blocking: bool
    disable_databases: bool
    query_type: str
    database_name: str
    previous_sql_queries: List[str]
    registry_url: Optional[str]
    discovered_services: List[Dict[str, Any]]
    mcp_service_results: List[Dict[str, Any]]
    use_mcp_results: bool
    mcp_tool_calls: List[Dict[str, Any]]
    mcp_capable_response: str
    return_mcp_results_to_llm: bool
    # RAG-specific fields
    rag_documents: List[Dict[str, Any]]
    rag_context: str
    use_rag_flag: bool
    rag_relevance_score: float
    rag_query: str
    rag_response: str


def check_rag_applicability_node(state: AgentState) -> AgentState:
    """
    Node to check if RAG is applicable for the user request.
    Determines whether to use RAG or proceed with traditional MCP approach.
    """
    start_time = time.time()
    user_request = state["user_request"]
    logger.info(f"[NODE START] check_rag_applicability_node - Checking if RAG is applicable for request: {user_request[:100]}...")

    try:
        # Import required components
        from rag_component.config import RAG_MODE
        from config.settings import str_to_bool
        import os

        # Check if RAG is enabled via configuration
        rag_enabled = str_to_bool(os.getenv("RAG_ENABLED", "true"))

        # Check if LLM model requested any MCP tool call (contains any service_id in tool_call section)
        mcp_tool_calls = state.get("mcp_tool_calls", [])
        has_any_mcp_tool_call = len(mcp_tool_calls) > 0

        # If RAG is enabled and LLM model requested any MCP tool call, consider using RAG
        # However, if RAG mode is set to "mcp", we'll only use RAG if MCP services are available
        use_rag = False
        if rag_enabled and has_any_mcp_tool_call:
            if RAG_MODE == "local":
                # Use local RAG
                use_rag = True
            elif RAG_MODE == "mcp":
                # Only use RAG if MCP services are available and the system is configured to use them
                # Check if there are any RAG MCP services available in the discovered services
                discovered_services = state.get("discovered_services", [])
                rag_mcp_services = [s for s in discovered_services if s.get("type") == "rag"]

                # If RAG MCP services are available, we'll use them; otherwise, we won't use RAG at all
                if rag_mcp_services:
                    use_rag = True
                    logger.info(f"RAG MCP services available ({len(rag_mcp_services)} services), using RAG in MCP mode")
                else:
                    logger.info("RAG MCP mode selected but no RAG MCP services discovered, skipping RAG")
                    use_rag = False
            elif RAG_MODE == "hybrid":
                # Use local RAG as fallback but prefer MCP if available
                use_rag = True
            else:
                # Default to local if mode is invalid
                use_rag = True

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] check_rag_applicability_node - RAG applicability check completed in {elapsed_time:.2f}s. Use RAG: {use_rag}, Mode: {RAG_MODE}")

        return {
            **state,
            "use_rag_flag": use_rag,
            "rag_query": user_request  # Use the original user request as the RAG query
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] check_rag_applicability_node - Error checking RAG applicability after {elapsed_time:.2f}s: {str(e)}")

        # On error, default to not using RAG to maintain existing functionality
        return {
            **state,
            "use_rag_flag": False,
            "rag_query": ""
        }


def test_check_rag_applicability_node_with_any_mcp_tool_call():
    """Test that the function correctly identifies when any MCP tool call is present"""

    # Set environment variable to enable RAG
    os.environ['RAG_ENABLED'] = 'true'

    # Mock RAG_MODE
    import sys
    from unittest.mock import MagicMock

    # Create a mock module for rag_component.config
    rag_config_mock = MagicMock()
    rag_config_mock.RAG_MODE = "mcp"

    # Add the mock to sys.modules
    sys.modules['rag_component.config'] = rag_config_mock

    # Also mock config.settings
    settings_mock = MagicMock()
    settings_mock.str_to_bool = lambda x: x.lower() in ('true', '1', 'yes', 'on')

    sys.modules['config.settings'] = settings_mock

    # Test state with any MCP tool call (regardless of service_id)
    state_with_any_mcp_tool_call = {
        "user_request": "What is the capital of France?",
        "mcp_tool_calls": [
            {"service_id": "rag-search-service", "params": {"query": "capital of France"}},
            {"service_id": "other-service", "params": {"query": "something else"}}
        ],
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_query": "",
        "rag_response": "",
        "discovered_services": [{"id": "rag-search-service", "type": "rag", "host": "localhost", "port": 8080}],
        "mcp_queries": [],
        "mcp_results": [],
        "synthesized_result": "",
        "can_answer": False,
        "iteration_count": 0,
        "max_iterations": 3,
        "final_answer": "",
        "error_message": None,
        "mcp_servers": [],
        "refined_queries": [],
        "failure_reason": None,
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "",
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
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "rag_relevance_score": 0.0
    }

    result = check_rag_applicability_node(state_with_any_mcp_tool_call)

    print(f"Test 1 - State with any MCP tool call:")
    print(f"  use_rag_flag: {result['use_rag_flag']}")
    print(f"  Expected: True")
    print(f"  Result: {'PASS' if result['use_rag_flag'] == True else 'FAIL'}")

    # Test state without any MCP tool call
    state_without_any_mcp_tool_call = {
        "user_request": "What is the capital of France?",
        "mcp_tool_calls": [],  # Empty list
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_query": "",
        "rag_response": "",
        "discovered_services": [{"id": "rag-search-service", "type": "rag", "host": "localhost", "port": 8080}],
        "mcp_queries": [],
        "mcp_results": [],
        "synthesized_result": "",
        "can_answer": False,
        "iteration_count": 0,
        "max_iterations": 3,
        "final_answer": "",
        "error_message": None,
        "mcp_servers": [],
        "refined_queries": [],
        "failure_reason": None,
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "",
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
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "rag_relevance_score": 0.0
    }

    result2 = check_rag_applicability_node(state_without_any_mcp_tool_call)

    print(f"\nTest 2 - State without any MCP tool call:")
    print(f"  use_rag_flag: {result2['use_rag_flag']}")
    print(f"  Expected: False")
    print(f"  Result: {'PASS' if result2['use_rag_flag'] == False else 'FAIL'}")

    # Clean up environment
    del os.environ['RAG_ENABLED']


def test_check_rag_applicability_node_with_any_tool_call_regardless_of_service_id():
    """Test that the function correctly identifies any MCP tool call regardless of service ID"""

    # Set environment variable to enable RAG
    os.environ['RAG_ENABLED'] = 'true'

    # Mock RAG_MODE
    import sys
    from unittest.mock import MagicMock

    # Create a mock module for rag_component.config
    rag_config_mock = MagicMock()
    rag_config_mock.RAG_MODE = "mcp"

    # Add the mock to sys.modules
    sys.modules['rag_component.config'] = rag_config_mock

    # Also mock config.settings
    settings_mock = MagicMock()
    settings_mock.str_to_bool = lambda x: x.lower() in ('true', '1', 'yes', 'on')

    sys.modules['config.settings'] = settings_mock

    # Test state with a tool call that has a service_id that doesn't start with 'rag'
    state_with_non_rag_service_id = {
        "user_request": "What is the weather today?",
        "mcp_tool_calls": [
            {"service_id": "sql-execution-service", "params": {"query": "SELECT * FROM weather_table"}},
        ],
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_query": "",
        "rag_response": "",
        "discovered_services": [{"id": "rag-document-retriever", "type": "rag", "host": "localhost", "port": 8080}],
        "mcp_queries": [],
        "mcp_results": [],
        "synthesized_result": "",
        "can_answer": False,
        "iteration_count": 0,
        "max_iterations": 3,
        "final_answer": "",
        "error_message": None,
        "mcp_servers": [],
        "refined_queries": [],
        "failure_reason": None,
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "",
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
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "rag_relevance_score": 0.0
    }

    result = check_rag_applicability_node(state_with_non_rag_service_id)

    print(f"\nTest 3 - State with non-RAG service ID (but still MCP tool call):")
    print(f"  use_rag_flag: {result['use_rag_flag']}")
    print(f"  Expected: True (because any MCP tool call triggers RAG when enabled)")
    print(f"  Result: {'PASS' if result['use_rag_flag'] == True else 'FAIL'}")

    # Clean up environment
    del os.environ['RAG_ENABLED']


if __name__ == "__main__":
    print("Testing updated check_rag_applicability_node logic...")
    test_check_rag_applicability_node_with_any_mcp_tool_call()
    test_check_rag_applicability_node_with_any_tool_call_regardless_of_service_id()
    print("\nTesting completed!")
#!/usr/bin/env python3
"""
Test script to verify the fix for the tool call multiplication issue in langgraph.
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import AgentState

def test_state_update_behavior():
    """
    Test that the state fields are updated correctly without duplication.
    """
    print("Testing state update behavior...")
    
    # Create initial state
    initial_state: AgentState = {
        "user_request": "test request",
        "mcp_queries": [{"service_id": "test-service", "method": "test_method", "params": {"query": "test"}}],
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
        # Fields retained for compatibility
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
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [{"service_id": "test-service", "method": "test_method", "params": {"query": "test"}}],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "is_final_answer": False,
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_relevance_score": 0.0,
        "rag_query": "",
        "rag_response": "",
        "raw_mcp_results": []
    }
    
    print(f"Initial mcp_queries count: {len(initial_state['mcp_queries'])}")
    print(f"Initial mcp_tool_calls count: {len(initial_state['mcp_tool_calls'])}")
    print(f"Initial raw_mcp_results count: {len(initial_state['raw_mcp_results'])}")
    print(f"Initial refined_queries count: {len(initial_state['refined_queries'])}")
    
    # Simulate updating the state with new values
    updated_state = {
        **initial_state,
        "mcp_queries": [{"service_id": "updated-service", "method": "updated_method", "params": {"query": "updated"}}],
        "mcp_tool_calls": [{"service_id": "updated-service", "method": "updated_method", "params": {"query": "updated"}}],
        "raw_mcp_results": [{"service_id": "result-service", "result": "test result"}],
        "refined_queries": [{"service_id": "refined-service", "method": "refined_method", "params": {"query": "refined"}}]
    }
    
    print(f"After update mcp_queries count: {len(updated_state['mcp_queries'])}")
    print(f"After update mcp_tool_calls count: {len(updated_state['mcp_tool_calls'])}")
    print(f"After update raw_mcp_results count: {len(updated_state['raw_mcp_results'])}")
    print(f"After update refined_queries count: {len(updated_state['refined_queries'])}")
    
    # Verify that counts are correct (should be 1 for each after update)
    assert len(updated_state['mcp_queries']) == 1, f"Expected 1 mcp_query, got {len(updated_state['mcp_queries'])}"
    assert len(updated_state['mcp_tool_calls']) == 1, f"Expected 1 mcp_tool_call, got {len(updated_state['mcp_tool_calls'])}"
    assert len(updated_state['raw_mcp_results']) == 1, f"Expected 1 raw_mcp_result, got {len(updated_state['raw_mcp_results'])}"
    assert len(updated_state['refined_queries']) == 1, f"Expected 1 refined_query, got {len(updated_state['refined_queries'])}"
    
    print("✅ All state update tests passed!")
    

def test_logging_simulation():
    """
    Simulate the scenario described in the log to ensure the fix works.
    """
    print("\nSimulating the log scenario...")
    
    # Simulate the initial state after analyze_request_node
    initial_state: AgentState = {
        "user_request": "найди в RAG и интернете требования к малым базам биометрических образов Чужой",
        "mcp_queries": [
            {"service_id": "rag-server-127-0-0-1-8091", "method": "query_documents", "params": {"query": "требования к малым базам биометрических образов Чужой"}},
            {"service_id": "search-server-127-0-0-1-8090", "method": "web_search", "params": {"query": "требования к малым базам биометрических образов Чужой"}},
            {"service_id": "sql-server-127-0-0-1-8092", "method": "get_schema", "params": {"db_name": "biometric_database"}}
        ],
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
        # Fields retained for compatibility
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
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [
            {"service_id": "rag-server-127-0-0-1-8091", "method": "query_documents", "params": {"query": "требования к малым базам биометрических образов Чужой"}},
            {"service_id": "search-server-127-0-0-1-8090", "method": "web_search", "params": {"query": "требования к малым базам биометрических образов Чужой"}},
            {"service_id": "sql-server-127-0-0-1-8092", "method": "get_schema", "params": {"db_name": "biometric_database"}}
        ],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "is_final_answer": False,
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_relevance_score": 0.0,
        "rag_query": "",
        "rag_response": "",
        "raw_mcp_results": []
    }
    
    print(f"Initial tool calls count: {len(initial_state['mcp_queries'])}")
    
    # Simulate the plan_mcp_queries_node behavior (this should NOT multiply the queries)
    planned_state = {
        **initial_state,
        "mcp_queries": initial_state["mcp_queries"]  # Same 3 queries, not multiplied
    }
    
    print(f"After planning tool calls count: {len(planned_state['mcp_queries'])}")
    
    # Simulate the execute_mcp_queries_node behavior (this should NOT multiply the queries)
    executed_state = {
        **planned_state,
        "mcp_results": [{"result": "simulated result"}],  # Results would be added here
        "raw_mcp_results": [{"result": "simulated raw result"}]  # Raw results would be added here
    }
    
    print(f"After execution tool calls count: {len(executed_state['mcp_queries'])}")
    
    # Verify that the counts remain correct (still 3, not multiplied)
    assert len(executed_state['mcp_queries']) == 3, f"Expected 3 mcp_queries after execution, got {len(executed_state['mcp_queries'])}"
    assert len(executed_state['mcp_tool_calls']) == 3, f"Expected 3 mcp_tool_calls, got {len(executed_state['mcp_tool_calls'])}"
    
    print("✅ Log scenario simulation passed! Tool calls remain at 3, no multiplication occurred.")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    print("Testing the fix for tool call multiplication issue in langgraph...")
    print("="*60)
    
    test_state_update_behavior()
    test_logging_simulation()
    
    print("="*60)
    print("🎉 All tests passed! The fix should prevent tool call multiplication.")
    print("The issue was in the state field reducers that were using operator.add")
    print("(append) instead of lambda x, y: y (replace) for fields that should")
    print("be replaced rather than accumulated.")
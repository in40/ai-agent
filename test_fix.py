#!/usr/bin/env python3
"""
Test script to verify the fix for returning combined results when response generation is disabled
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import AgentState

def test_generate_final_answer_with_disabled_response():
    """Test that generate_final_answer_node properly returns combined results when response generation is disabled"""
    
    # Mock environment variable to disable response generation
    os.environ["DISABLE_RESPONSE_GENERATION"] = "true"
    
    # Create a test state with mcp_results containing data
    test_state: AgentState = {
        "user_request": "Test request",
        "mcp_results": [
            {
                "source": "RAG Service",
                "content": "This is a test result from RAG service with important information about biometric templates.",
                "title": "Biometric Standards Document"
            },
            {
                "source": "Search Service", 
                "content": "This is a test result from Search service with additional relevant information.",
                "title": "Search Result"
            }
        ],
        "rag_results": [],
        "other_results": [],
        "rag_documents": [],
        "final_answer": "",
        "rag_response": "",
        "synthesized_result": "",
        "error_message": "Some service failed",
        "can_answer": True,
        "iteration_count": 0,
        "max_iterations": 3,
        "failure_reason": None,
        
        # Additional fields required by the state
        "mcp_queries": [],
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
        "mcp_tool_calls": [],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "is_final_answer": False,
        "rag_context": "",
        "use_rag_flag": False,
        "rag_relevance_score": 0.0,
        "rag_query": "",
        "raw_mcp_results": []
    }
    
    # Import and run the function
    from langgraph_agent.langgraph_agent import generate_final_answer_node
    
    result = generate_final_answer_node(test_state)
    
    print("Test Results:")
    print(f"Final Answer Length: {len(result['final_answer'])}")
    print(f"Final Answer Preview: {result['final_answer'][:500]}...")
    
    # Check if the result contains the content from mcp_results
    final_answer = result['final_answer']
    contains_rag_content = "biometric templates" in final_answer.lower()
    contains_search_content = "additional relevant information" in final_answer.lower()
    
    print(f"\nContains RAG content: {contains_rag_content}")
    print(f"Contains Search content: {contains_search_content}")
    
    if contains_rag_content and contains_search_content:
        print("\n✅ SUCCESS: The fix is working! Combined results are included in the final answer.")
        return True
    else:
        print("\n❌ FAILURE: The fix is not working properly.")
        return False

def test_synthesize_results_with_disabled_response():
    """Test that synthesize_results_node properly handles results when response generation is disabled"""

    # Mock environment variable to disable response generation
    os.environ["DISABLE_RESPONSE_GENERATION"] = "true"

    # Create a test state with mcp_results and an error message
    test_state: AgentState = {
        "user_request": "Test request",
        "mcp_results": [
            {
                "source": "RAG Service",
                "content": "This is a test result from RAG service with important information about biometric templates.",
                "title": "Biometric Standards Document"
            }
        ],
        "mcp_results": [{"source": "Search", "content": "Search result", "title": "Search Title"}],
        "rag_results": [{"source": "RAG", "content": "RAG result", "title": "RAG Title"}],
        "other_results": [],
        "rag_documents": [],
        "final_answer": "",
        "rag_response": "",
        "synthesized_result": "",
        "error_message": "SQL service failed",
        "can_answer": True,
        "iteration_count": 0,
        "max_iterations": 3,
        "failure_reason": None,

        # Additional fields required by the state
        "mcp_queries": [],
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
        "mcp_tool_calls": [],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "is_final_answer": False,
        "rag_context": "",
        "use_rag_flag": False,
        "rag_relevance_score": 0.0,
        "rag_query": "",
        "raw_mcp_results": []
    }

    # Import and run the function
    from langgraph_agent.langgraph_agent import synthesize_results_node

    result = synthesize_results_node(test_state)

    print("\n" + "="*50)
    print("Synthesize Results Test:")
    print(f"Synthesized Result Length: {len(result['synthesized_result'])}")
    print(f"Synthesized Result Preview: {result['synthesized_result'][:500]}...")

    # Check if the result contains the content from mcp_results
    synthesized_result = result['synthesized_result']
    contains_rag_content = "biometric templates" in synthesized_result.lower()

    print(f"\nContains RAG content: {contains_rag_content}")

    # The synthesize_results_node should return the formatted mcp_results when response generation is disabled
    # regardless of error_message, since it takes the first branch of the if statement
    if contains_rag_content:
        print("\n✅ SUCCESS: The synthesize_results_node is working correctly!")
        return True
    else:
        print("\n❌ FAILURE: The synthesize_results_node is not working properly.")
        return False

if __name__ == "__main__":
    print("Testing the fix for returning combined results when response generation is disabled...\n")
    
    test1_passed = test_generate_final_answer_with_disabled_response()
    test2_passed = test_synthesize_results_with_disabled_response()
    
    print("\n" + "="*60)
    print("OVERALL TEST RESULT:")
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED: The fix is working correctly!")
    else:
        print("❌ SOME TESTS FAILED: The fix needs more work.")
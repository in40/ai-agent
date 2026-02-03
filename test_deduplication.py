#!/usr/bin/env python3
"""
Test script to verify the deduplication functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import generate_result_id, add_unique_results_to_state, AgentState

def test_generate_result_id():
    """Test the result ID generation function"""
    print("Testing generate_result_id function...")
    
    # Test with identical results
    result1 = {
        "content": "This is a test content",
        "source": "test_source",
        "title": "Test Title",
        "url": "http://example.com"
    }
    
    result2 = {
        "content": "This is a test content",
        "source": "test_source",
        "title": "Test Title",
        "url": "http://example.com"
    }
    
    id1 = generate_result_id(result1)
    id2 = generate_result_id(result2)
    
    assert id1 == id2, f"Identical results should have the same ID: {id1} != {id2}"
    print(f"✓ Identical results have the same ID: {id1}")
    
    # Test with different content
    result3 = {
        "content": "Different content",
        "source": "test_source",
        "title": "Test Title",
        "url": "http://example.com"
    }
    
    id3 = generate_result_id(result3)
    
    assert id1 != id3, f"Different results should have different IDs: {id1} == {id3}"
    print(f"✓ Different results have different IDs: {id1} != {id3}")
    
    print("generate_result_id function tests passed!\n")


def test_add_unique_results_to_state():
    """Test the unique results addition function"""
    print("Testing add_unique_results_to_state function...")
    
    # Initialize state
    initial_state: AgentState = {
        "user_request": "test request",
        "mcp_queries": [],
        "mcp_results": [],
        "rag_results": [],
        "other_results": [],
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
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "is_final_answer": False,
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_relevance_score": 0.0,
        "rag_query": "",
        "rag_response": "",
        "raw_mcp_results": [],
        "result_ids_registry": set()
    }
    
    # Create some test results
    result1 = {
        "content": "This is the first test content",
        "source": "test_source_1",
        "title": "Test Title 1",
        "url": "http://example.com/1"
    }
    
    result2 = {
        "content": "This is the second test content",
        "source": "test_source_2",
        "title": "Test Title 2",
        "url": "http://example.com/2"
    }
    
    # Add the first result
    updated_state = add_unique_results_to_state(initial_state, [result1], "mcp_results")
    
    # Verify the result was added
    assert len(updated_state["mcp_results"]) == 1, f"Expected 1 result, got {len(updated_state['mcp_results'])}"
    assert len(updated_state["result_ids_registry"]) == 1, f"Expected 1 ID in registry, got {len(updated_state['result_ids_registry'])}"
    print("✓ First result was added successfully")
    
    # Try to add the same result again
    updated_state2 = add_unique_results_to_state(updated_state, [result1], "mcp_results")
    
    # Verify the duplicate was not added
    assert len(updated_state2["mcp_results"]) == 1, f"Expected 1 result after duplicate attempt, got {len(updated_state2['mcp_results'])}"
    assert len(updated_state2["result_ids_registry"]) == 1, f"Expected 1 ID in registry after duplicate attempt, got {len(updated_state2['result_ids_registry'])}"
    print("✓ Duplicate result was correctly rejected")
    
    # Add a different result
    updated_state3 = add_unique_results_to_state(updated_state2, [result2], "mcp_results")
    
    # Verify the new result was added
    assert len(updated_state3["mcp_results"]) == 2, f"Expected 2 results after adding new result, got {len(updated_state3['mcp_results'])}"
    assert len(updated_state3["result_ids_registry"]) == 2, f"Expected 2 IDs in registry, got {len(updated_state3['result_ids_registry'])}"
    print("✓ New result was added successfully")
    
    print("add_unique_results_to_state function tests passed!\n")


def main():
    """Main test function"""
    print("Running deduplication tests...\n")
    
    test_generate_result_id()
    test_add_unique_results_to_state()
    
    print("All tests passed! ✓")


if __name__ == "__main__":
    main()
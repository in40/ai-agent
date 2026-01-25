#!/usr/bin/env python3
"""
Simple test to verify the updated check_rag_applicability_node logic
"""

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import check_rag_applicability_node


def test_check_rag_applicability_node_with_rag_tool_call():
    """Test that the function correctly identifies when RAG MCP tool call is present"""
    
    # Set environment variable to enable RAG
    os.environ['RAG_ENABLED'] = 'true'
    
    # Test state with a RAG tool call
    state_with_rag_tool_call = {
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
        "discovered_services": [{"id": "rag-search-service", "type": "rag", "host": "localhost", "port": 8080}]
    }
    
    result = check_rag_applicability_node(state_with_rag_tool_call)
    
    print(f"Test 1 - State with RAG tool call:")
    print(f"  use_rag_flag: {result['use_rag_flag']}")
    print(f"  Expected: True")
    print(f"  Result: {'PASS' if result['use_rag_flag'] == True else 'FAIL'}")
    
    # Test state without RAG tool call
    state_without_rag_tool_call = {
        "user_request": "What is the capital of France?",
        "mcp_tool_calls": [
            {"service_id": "sql-execution-service", "params": {"query": "SELECT * FROM cities"}},
            {"service_id": "other-service", "params": {"query": "something else"}}
        ],
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_query": "",
        "rag_response": "",
        "discovered_services": [{"id": "rag-search-service", "type": "rag", "host": "localhost", "port": 8080}]
    }
    
    result2 = check_rag_applicability_node(state_without_rag_tool_call)
    
    print(f"\nTest 2 - State without RAG tool call:")
    print(f"  use_rag_flag: {result2['use_rag_flag']}")
    print(f"  Expected: False")
    print(f"  Result: {'PASS' if result2['use_rag_flag'] == False else 'FAIL'}")
    
    # Clean up environment
    del os.environ['RAG_ENABLED']


def test_check_rag_applicability_node_with_different_service_ids():
    """Test that the function correctly identifies different RAG service ID patterns"""
    
    # Set environment variable to enable RAG
    os.environ['RAG_ENABLED'] = 'true'
    
    # Test state with a RAG tool call that has a service_id starting with 'rag'
    state_with_rag_prefix = {
        "user_request": "What is the weather today?",
        "mcp_tool_calls": [
            {"service_id": "rag-document-retriever", "params": {"query": "weather information"}},
        ],
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_query": "",
        "rag_response": "",
        "discovered_services": [{"id": "rag-document-retriever", "type": "rag", "host": "localhost", "port": 8080}]
    }
    
    result = check_rag_applicability_node(state_with_rag_prefix)
    
    print(f"\nTest 3 - State with RAG service ID starting with 'rag':")
    print(f"  use_rag_flag: {result['use_rag_flag']}")
    print(f"  Expected: True")
    print(f"  Result: {'PASS' if result['use_rag_flag'] == True else 'FAIL'}")
    
    # Clean up environment
    del os.environ['RAG_ENABLED']


if __name__ == "__main__":
    print("Testing updated check_rag_applicability_node logic...")
    test_check_rag_applicability_node_with_rag_tool_call()
    test_check_rag_applicability_node_with_different_service_ids()
    print("\nTesting completed!")
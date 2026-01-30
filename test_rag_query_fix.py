#!/usr/bin/env python3
"""
Test script to verify that the RAG query extraction fix works correctly.
This script simulates the scenario described in the issue.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import retrieve_documents_node


def test_rag_query_extraction():
    """
    Test that the retrieve_documents_node correctly extracts the query from tool calls.
    """
    print("Testing RAG query extraction fix...")
    
    # Simulate the state that would come from analyze_request_node
    # with a RAG tool call containing the query
    test_state = {
        "user_request": "посмотри в локальных документах, что мы знаем про правила малых баз?",
        "mcp_tool_calls": [
            {
                'service_id': 'rag-server-127-0-0-1-8091',
                'method': 'query_documents',
                'params': {'query': 'правила малых баз'}
            }
        ],
        "discovered_services": [
            {
                "id": "rag-server-127-0-0-1-8091",
                "host": "localhost",
                "port": 8091,
                "type": "rag",
                "metadata": {"protocol": "http"}
            }
        ],
        "rag_query": "",  # Initially empty, should be extracted from tool call
        "rag_documents": [],
        "rag_relevance_score": 0.0
    }
    
    print(f"Initial state rag_query: '{test_state['rag_query']}'")
    print(f"MCP tool calls: {test_state['mcp_tool_calls']}")
    
    try:
        # Call the retrieve_documents_node function
        updated_state = retrieve_documents_node(test_state)
        
        print(f"After processing, rag_query: '{updated_state['rag_query']}'")
        print(f"RAG documents retrieved: {len(updated_state['rag_documents'])}")
        
        # Check if the query was correctly extracted
        if updated_state['rag_query'] == 'правила малых баз':
            print("✅ SUCCESS: Query was correctly extracted from tool call!")
            return True
        else:
            print(f"❌ FAILURE: Expected 'правила малых баз', but got '{updated_state['rag_query']}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rag_query_extraction()
    if success:
        print("\n🎉 Test passed! The RAG query extraction fix is working correctly.")
    else:
        print("\n💥 Test failed! The fix needs more work.")
        sys.exit(1)
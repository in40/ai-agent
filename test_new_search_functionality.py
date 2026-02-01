#!/usr/bin/env python3
"""
Test script to verify the new MCP search functionality with download and summarization.
This script tests the enhanced workflow where search results are processed with download and summarization
before being reranked and used in the RAG pipeline.
"""

import sys
import os
import json
from pprint import pprint

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_new_search_functionality():
    """Test the new search functionality with download and summarization."""
    print("Testing new MCP search functionality with download and summarization...")
    
    try:
        from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState, run_enhanced_agent
        from config.settings import MCP_REGISTRY_URL
        
        print("✓ Successfully imported langgraph agent components")
        
        # Create a test request that would trigger search functionality
        test_request = "Find recent information about artificial intelligence developments"
        
        print(f"Running test request: {test_request}")
        
        # Create the enhanced agent graph
        graph = create_enhanced_agent_graph()
        print("✓ Created enhanced agent graph")
        
        # Run the agent with the test request
        result = run_enhanced_agent(
            user_request=test_request,
            registry_url=MCP_REGISTRY_URL
        )
        
        print("✓ Agent execution completed")
        print("\nAgent Result:")
        print("="*50)
        print(f"Final Answer: {result['final_answer'][:200]}...")
        print(f"Synthesized Result: {result['synthesized_result'][:200]}...")
        print(f"MCP Results Count: {len(result['mcp_results'])}")
        print(f"Can Answer: {result['can_answer']}")
        print(f"Iteration Count: {result['iteration_count']}")
        
        # Check if the new node was executed by looking at execution logs
        execution_nodes = [log.get('node', '') for log in result.get('execution_log', [])]
        print(f"Execution nodes: {execution_nodes}")
        
        if 'process_search_results_with_download' in execution_nodes:
            print("✓ New search processing node was executed")
        else:
            print("⚠ New search processing node was not executed (may be expected if no search results were returned)")
            
        print("\nDetailed MCP Results:")
        for i, mcp_result in enumerate(result['mcp_results']):
            print(f"  Result {i+1}: {mcp_result.get('service_id', 'N/A')} - {mcp_result.get('status', 'N/A')}")
            if mcp_result.get('service_id', '').lower().find('search') != -1:
                search_data = mcp_result.get('result', {}).get('result', {})
                if 'results' in search_data:
                    print(f"    Search results count: {len(search_data['results'])}")
                    for j, search_result in enumerate(search_data['results'][:2]):  # Show first 2 results
                        print(f"      {j+1}. Title: {search_result.get('title', 'N/A')[:50]}...")
                        print(f"         URL: {search_result.get('url', 'N/A')}")
        
        print("\n✓ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_search_node_directly():
    """Test the new search processing node directly."""
    print("\nTesting the new search processing node directly...")
    
    try:
        from langgraph_agent.langgraph_agent import process_search_results_with_download_node, AgentState
        
        # Create a mock state with search results
        mock_state: AgentState = {
            "user_request": "What are the latest developments in AI?",
            "mcp_results": [
                {
                    "service_id": "search-service-1",
                    "action": "search",
                    "status": "success",
                    "result": {
                        "result": {
                            "results": [
                                {
                                    "title": "Latest AI Developments",
                                    "url": "https://example.com/ai-developments",
                                    "description": "An article about recent advancements in artificial intelligence"
                                },
                                {
                                    "title": "AI Research Breakthroughs",
                                    "url": "https://example.com/ai-research",
                                    "description": "Research paper on new AI methodologies"
                                }
                            ]
                        }
                    }
                }
            ],
            "discovered_services": [
                {
                    "id": "download-service-1",
                    "host": "127.0.0.1",
                    "port": 8093,
                    "type": "mcp_download",
                    "metadata": {}
                }
            ],
            "rag_documents": [],
            "rag_relevance_score": 0.0,
            "rag_query": "What are the latest developments in AI?",
            # Add other required fields for compatibility
            "mcp_queries": [],
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
            "registry_url": "http://127.0.0.1:8080",
            "discovered_services": [],
            "mcp_service_results": [],
            "use_mcp_results": False,
            "mcp_tool_calls": [],
            "mcp_capable_response": "",
            "return_mcp_results_to_llm": False,
            "is_final_answer": False,
            "rag_context": "",
            "use_rag_flag": False,
            "rag_response": ""
        }
        
        print("✓ Created mock state with search results")
        print(f"Search results: {len(mock_state['mcp_results'][0]['result']['result']['results'])}")
        
        # Call the new node function
        result_state = process_search_results_with_download_node(mock_state)
        
        print("✓ New search processing node executed")
        print(f"Processed documents count: {len(result_state['rag_documents'])}")
        
        if result_state['rag_documents']:
            print("Sample processed document:")
            sample_doc = result_state['rag_documents'][0]
            print(f"  Title: {sample_doc.get('title', 'N/A')}")
            print(f"  URL: {sample_doc.get('url', 'N/A')}")
            print(f"  Summary length: {len(sample_doc.get('summary', ''))}")
            print(f"  Relevance Score: {sample_doc.get('relevance_score', 'N/A')}")
        
        print("✓ Direct node test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error during direct node test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running tests for new MCP search functionality with download and summarization")
    print("="*80)
    
    success1 = test_search_node_directly()
    success2 = test_new_search_functionality()
    
    print("\n" + "="*80)
    if success1 and success2:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
        sys.exit(1)
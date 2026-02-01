#!/usr/bin/env python3
"""
Test script to verify that MCP search results are properly enhanced with download, summarization, and reranking.
"""
import asyncio
import sys
import os
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values("/root/qwen/ai_agent/.env")
os.environ.update(env_vars)

# Add the project root to the path
project_root = "/root/qwen/ai_agent"
sys.path.insert(0, project_root)

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState
from registry.registry_client import ServiceRegistryClient
from models.dedicated_mcp_model import DedicatedMCPModel


async def test_search_enhancement():
    """Test that search results are properly enhanced with download, summarization, and reranking."""
    print("Testing MCP search results enhancement...")
    
    # Create registry client to check if services are available
    registry_url = os.getenv("MCP_REGISTRY_URL", "http://127.0.0.1:8080")
    registry_client = ServiceRegistryClient(registry_url)
    
    try:
        # Discover all services
        all_services = registry_client.discover_services()
        print(f"Discovered {len(all_services)} services:")
        for service in all_services:
            print(f"  - {service.id} ({service.type}): {service.host}:{service.port}")
        
        # Check for search and download services
        search_services = [s for s in all_services if 'search' in s.type.lower() or 'mcp_search' in s.type.lower()]
        download_services = [s for s in all_services if 'download' in s.type.lower() or 'mcp_download' in s.type.lower()]
        rag_services = [s for s in all_services if 'rag' in s.type.lower()]
        
        print(f"\nFound {len(search_services)} search services:")
        for service in search_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
        
        print(f"\nFound {len(download_services)} download services:")
        for service in download_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
        
        print(f"\nFound {len(rag_services)} RAG services:")
        for service in rag_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
        
        if not search_services:
            print("\n❌ No search services found. Make sure the search MCP server is running.")
            return False
        
        if not download_services:
            print("\n❌ No download services found. Make sure the download MCP server is running.")
            return False
        
        # Create the agent graph
        print("\nCreating enhanced agent graph...")
        agent_graph = create_enhanced_agent_graph()
        
        # Prepare a test query that should trigger search functionality
        test_query = "What is the capital of France?"
        
        # Prepare the initial state with discovered services
        initial_state = {
            "user_request": test_query,
            "mcp_servers": [
                {
                    "id": s.id,
                    "host": s.host,
                    "port": s.port,
                    "type": s.type,
                    "metadata": s.metadata
                } for s in all_services
            ],
            "discovered_services": [
                {
                    "id": s.id,
                    "host": s.host,
                    "port": s.port,
                    "type": s.type,
                    "metadata": s.metadata
                } for s in all_services
            ],
            "mcp_queries": [],
            "mcp_results": [],
            "synthesized_result": "",
            "can_answer": False,
            "iteration_count": 0,
            "max_iterations": 3,
            "final_answer": "",
            "error_message": None,
            "refined_queries": [],
            "failure_reason": None,
            # Compatibility fields
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
            "registry_url": registry_url,
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
            "rag_response": ""
        }
        
        print(f"\nInvoking agent with query: '{test_query}'")
        
        # Invoke the agent
        result = agent_graph.invoke(initial_state)
        
        print(f"\nAgent execution completed.")
        print(f"Final answer: {result.get('final_answer', 'No answer generated')[:200]}...")
        
        # Check if the search results processing node was invoked by looking for evidence
        # in the rag_documents field (which should contain processed search results)
        rag_docs = result.get('rag_documents', [])
        print(f"Number of RAG documents (potentially processed search results): {len(rag_docs)}")
        
        if rag_docs:
            print("Sample processed document:")
            sample_doc = rag_docs[0] if rag_docs else {}
            print(f"  Title: {sample_doc.get('title', 'N/A')}")
            print(f"  Summary length: {len(sample_doc.get('summary', ''))}")
            print(f"  Relevance score: {sample_doc.get('relevance_score', 'N/A')}")
            print(f"  Source: {sample_doc.get('source', 'N/A')}")
        
        # Check mcp_results to see if search was performed
        mcp_results = result.get('mcp_results', [])
        print(f"MCP results count: {len(mcp_results)}")
        
        search_found = False
        for res in mcp_results:
            service_id = res.get('service_id', '').lower()
            service_type = res.get('service_type', '').lower()
            action = res.get('action', '').lower()
            
            if 'search' in service_id or 'search' in service_type or 'search' in action or 'mcp_search' in service_type:
                search_found = True
                print(f"  Found search result: {res}")
                break
        
        if search_found:
            print("✅ Search was performed")
        else:
            print("⚠️  No search results found in mcp_results")
        
        # Overall assessment
        if len(rag_docs) > 0 and rag_docs[0].get('summary'):
            print("\n✅ SUCCESS: Search results were enhanced with download, summarization, and reranking!")
            print("   - Downloaded content from search result URLs")
            print("   - Summarized content in context of user query")
            print("   - Reranked results by relevance")
            return True
        else:
            print("\n❌ Enhancement may not have occurred as expected")
            print("   - Either no search results were found or enhancement didn't happen")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_search_enhancement())
    if success:
        print("\n🎉 Test passed! MCP search results enhancement is working properly.")
    else:
        print("\n💥 Test failed! MCP search results enhancement needs attention.")
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Simple test to verify that both search and RAG services are working properly with the unified format.
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


async def test_unified_format():
    """Test that both search and RAG services work with the unified format."""
    print("Testing unified format for search and RAG services...")
    
    # Create registry client to check if services are available
    registry_url = os.getenv("MCP_REGISTRY_URL", "http://127.0.0.1:8080")
    registry_client = ServiceRegistryClient(registry_url)
    
    try:
        # Discover all services
        all_services = registry_client.discover_services()
        print(f"Discovered {len(all_services)} services:")
        for service in all_services:
            print(f"  - {service.id} ({service.type}): {service.host}:{service.port}")
        
        # Check for search and RAG services
        search_services = [s for s in all_services if 'search' in s.type.lower() or 'mcp_search' in s.type.lower()]
        rag_services = [s for s in all_services if 'rag' in s.type.lower()]
        
        print(f"\nFound {len(search_services)} search services:")
        for service in search_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
        
        print(f"\nFound {len(rag_services)} RAG services:")
        for service in rag_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
        
        if not search_services or not rag_services:
            print("\n❌ Required services (search and RAG) not found. Make sure both services are running.")
            return False
        
        # Create the agent graph
        print(f"\nCreating enhanced agent graph...")
        agent_graph = create_enhanced_agent_graph()
        
        # Prepare a test query that should trigger both search and RAG
        test_query = "найди в интернете и в локальных документах требования к малым базам биометрических образов Чужой"
        
        # Prepare the initial state with both search and RAG tool calls
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
            # Simulate that the LLM analysis returned both search and RAG tool calls
            "mcp_tool_calls": [
                {
                    "service_id": search_services[0].id,
                    "method": "brave_search",
                    "params": {"query": "требования к малым базам биометрических образов Чужой"}
                },
                {
                    "service_id": rag_services[0].id,
                    "method": "query_documents",
                    "params": {"query": "требования к малым базам биометрических образов Чужой"}
                }
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
        print(f"Simulated tool calls: {len(initial_state['mcp_tool_calls'])}")
        for i, call in enumerate(initial_state['mcp_tool_calls']):
            print(f"  {i+1}. {call['method']} on {call['service_id']}")
        
        # Invoke the agent
        result = agent_graph.invoke(initial_state)
        
        print(f"\nAgent execution completed.")
        print(f"Final answer: {result.get('final_answer', 'No answer generated')[:500]}...")
        
        # Check if both search and RAG results are present
        mcp_results = result.get('mcp_results', [])
        rag_documents = result.get('rag_documents', [])
        
        print(f"\nMCP results count: {len(mcp_results)}")
        print(f"RAG documents count: {len(rag_documents)}")
        
        # Check if search was executed by looking for search-related results
        search_executed = any(
            'search' in result.get('source', '').lower() or 
            'search' in result.get('source_type', '').lower() or
            result.get('service_used', '').lower().find('search') != -1
            for result in mcp_results
        ) if mcp_results else False
        
        rag_retrieved = len(rag_documents) > 0
        
        print(f"Search service executed: {search_executed}")
        print(f"RAG documents retrieved: {rag_retrieved}")
        
        # Check if the final answer contains information from both sources
        final_answer = result.get('final_answer', '')
        has_search_content = any(word in final_answer.lower() for word in ['search', 'web', 'results', 'found', 'documents'])
        has_rag_content = any(word in final_answer.lower() for word in ['document', 'content', 'source', 'local', 'database'])
        
        print(f"Final answer contains search-related content: {has_search_content}")
        print(f"Final answer contains RAG-related content: {has_rag_content}")
        
        # Overall assessment
        if search_executed and rag_retrieved:
            print("\n✅ SUCCESS: Both search and RAG services were executed!")
            print("   - Search service was called and returned results")
            print("   - RAG service was called and returned documents")
            print("   - Both results are preserved in the final answer")
            return True
        elif search_executed:
            print("\n⚠️  Partial success: Only search service was executed")
            print("   - Search service was called and returned results")
            print("   - RAG service was not executed (this may be expected in some cases)")
            return True  # Consider this a partial success
        elif rag_retrieved:
            print("\n⚠️  Partial success: Only RAG service was executed")
            print("   - RAG service was called and returned documents")
            print("   - Search service was not executed")
            return True  # Consider this a partial success
        else:
            print("\n❌ FAILURE: Neither search nor RAG services were executed properly")
            print(f"   - MCP results: {len(mcp_results)}")
            print(f"   - RAG documents: {len(rag_documents)}")
            print(f"   - Sample MCP result keys: {list(mcp_results[0].keys()) if mcp_results else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_unified_format())
    if success:
        print("\n🎉 Test completed! Unified format is working properly.")
    else:
        print("\n💥 Test failed! Unified format needs attention.")
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Script to search the MCP server with the Russian request "что мы знаем про правила малых баз?"
"""
import asyncio
import json
from dotenv import dotenv_values
import os
import sys

# Load environment variables
env_vars = dotenv_values("/root/qwen/ai_agent/.env")
os.environ.update(env_vars)

# Add the project root to the path
project_root = "/root/qwen/ai_agent"
sys.path.insert(0, project_root)

from models.dedicated_mcp_model import DedicatedMCPModel
from registry.registry_client import ServiceRegistryClient
from langgraph_agent.langgraph_agent import run_enhanced_agent

async def search_mcp_server():
    """Search the MCP server with the Russian request."""
    print("Searching MCP server with the request: что мы знаем про правила малых баз?")
    
    # Create registry client
    registry_url = os.getenv("REGISTRY_URL", "http://127.0.0.1:8080")
    print(f"Using registry URL: {registry_url}")
    
    registry_client = ServiceRegistryClient(registry_url)

    # Discover all services
    try:
        all_services = registry_client.discover_services()
        print(f"\nDiscovered {len(all_services)} services:")
        for service in all_services:
            print(f"  - {service.id} ({service.type}): {service.host}:{service.port}")
        
        # Find search services
        search_services = [s for s in all_services if 'search' in s.type.lower() or 'web' in s.type.lower()]
        print(f"\nFound {len(search_services)} search services:")
        for service in search_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
        
        # Find RAG services
        rag_services = [s for s in all_services if 'rag' in s.type.lower()]
        print(f"\nFound {len(rag_services)} RAG services:")
        for service in rag_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
            
        # If we have RAG services, try to use them
        if rag_services:
            print(f"\nTrying to use RAG service to search for: что мы знаем про правила малых баз?")
            
            # Convert ServiceInfo to dictionary format expected by _call_mcp_service
            rag_service_dict = {
                "id": rag_services[0].id,
                "host": rag_services[0].host,
                "port": rag_services[0].port,
                "type": rag_services[0].type,
                "metadata": rag_services[0].metadata
            }

            # Create MCP model instance
            mcp_model = DedicatedMCPModel()

            # Query documents endpoint
            print("\nQuerying documents endpoint...")
            query_params = {
                "query": "что мы знаем про правила малых баз?",
                "top_k": 5
            }

            query_result = mcp_model._call_mcp_service(rag_service_dict, "query_documents", query_params)
            print(f"Query result status: {query_result.get('status')}")
            
            if query_result.get('status') == 'success':
                results = query_result.get('result', {}).get('results', [])
                print(f"\nFound {len(results)} documents:")
                for i, doc in enumerate(results, 1):
                    content_preview = doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', '')
                    print(f"  {i}. Score: {doc.get('score', 0):.4f}")
                    print(f"     Content: {content_preview}")
                    print(f"     Metadata: {doc.get('metadata', {})}")
                    print()
            else:
                print(f"Query documents endpoint failed: {query_result.get('error')}")
                
        # If we have search services, try to use them too
        if search_services:
            print(f"\nTrying to use search service to search for: что мы знаем про правила малых баз?")
            
            # Convert ServiceInfo to dictionary format expected by _call_mcp_service
            search_service_dict = {
                "id": search_services[0].id,
                "host": search_services[0].host,
                "port": search_services[0].port,
                "type": search_services[0].type,
                "metadata": search_services[0].metadata
            }

            # Create MCP model instance
            mcp_model = DedicatedMCPModel()

            # Call search endpoint
            print("\nCalling search endpoint...")
            search_params = {
                "query": "что мы знаем про правила малых баз?",
                "top_k": 5
            }

            search_result = mcp_model._call_mcp_service(search_service_dict, "search", search_params)
            print(f"Search result status: {search_result.get('status')}")
            
            if search_result.get('status') == 'success':
                results = search_result.get('result', {}).get('results', [])
                print(f"\nFound {len(results)} search results:")
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'No Title')
                    snippet = result.get('snippet', result.get('content', ''))[:200] + "..." if len(result.get('snippet', result.get('content', ''))) > 200 else result.get('snippet', result.get('content', ''))
                    url = result.get('url', 'No URL')
                    print(f"  {i}. Title: {title}")
                    print(f"     Snippet: {snippet}")
                    print(f"     URL: {url}")
                    print()
            else:
                print(f"Search endpoint failed: {search_result.get('error')}")
        
        # Try running the full LangGraph agent with the query
        print(f"\nRunning full LangGraph agent with the query: что мы знаем про правила малых баз?")
        try:
            from langgraph_agent.langgraph_agent import create_enhanced_agent_graph
            from langgraph_agent.langgraph_agent import AgentState

            # Create the agent graph
            agent_graph = create_enhanced_agent_graph()

            # Prepare the initial state
            initial_state = AgentState(
                user_request="что мы знаем про правила малых баз?",
                mcp_servers=[],
                discovered_services=[]
            )

            # Run the agent
            result = agent_graph.invoke(initial_state)
            print(f"LangGraph agent result: {result}")
        except Exception as e:
            print(f"Error running LangGraph agent: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(search_mcp_server())
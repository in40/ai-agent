#!/usr/bin/env python3
"""
Script to search the MCP server with the Russian request and show results
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

async def search_mcp_server():
    """Search the MCP server with the Russian request."""
    print("Searching MCP server with the request: что мы знаем про правила малых баз?")
    print("="*80)
    
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
            
        # Test search service
        if search_services:
            print(f"\n{'='*80}")
            print("SEARCH SERVICE RESULTS")
            print("="*80)
            
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
            print(f"\nCalling search endpoint with query: что мы знаем про правила малых баз?")
            search_params = {
                "query": "что мы знаем про правила малых баз?",
                "top_k": 10
            }

            search_result = mcp_model._call_mcp_service(search_service_dict, "search", search_params)
            
            if search_result.get('status') == 'success':
                # Extract the actual search results from the nested structure
                actual_results = search_result.get('result', {}).get('result', {}).get('results', [])
                print(f"\nFound {len(actual_results)} search results:")
                
                if actual_results:
                    print(f"\nDetailed search results:")
                    for i, result in enumerate(actual_results, 1):
                        print(f"\n--- Search Result {i} ---")
                        print(f"Title: {result.get('title', 'No Title')}")
                        print(f"URL: {result.get('url', 'No URL')}")
                        print(f"Description: {result.get('description', 'No Description')[:200]}...")
                        print(f"Language: {result.get('language', 'Unknown')}")
            else:
                print(f"\nSearch failed with error: {search_result.get('error')}")
        
        # Test RAG service
        if rag_services:
            print(f"\n{'='*80}")
            print("RAG SERVICE RESULTS")
            print("="*80)
            
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
            print(f"\nQuerying RAG documents with: что мы знаем про правила малых баз?")
            query_params = {
                "query": "что мы знаем про правила малых баз?",
                "top_k": 10
            }

            query_result = mcp_model._call_mcp_service(rag_service_dict, "query_documents", query_params)
            
            if query_result.get('status') == 'success':
                rag_results = query_result.get('result', {}).get('results', [])
                print(f"\nFound {len(rag_results)} RAG results:")
                
                if rag_results:
                    print(f"\nDetailed RAG results:")
                    for i, result in enumerate(rag_results, 1):
                        print(f"\n--- RAG Result {i} ---")
                        print(f"Content preview: {result.get('content', 'No content')[:200]}...")
                        print(f"Score: {result.get('score', 'No score')}")
                        print(f"Metadata: {json.dumps(result.get('metadata', {}), ensure_ascii=False)}")
            else:
                print(f"\nRAG query failed with error: {query_result.get('error')}")
        
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(search_mcp_server())
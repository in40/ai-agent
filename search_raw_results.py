#!/usr/bin/env python3
"""
Script to search the MCP server with the Russian request and show raw results
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

async def search_mcp_server_raw():
    """Search the MCP server with the Russian request and show raw results."""
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
            
        # Test search service directly
        if search_services:
            print(f"\n{'='*80}")
            print("TESTING SEARCH SERVICE RESULTS")
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
            print(f"\nRaw search result:")
            print(json.dumps(search_result, indent=2, ensure_ascii=False))
            
            if search_result.get('status') == 'success':
                results = search_result.get('result', {}).get('results', [])
                print(f"\nNumber of search results: {len(results)}")
                
                if results:
                    print(f"\nDetailed results:")
                    for i, result in enumerate(results, 1):
                        print(f"\n--- Result {i} ---")
                        for key, value in result.items():
                            if key == 'description' or key == 'content':
                                # Truncate long descriptions
                                value_preview = value[:200] + "..." if len(value) > 200 else value
                                print(f"  {key}: {value_preview}")
                            else:
                                print(f"  {key}: {value}")
            else:
                print(f"\nSearch failed with error: {search_result.get('error')}")
        
        # Test RAG service directly
        if rag_services:
            print(f"\n{'='*80}")
            print("TESTING RAG SERVICE RESULTS")
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
            print(f"\nRaw RAG result:")
            print(json.dumps(query_result, indent=2, ensure_ascii=False))
            
            if query_result.get('status') == 'success':
                results = query_result.get('result', {}).get('results', [])
                print(f"\nNumber of RAG results: {len(results)}")
                
                if results:
                    print(f"\nDetailed RAG results:")
                    for i, result in enumerate(results, 1):
                        print(f"\n--- RAG Result {i} ---")
                        for key, value in result.items():
                            if key == 'content':
                                # Truncate long content
                                value_preview = value[:200] + "..." if len(value) > 200 else value
                                print(f"  {key}: {value_preview}")
                            else:
                                print(f"  {key}: {value}")
            else:
                print(f"\nRAG query failed with error: {query_result.get('error')}")
        
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(search_mcp_server_raw())
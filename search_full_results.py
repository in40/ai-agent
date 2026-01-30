#!/usr/bin/env python3
"""
Script to search the MCP server with the Russian request and show full results
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

async def search_mcp_server_full():
    """Search the MCP server with the Russian request and show full results."""
    print("Searching MCP server with the request: что мы знаем про правила малых баз?")
    print("="*80)
    
    # Create registry client
    registry_url = os.getenv("REGISTRY_URL", "http://127.0.0.1:8080")
    print(f"Using registry URL: {registry_url}")
    
    registry_client = ServiceRegistryClient(registry_url)

    # Discover RAG services
    try:
        all_services = registry_client.discover_services()
        rag_services = [s for s in all_services if 'rag' in s.type.lower()]
        
        if rag_services:
            print(f"\nFound {len(rag_services)} RAG services:")
            for service in rag_services:
                print(f"  - {service.id}: {service.host}:{service.port}")
            
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
                "top_k": 5  # Limit to top 5 results for readability
            }

            query_result = mcp_model._call_mcp_service(rag_service_dict, "query_documents", query_params)
            
            if query_result.get('status') == 'success':
                rag_results = query_result.get('result', {}).get('results', [])
                print(f"\nFound {len(rag_results)} RAG results:")
                
                if rag_results:
                    print(f"\nDetailed RAG results with full content:")
                    for i, result in enumerate(rag_results, 1):
                        print(f"\n{'='*80}")
                        print(f"RAG Result {i}")
                        print(f"{'='*80}")
                        print(f"Score: {result.get('score', 'No score')}")
                        print(f"Source: {result.get('metadata', {}).get('source', 'Unknown source')}")
                        print(f"Section: {result.get('metadata', {}).get('section', 'Unknown section')}")
                        print(f"Title: {result.get('metadata', {}).get('title', 'No title')}")
                        print(f"Content:")
                        print(f"{'-'*40}")
                        print(f"{result.get('content', 'No content')}")
                        print(f"{'-'*40}")
                        print(f"Other metadata: {json.dumps({k:v for k,v in result.get('metadata', {}).items() if k not in ['source', 'section', 'title', 'content']}, indent=2, ensure_ascii=False)}")
            else:
                print(f"\nRAG query failed with error: {query_result.get('error')}")
        
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(search_mcp_server_full())
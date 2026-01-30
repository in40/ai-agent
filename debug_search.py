#!/usr/bin/env python3
"""
Script to debug the search MCP server functionality
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

async def debug_search_functionality():
    """Debug the search functionality."""
    print("Debugging search functionality...")
    
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
            
        if search_services:
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

            # Test different query formats
            test_queries = [
                "что мы знаем про правила малых баз?",
                "правила малых баз",
                "малые базы",
                "small databases",
                "database rules"
            ]
            
            for query in test_queries:
                print(f"\n--- Testing query: '{query}' ---")
                
                # Call search endpoint with different methods
                search_methods = ["search", "query", "search_web", "web_search"]
                
                for method in search_methods:
                    print(f"  Trying method: {method}")
                    
                    search_params = {
                        "query": query,
                        "top_k": 5
                    }

                    try:
                        search_result = mcp_model._call_mcp_service(search_service_dict, method, search_params)
                        print(f"    Result status: {search_result.get('status')}")
                        
                        if search_result.get('status') == 'success':
                            results = search_result.get('result', {}).get('results', [])
                            print(f"    Found {len(results)} results")
                            
                            if results:
                                for i, result in enumerate(results[:3]):  # Show first 3 results
                                    title = result.get('title', 'No Title')
                                    snippet = result.get('snippet', result.get('content', ''))[:200] + "..." if len(result.get('snippet', result.get('content', ''))) > 200 else result.get('snippet', result.get('content', ''))
                                    url = result.get('url', 'No URL')
                                    print(f"      {i+1}. Title: {title}")
                                    print(f"         Snippet: {snippet}")
                                    print(f"         URL: {url}")
                                    print()
                        else:
                            print(f"    Error: {search_result.get('error')}")
                            
                    except Exception as e:
                        print(f"    Method {method} failed: {e}")
                        
        # Also test the RAG service with different queries to compare
        rag_services = [s for s in all_services if 'rag' in s.type.lower()]
        print(f"\nFound {len(rag_services)} RAG services:")
        for service in rag_services:
            print(f"  - {service.id}: {service.host}:{service.port}")
            
        if rag_services:
            print(f"\n--- Testing RAG service with different queries ---")
            
            # Convert ServiceInfo to dictionary format expected by _call_mcp_service
            rag_service_dict = {
                "id": rag_services[0].id,
                "host": rag_services[0].host,
                "port": rag_services[0].port,
                "type": rag_services[0].type,
                "metadata": rag_services[0].metadata
            }

            # Test different queries with RAG
            rag_test_queries = [
                "что мы знаем про правила малых баз?",
                "правила малых баз",
                "малые базы",
                "small databases",
                "database rules"
            ]
            
            for query in rag_test_queries:
                print(f"\n  Testing RAG query: '{query}'")
                
                query_params = {
                    "query": query,
                    "top_k": 5
                }

                try:
                    query_result = mcp_model._call_mcp_service(rag_service_dict, "query_documents", query_params)
                    print(f"    RAG result status: {query_result.get('status')}")
                    
                    if query_result.get('status') == 'success':
                        results = query_result.get('result', {}).get('results', [])
                        print(f"    RAG found {len(results)} documents")
                    else:
                        print(f"    RAG error: {query_result.get('error')}")
                        
                except Exception as e:
                    print(f"    RAG query '{query}' failed: {e}")
        
    except Exception as e:
        print(f"Error in search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_search_functionality())
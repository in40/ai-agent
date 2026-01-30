#!/usr/bin/env python3
"""
Test script to verify how the MCP model calls the search service
"""
import json
import requests
from models.dedicated_mcp_model import DedicatedMCPModel
from registry.registry_client import ServiceRegistryClient

# Create registry client
registry_client = ServiceRegistryClient("http://127.0.0.1:8080")

# Discover search services
search_services = registry_client.discover_services(service_type="mcp_search")
print(f"Found {len(search_services)} search services")

if search_services:
    search_service = search_services[0]
    print(f"Testing search service: {search_service.id} at {search_service.host}:{search_service.port}")
    
    # Convert ServiceInfo to dictionary format expected by _call_mcp_service
    search_service_dict = {
        "id": search_service.id,
        "host": search_service.host,
        "port": search_service.port,
        "type": search_service.type,
        "metadata": search_service.metadata
    }

    # Create MCP model instance
    mcp_model = DedicatedMCPModel()

    # Test calling the search service using the same method as the LangGraph agent
    print("\nTesting _call_mcp_service method...")
    search_params = {
        "query": "что мы знаем про правила малых баз?",
        "top_k": 5
    }

    search_result = mcp_model._call_mcp_service(search_service_dict, "search", search_params)
    print(f"Search result status: {search_result.get('status')}")
    
    if search_result.get('status') == 'success':
        results = search_result.get('result', {}).get('results', [])
        print(f"Found {len(results)} results from _call_mcp_service")
        
        if results:
            print("First few results:")
            for i, result in enumerate(results[:3]):
                title = result.get('title', 'No Title')
                snippet = result.get('snippet', result.get('content', ''))[:200] + "..." if len(result.get('snippet', result.get('content', ''))) > 200 else result.get('snippet', result.get('content', ''))
                url = result.get('url', 'No URL')
                print(f"  {i+1}. Title: {title}")
                print(f"     Snippet: {snippet}")
                print(f"     URL: {url}")
                print()
    else:
        print(f"Search failed: {search_result.get('error')}")
        
    # Let's also test what the actual HTTP request looks like
    print("\nTesting direct HTTP request with the same format as _call_mcp_service...")
    base_url = f"http://{search_service.host}:{search_service.port}"
    endpoint = f"{base_url}/search"
    
    payload = {
        "action": "search",
        "parameters": {
            "query": "что мы знаем про правила малых баз?",
            "top_k": 5
        },
        "timestamp": "2026-01-30T13:49:39.123456Z"
    }
    
    print(f"Sending payload: {json.dumps(payload, ensure_ascii=False)}")
    
    response = requests.post(
        endpoint,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    print(f"Direct HTTP response status: {response.status_code}")
    print(f"Direct HTTP response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
else:
    print("No search services found!")
#!/usr/bin/env python3
"""
Test script to debug the exact difference between direct call and MCP call
"""
import json
import requests
from models.dedicated_mcp_model import DedicatedMCPModel
from registry.registry_client import ServiceRegistryClient

# Create registry client
registry_client = ServiceRegistryClient("http://127.0.0.1:8080")

# Discover search services
search_services = registry_client.discover_services(service_type="mcp_search")
search_service = search_services[0]

# Convert to dictionary format
search_service_dict = {
    "id": search_service.id,
    "host": search_service.host,
    "port": search_service.port,
    "type": search_service.type,
    "metadata": search_service.metadata
}

print(f"Testing service: {search_service_dict['id']}")
print(f"Host: {search_service_dict['host']}, Port: {search_service_dict['port']}")

# Create MCP model instance
mcp_model = DedicatedMCPModel()

# Test 1: Direct HTTP call (this worked before)
print("\n=== Test 1: Direct HTTP call ===")
direct_url = f"http://{search_service_dict['host']}:{search_service_dict['port']}"
direct_payload = {"query": "что мы знаем про правила малых баз?"}

print(f"Direct payload: {json.dumps(direct_payload, ensure_ascii=False)}")

direct_response = requests.post(
    direct_url,
    json=direct_payload,
    headers={'Content-Type': 'application/json'},
    timeout=30
)

print(f"Direct response status: {direct_response.status_code}")
direct_result = direct_response.json()
print(f"Direct results count: {len(direct_result.get('result', {}).get('results', []))}")

# Test 2: MCP call with action (this is what _call_mcp_service does)
print("\n=== Test 2: MCP call with action ===")
action_url = f"http://{search_service_dict['host']}:{search_service_dict['port']}/search"
action_payload = {
    "action": "search",
    "parameters": {"query": "что мы знаем про правила малых баз?"},
    "timestamp": "2026-01-30T13:52:43.123456Z"
}

print(f"Action payload: {json.dumps(action_payload, ensure_ascii=False)}")

action_response = requests.post(
    action_url,
    json=action_payload,
    headers={'Content-Type': 'application/json'},
    timeout=30
)

print(f"Action response status: {action_response.status_code}")
action_result = action_response.json()
print(f"Action results count: {len(action_result.get('result', {}).get('results', []))}")

# Test 3: Using the MCP model's _call_mcp_service method
print("\n=== Test 3: Using MCP model's _call_mcp_service ===")
mcp_result = mcp_model._call_mcp_service(
    search_service_dict,
    "search",
    {"query": "что мы знаем про правила малых баз?"}
)

print(f"MCP result status: {mcp_result.get('status')}")
mcp_results = mcp_result.get('result', {}).get('results', [])
print(f"MCP results count: {len(mcp_results)}")

# Let's also check what the search server expects by looking at its code again
print("\n=== Analysis ===")
print("The search server expects:")
print("1. POST request to the root endpoint (/) with query in the body")
print("2. OR POST request to /search endpoint with query in the body")
print("")
print("The MCP model sends:")
print("POST request to /search endpoint with:")
print('{"action": "search", "parameters": {"query": "..."}}')
print("")
print("The search server's SearchRequestHandler.do_POST method looks for:")
print("- request_data['query'] at the top level")
print("- OR request_data['parameters']['query'] if parameters exist")
print("")
print("So it SHOULD work with the MCP format, but let's see what's happening...")

# Let's try the exact format the search server expects
print("\n=== Test 4: Format expected by search server ===")
expected_format_payload = {
    "query": "что мы знаем про правила малых баз?",
    "top_k": 5
}

expected_format_response = requests.post(
    f"http://{search_service_dict['host']}:{search_service_dict['port']}/search",
    json=expected_format_payload,
    headers={'Content-Type': 'application/json'},
    timeout=30
)

print(f"Expected format response status: {expected_format_response.status_code}")
expected_result = expected_format_response.json()
print(f"Expected format results count: {len(expected_result.get('result', {}).get('results', []))}")

if expected_format_response.status_code == 200:
    print("Expected format result keys:", list(expected_result.keys()))
    if 'result' in expected_result:
        print("Expected format inner result keys:", list(expected_result['result'].keys()))
        if 'results' in expected_result['result']:
            print("First few results from expected format:")
            for i, result in enumerate(expected_result['result']['results'][:2]):
                print(f"  {i+1}. {result.get('title', 'No title')[:50]}...")
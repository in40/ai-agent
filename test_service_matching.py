#!/usr/bin/env python3
"""
Test script to verify the service matching issue
"""
from models.dedicated_mcp_model import DedicatedMCPModel
from registry.registry_client import ServiceRegistryClient

# Create registry client
registry_client = ServiceRegistryClient("http://127.0.0.1:8080")

# Discover all services
all_services = registry_client.discover_services()
print("All discovered services:")
for service in all_services:
    print(f"  ID: {service.id}, Type: {service.type}, Host: {service.host}:{service.port}")

print()

# Test the service lookup issue
mcp_model = DedicatedMCPModel()

# Simulate what happens in execute_mcp_tool_calls
service_lookup = {service['id']: service for service in [
    {
        "id": svc.id,
        "host": svc.host,
        "port": svc.port,
        "type": svc.type,
        "metadata": svc.metadata
    } for svc in all_services
]}

print("Service lookup dictionary keys:")
for key in service_lookup.keys():
    print(f"  {key}")

print()

# Test what happens when we try to look up "mcp_search" (what LLM might generate)
test_service_id = "mcp_search"
if test_service_id in service_lookup:
    print(f"✓ Found service with ID '{test_service_id}'")
else:
    print(f"✗ Service with ID '{test_service_id}' NOT FOUND")
    
    # Look for services by type instead
    matching_by_type = [svc for svc in all_services if svc.type == test_service_id]
    print(f"  Found {len(matching_by_type)} services by TYPE '{test_service_id}':")
    for svc in matching_by_type:
        print(f"    - {svc.id}")

print()

# Test with the actual search service ID
search_services = [svc for svc in all_services if svc.type == "mcp_search"]
if search_services:
    actual_search_service_id = search_services[0].id
    print(f"Actual search service ID: {actual_search_service_id}")
    
    # Test if this ID exists in the lookup
    if actual_search_service_id in service_lookup:
        print(f"✓ Found actual service with ID '{actual_search_service_id}'")
        
        # Test calling it
        result = mcp_model._call_mcp_service(
            service_lookup[actual_search_service_id],
            "search",
            {"query": "что мы знаем про правила малых баз?"}
        )
        print(f"  Search result status: {result.get('status')}")
        if result.get('status') == 'success':
            results = result.get('result', {}).get('results', [])
            print(f"  Found {len(results)} results")
    else:
        print(f"✗ Actual service with ID '{actual_search_service_id}' NOT FOUND")
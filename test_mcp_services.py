#!/usr/bin/env python3
"""
Test script to verify MCP service registration and discovery.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_service_registration():
    """Test if MCP services are properly registered and discoverable."""
    print("Testing MCP Service Registration and Discovery...")
    print("=" * 50)
    
    try:
        # Import the registry client
        from registry.registry_client import ServiceRegistryClient
        
        # Create a registry client
        registry_url = "http://127.0.0.1:8080"
        client = ServiceRegistryClient(registry_url)
        
        # Check if registry is accessible
        print("Checking registry health...")
        if client.check_health():
            print("✓ Registry is healthy")
        else:
            print("✗ Registry is not accessible")
            return False
        
        # List all services
        print("\nListing all registered services...")
        services = client.list_all_services()
        
        print(f"Found {len(services)} services:")
        for i, service in enumerate(services):
            print(f"  {i+1}. ID: {service.id}")
            print(f"     Host: {service.host}")
            print(f"     Port: {service.port}")
            print(f"     Type: {service.type}")
            print(f"     Metadata: {service.metadata}")
            print()
        
        # Check for search-related services
        search_services = [s for s in services if 'search' in s.id.lower() or 'search' in s.type.lower()]
        print(f"Found {len(search_services)} search-related services:")
        for service in search_services:
            print(f"  - {service.id} at {service.host}:{service.port}")
        
        if not search_services:
            print("\n⚠ No search services found. This could be the issue!")
            print("The search server might not be running or properly registered.")
        
        # Check for any services that might match the expected pattern
        expected_ids = [
            "search_server-127-0-0-1-8090",  # What the agent is looking for
            "search-server-127-0-0-1-8090",  # What the server registers as
        ]
        
        print(f"\nLooking for services with expected IDs: {expected_ids}")
        for exp_id in expected_ids:
            found = any(s.id == exp_id for s in services)
            print(f"  {exp_id}: {'Found' if found else 'Not found'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during service registration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_server_connection():
    """Test if the search server is accessible directly."""
    print("\nTesting direct connection to search server...")
    print("=" * 50)
    
    try:
        import requests
        
        # Try to connect to the search server directly
        search_url = "http://127.0.0.1:8090"
        
        # Try a simple GET request to see if the server responds
        try:
            response = requests.get(search_url, timeout=5)
            print(f"GET request to {search_url}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"GET request to {search_url} failed: {e}")
        
        # Try a POST request with minimal data to see if it accepts requests
        try:
            test_data = {"query": "test"}
            response = requests.post(
                f"{search_url}", 
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print(f"POST request to {search_url}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"POST request to {search_url} failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during search server connection test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("MCP Service Registration Test")
    print("=" * 50)
    
    reg_test = test_service_registration()
    conn_test = test_search_server_connection()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Service Registration Test: {'PASS' if reg_test else 'FAIL'}")
    print(f"  Search Server Connection Test: {'PASS' if conn_test else 'FAIL'}")
    
    if not reg_test:
        print("\nPossible causes for service registration issues:")
        print("1. The search server is not running")
        print("2. The search server failed to register with the registry")
        print("3. There's a mismatch in service ID format")
        print("4. The registry URL is incorrect")
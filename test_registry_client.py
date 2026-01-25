#!/usr/bin/env python3
"""
Simple test to verify that the registry discovery functionality is working.
"""

import sys
import os

def test_registry_client():
    """Test the registry client directly"""
    
    print("Testing registry client connection...")
    
    try:
        from registry.registry_client import ServiceRegistryClient
        
        # Create a client instance
        client = ServiceRegistryClient("http://127.0.0.1:8080")
        
        # Check if registry is healthy
        is_healthy = client.check_health()
        print(f"✓ Registry health: {is_healthy}")
        
        if not is_healthy:
            print("✗ Registry is not healthy")
            return False
        
        # Discover services
        services = client.discover_services()
        print(f"✓ Discovered {len(services)} services from registry")
        
        for i, service in enumerate(services):
            print(f"  {i+1}. {service.type} - {service.host}:{service.port} (ID: {service.id})")
        
        return len(services) > 0
        
    except Exception as e:
        print(f"✗ Error testing registry client: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_discover_services_node():
    """Test the discover_services_node function directly"""
    
    print("\nTesting discover_services_node function...")
    
    try:
        from langgraph_agent.langgraph_agent import discover_services_node
        
        # Create a test state with registry URL
        test_state = {
            "user_request": "Test request",
            "registry_url": "http://127.0.0.1:8080",
            "mcp_servers": [],
            "discovered_services": []
        }
        
        print(f"Input state: registry_url={test_state['registry_url']}")
        
        # Call the function
        result = discover_services_node(test_state)
        
        print(f"Output state: {len(result['mcp_servers'])} servers, {len(result['discovered_services'])} discovered services")
        
        # Check if services were discovered
        if len(result['mcp_servers']) > 0 or len(result['discovered_services']) > 0:
            print("✓ Services were discovered by the node")
            for i, service in enumerate(result['mcp_servers'] or result['discovered_services']):
                print(f"  {i+1}. {service.get('type', 'Unknown')} - {service.get('host', 'Unknown')}:{service.get('port', 'Unknown')}")
            return True
        else:
            print("✗ No services were discovered by the node")
            return False
            
    except Exception as e:
        print(f"✗ Error testing discover_services_node: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Verifying MCP registry discovery fix...\n")
    
    success1 = test_registry_client()
    success2 = test_discover_services_node()
    
    if success1 and success2:
        print("\n🎉 SUCCESS: MCP registry discovery is working correctly!")
        print("- Registry client can connect and discover services")
        print("- discover_services_node can discover services from the registry")
        print("- The mcp_servers list is now populated with discovered services")
    else:
        print("\n❌ FAILURE: Issues remain with MCP registry discovery")
        sys.exit(1)
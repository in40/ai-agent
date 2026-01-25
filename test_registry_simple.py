#!/usr/bin/env python3
"""
Simple test to verify that MCP registry discovery is working.
"""

def test_registry_discovery():
    """Test that registry discovery is working"""
    
    print("Testing MCP registry discovery...")
    
    # Test direct registry access
    try:
        from registry.registry_client import ServiceRegistryClient
        
        print("✓ Successfully imported ServiceRegistryClient")
        
        # Test connecting to the registry
        client = ServiceRegistryClient("http://127.0.0.1:8080")
        print("✓ Successfully created registry client")
        
        # Check health
        is_healthy = client.check_health()
        print(f"✓ Registry health: {is_healthy}")
        
        if is_healthy:
            # Discover services
            services = client.discover_services()
            print(f"✓ Discovered {len(services)} services from registry")
            
            for i, service in enumerate(services):
                print(f"  {i+1}. {service.type} - {service.host}:{service.port} (ID: {service.id})")
                
            return len(services) > 0
        else:
            print("✗ Registry is not healthy")
            return False
            
    except Exception as e:
        print(f"✗ Error testing registry: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_discover_services_node():
    """Test the discover_services_node function directly"""
    
    print("\nTesting discover_services_node function...")
    
    try:
        from langgraph_agent.langgraph_agent import discover_services_node
        
        print("✓ Successfully imported discover_services_node")
        
        # Create a test state with registry URL
        test_state = {
            "user_request": "Test request",
            "registry_url": "http://127.0.0.1:8080",
            "mcp_servers": [],
            "discovered_services": []
        }
        
        print(f"✓ Created test state with registry URL: {test_state['registry_url']}")
        
        # Call the discovery function
        result = discover_services_node(test_state)
        
        print("✓ discover_services_node executed successfully")
        
        # Check the results
        discovered_services = result.get('discovered_services', [])
        mcp_servers = result.get('mcp_servers', [])
        
        print(f"✓ Number of discovered services: {len(discovered_services)}")
        print(f"✓ Number of MCP servers: {len(mcp_servers)}")
        
        if discovered_services:
            print("✓ Discovered services:")
            for i, service in enumerate(discovered_services):
                print(f"  {i+1}. {service.get('type', 'Unknown type')} - {service.get('host', 'Unknown host')}:{service.get('port', 'Unknown port')}")
        
        if mcp_servers:
            print("✓ MCP servers:")
            for i, server in enumerate(mcp_servers):
                print(f"  {i+1}. {server.get('type', 'Unknown type')} - {server.get('host', 'Unknown host')}:{server.get('port', 'Unknown port')}")
        
        return len(discovered_services) > 0 or len(mcp_servers) > 0
        
    except Exception as e:
        print(f"✗ Error testing discover_services_node: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running MCP registry discovery verification...\n")
    
    registry_success = test_registry_discovery()
    node_success = test_discover_services_node()
    
    print(f"\nRegistry discovery: {'✓ PASS' if registry_success else '✗ FAIL'}")
    print(f"Node discovery: {'✓ PASS' if node_success else '✗ FAIL'}")
    
    if registry_success and node_success:
        print("\n🎉 SUCCESS: MCP registry discovery is working correctly!")
        print("- Registry can be accessed and services discovered")
        print("- discover_services_node can discover services from registry")
        print("- Services are properly populated in the state")
    else:
        print("\n❌ FAILURE: MCP registry discovery is not working correctly")
        exit(1)
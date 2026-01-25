#!/usr/bin/env python3
"""
Test to check if the discover_services_node can actually connect to the registry.
"""

def test_discover_services_with_actual_registry():
    """Test the discover_services_node with the actual running registry"""
    
    from langgraph_agent.langgraph_agent import discover_services_node
    
    # Create a state with the actual registry URL
    state_with_registry = {
        "user_request": "Test request to discover services",
        "registry_url": "http://127.0.0.1:8080",
        "mcp_servers": [],
        "discovered_services": []
    }
    
    print("Testing discover_services_node with actual registry...")
    print(f"Registry URL: {state_with_registry['registry_url']}")
    
    try:
        result = discover_services_node(state_with_registry)
        
        print(f"Discovery result keys: {list(result.keys())}")
        print(f"Number of discovered services: {len(result['discovered_services'])}")
        print(f"Number of MCP servers: {len(result['mcp_servers'])}")
        
        if result['discovered_services']:
            print("Discovered services:")
            for i, service in enumerate(result['discovered_services']):
                print(f"  {i+1}. ID: {service['id']}, Type: {service['type']}, Host: {service['host']}, Port: {service['port']}")
        else:
            print("No services discovered!")
            
        if result['mcp_servers']:
            print("MCP Servers:")
            for i, server in enumerate(result['mcp_servers']):
                print(f"  {i+1}. ID: {server['id']}, Type: {server['type']}, Host: {server['host']}, Port: {server['port']}")
        else:
            print("No MCP servers found!")
            
        return result
    
    except Exception as e:
        print(f"Error during service discovery: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_registry_connection_manually():
    """Manually test registry connection using the registry client"""
    
    try:
        from registry.registry_client import ServiceRegistryClient
        
        print("\nTesting manual registry connection...")
        client = ServiceRegistryClient("http://127.0.0.1:8080")
        
        # Test health check
        is_healthy = client.check_health()
        print(f"Registry health: {is_healthy}")
        
        # Discover all services
        services = client.discover_services()
        print(f"Manually discovered {len(services)} services:")
        
        for i, service in enumerate(services):
            print(f"  {i+1}. ID: {service.id}, Type: {service.type}, Host: {service.host}, Port: {service.port}")
        
        return services
    
    except Exception as e:
        print(f"Error in manual registry connection: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("Testing registry connection and service discovery...")
    
    # Test manual connection first
    manual_services = test_registry_connection_manually()
    
    print("\n" + "="*60)
    
    # Test the discover_services_node
    result = test_discover_services_with_actual_registry()
    
    if result and result['discovered_services']:
        print("\n✓ SUCCESS: Services were discovered by the node!")
    else:
        print("\n✗ FAILURE: No services discovered by the node")
        
    if manual_services:
        print(f"\n✓ Manual connection worked and found {len(manual_services)} services")
    else:
        print("\n✗ Manual connection didn't find any services")
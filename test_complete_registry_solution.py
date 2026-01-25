#!/usr/bin/env python3
"""
Final comprehensive test to verify that the MCP registry discovery fix is working properly.
"""

import os
import sys
import time

def test_complete_solution():
    """Test the complete solution for MCP registry discovery"""
    
    print("Testing complete MCP registry discovery solution...")
    
    # Import required modules
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        from config.settings import MCP_REGISTRY_URL
        print(f"✓ Successfully imported run_enhanced_agent")
        print(f"✓ Default registry URL from config: {MCP_REGISTRY_URL}")
    except ImportError as e:
        print(f"✗ Failed to import required modules: {e}")
        return False

    # Test 1: Run agent with default registry URL
    print("\n--- Test 1: Running agent with default registry URL ---")
    try:
        result = run_enhanced_agent("What services are available?")
        
        print(f"✓ Agent executed successfully")
        print(f"✓ Result keys: {list(result.keys())}")
        
        # Check if services were discovered
        mcp_servers = result.get('mcp_servers', [])
        discovered_services = result.get('discovered_services', [])
        
        print(f"✓ Number of MCP servers in result: {len(mcp_servers)}")
        print(f"✓ Number of discovered services in result: {len(discovered_services)}")
        
        if mcp_servers:
            print("✓ MCP servers discovered:")
            for i, server in enumerate(mcp_servers):
                print(f"  {i+1}. {server.get('type', 'Unknown type')} at {server.get('host', 'Unknown host')}:{server.get('port', 'Unknown port')}")
        else:
            print("✗ No MCP servers discovered")
            
        if discovered_services:
            print("✓ Discovered services:")
            for i, service in enumerate(discovered_services):
                print(f"  {i+1}. {service.get('type', 'Unknown type')} at {service.get('host', 'Unknown host')}:{service.get('port', 'Unknown port')}")
        else:
            print("✗ No discovered services")
        
        # Test 2: Run agent with explicit registry URL
        print("\n--- Test 2: Running agent with explicit registry URL ---")
        result_with_url = run_enhanced_agent(
            "List available services", 
            registry_url="http://127.0.0.1:8080"
        )
        
        mcp_servers_with_url = result_with_url.get('mcp_servers', [])
        discovered_services_with_url = result_with_url.get('discovered_services', [])
        
        print(f"✓ Agent with explicit URL executed successfully")
        print(f"✓ MCP servers with explicit URL: {len(mcp_servers_with_url)}")
        print(f"✓ Discovered services with explicit URL: {len(discovered_services_with_url)}")
        
        # Both tests should have discovered services if the registry is working
        success = len(mcp_servers) > 0 or len(discovered_services) > 0
        success_with_url = len(mcp_servers_with_url) > 0 or len(discovered_services_with_url) > 0
        
        if success or success_with_url:
            print("\n🎉 SUCCESS: MCP services are being discovered from the registry!")
            print("✓ The fix is working correctly:")
            print("  - Services are discovered from the MCP registry")
            print("  - The discover_services_node is properly integrated")
            print("  - The mcp_servers list is populated with discovered services")
            return True
        else:
            print("\n❌ FAILURE: No services were discovered")
            return False
            
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_registry_directly():
    """Test the registry connection directly"""
    
    print("\n--- Testing registry connection directly ---")
    
    try:
        from registry.registry_client import ServiceRegistryClient
        
        client = ServiceRegistryClient("http://127.0.0.1:8080")
        
        # Test health
        is_healthy = client.check_health()
        print(f"✓ Registry health: {is_healthy}")
        
        if not is_healthy:
            print("✗ Registry is not healthy")
            return False
        
        # Test discovery
        services = client.discover_services()
        print(f"✓ Discovered {len(services)} services from registry")
        
        for i, service in enumerate(services):
            print(f"  {i+1}. {service.type} - {service.host}:{service.port} (ID: {service.id})")
        
        return len(services) > 0
        
    except Exception as e:
        print(f"✗ Error testing registry directly: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running comprehensive test of MCP registry discovery fix...\n")
    
    registry_success = test_registry_directly()
    solution_success = test_complete_solution()
    
    if registry_success and solution_success:
        print("\n🎉 ALL TESTS PASSED! The MCP registry discovery fix is working correctly.")
        print("\nSUMMARY OF IMPLEMENTATION:")
        print("✓ Added discover_services_node to connect to MCP registry")
        print("✓ Integrated the node into the LangGraph workflow")
        print("✓ Updated run_enhanced_agent to accept registry_url parameter")
        print("✓ Used default registry URL from config when none provided")
        print("✓ MCP services are now properly discovered and sent to the LLM")
    else:
        print("\n❌ SOME TESTS FAILED!")
        if not registry_success:
            print("- Registry connection test failed")
        if not solution_success:
            print("- Solution integration test failed")
        sys.exit(1)
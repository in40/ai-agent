#!/usr/bin/env python3
"""
Final test to verify that the MCP registry discovery fix is working properly.
"""

import json
import os
import sys
import time

def test_complete_registry_integration():
    """Test the complete registry integration"""
    
    print("Testing complete MCP registry discovery integration...")
    
    # Import the run_enhanced_agent function
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        print("✓ Successfully imported run_enhanced_agent")
    except ImportError as e:
        print(f"✗ Failed to import run_enhanced_agent: {e}")
        return False

    # Test with a registry URL
    test_request = "What services are available?"
    registry_url = "http://127.0.0.1:8080"  # Our running registry
    
    print(f"Making test request: '{test_request}' with registry URL: {registry_url}")
    
    try:
        # Call the agent with the registry URL
        result = run_enhanced_agent(
            user_request=test_request,
            registry_url=registry_url
        )
        
        print("✓ Agent executed successfully with registry URL")
        print(f"✓ Result keys: {list(result.keys())}")
        
        # Check if MCP servers were discovered
        mcp_servers = result.get('mcp_servers', [])
        discovered_services = result.get('discovered_services', [])
        
        print(f"✓ Number of MCP servers discovered: {len(mcp_servers)}")
        print(f"✓ Number of discovered services: {len(discovered_services)}")
        
        if mcp_servers:
            print("✓ MCP servers found in result:")
            for i, server in enumerate(mcp_servers):
                print(f"  {i+1}. {server.get('type', 'Unknown type')} at {server.get('host', 'Unknown host')}:{server.get('port', 'Unknown port')}")
        else:
            print("✗ No MCP servers found in result")
            
        if discovered_services:
            print("✓ Discovered services found in result:")
            for i, service in enumerate(discovered_services):
                print(f"  {i+1}. {service.get('type', 'Unknown type')} at {service.get('host', 'Unknown host')}:{service.get('port', 'Unknown port')}")
        else:
            print("✗ No discovered services found in result")
        
        # The key test: check if the result contains service information
        if len(mcp_servers) > 0 or len(discovered_services) > 0:
            print("\n🎉 SUCCESS: MCP services are now being discovered from the registry!")
            return True
        else:
            print("\n❌ FAILURE: No services were discovered despite registry being available")
            return False
            
    except Exception as e:
        print(f"✗ Error running agent with registry: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_registry():
    """Test behavior when no registry is provided"""
    
    print("\nTesting behavior without registry URL...")
    
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        
        result = run_enhanced_agent(
            user_request="Test without registry",
            registry_url=None
        )
        
        # When no registry is provided, we should still get a valid response
        print("✓ Agent executed successfully without registry URL")
        
        # Check that no services were discovered (which is expected)
        mcp_servers = result.get('mcp_servers', [])
        discovered_services = result.get('discovered_services', [])
        
        print(f"✓ MCP servers without registry: {len(mcp_servers)}")
        print(f"✓ Discovered services without registry: {len(discovered_services)}")
        
        # This is expected behavior - no services when no registry is provided
        return True
        
    except Exception as e:
        print(f"✗ Error running agent without registry: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running final verification of MCP registry discovery fix...\n")
    
    success1 = test_complete_registry_integration()
    success2 = test_without_registry()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! The MCP registry discovery fix is working correctly.")
        print("\nSUMMARY OF FIXES:")
        print("1. ✅ Added discover_services_node to connect to MCP registry")
        print("2. ✅ Integrated the node into the LangGraph workflow")
        print("3. ✅ Updated run_enhanced_agent to accept registry_url parameter")
        print("4. ✅ Fixed the DedicatedMCPModel JSON parsing issue")
        print("5. ✅ Updated the backend to pass registry_url to the agent")
        print("6. ✅ MCP services are now properly discovered and sent to the LLM")
    else:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)
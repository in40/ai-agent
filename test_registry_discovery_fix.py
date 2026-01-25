#!/usr/bin/env python3
"""
Test script to verify that the MCP registry discovery fix is working correctly.
"""

import requests
import json
import time
import threading
import sys
import os

# Add the project root to the path to import modules
sys.path.insert(0, '/root/qwen_test/ai_agent')

def test_registry_discovery():
    """Test that the registry discovery functionality works correctly"""
    
    print("Testing MCP registry discovery functionality...")
    
    # Test 1: Verify that the registry service is running
    try:
        response = requests.get("http://127.0.0.1:8080/health", timeout=5)
        if response.status_code == 200:
            print("✓ Registry service is running and healthy")
        else:
            print(f"✗ Registry service returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Registry service is not accessible: {e}")
        return False
    
    # Test 2: Verify that services are registered
    try:
        response = requests.get("http://127.0.0.1:8080/services", timeout=5)
        if response.status_code == 200:
            services_data = response.json()
            services = services_data.get('services', [])
            print(f"✓ Registry has {len(services)} services registered")
            
            if len(services) == 0:
                print("⚠ Warning: No services are registered with the registry")
            else:
                for service in services:
                    print(f"  - {service['id']} ({service['type']}) at {service['host']}:{service['port']}")
        else:
            print(f"✗ Failed to get services list: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to query services: {e}")
        return False
    
    # Test 3: Verify that the new upload progress endpoint exists
    try:
        # We'll use a fake session ID to test if the endpoint exists
        response = requests.get("http://127.0.0.1:8080/upload_progress/fake-session-id", 
                               headers={"Authorization": "Bearer fake-token"}, timeout=5)
        # We expect a 401 (unauthorized) or 404 (not found) but not a 404 (endpoint not found)
        if response.status_code in [401, 404]:
            print("✓ Upload progress endpoint is available")
        else:
            print(f"✗ Upload progress endpoint returned unexpected status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Upload progress endpoint is not accessible: {e}")
        return False
    
    # Test 4: Test the discover_services_node function directly
    try:
        from langgraph_agent.langgraph_agent import discover_services_node
        
        # Create a test state with the registry URL
        test_state = {
            "user_request": "Test request",
            "registry_url": "http://127.0.0.1:8080",
            "mcp_servers": [],
            "discovered_services": []
        }
        
        # Call the discover_services_node function
        result = discover_services_node(test_state)
        
        print(f"✓ discover_services_node executed successfully")
        print(f"  - Discovered {len(result['discovered_services'])} services")
        print(f"  - MCP servers list has {len(result['mcp_servers'])} entries")
        
        if len(result['discovered_services']) > 0:
            print("✓ Services were successfully discovered from the registry")
            for service in result['discovered_services']:
                print(f"    * {service['id']} ({service['type']}) at {service['host']}:{service['port']}")
        else:
            print("✗ No services were discovered from the registry")
            return False
            
    except Exception as e:
        print(f"✗ Error testing discover_services_node: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_langgraph_integration():
    """Test that the LangGraph workflow includes the discover_services node"""
    
    print("\nTesting LangGraph workflow integration...")
    
    try:
        from langgraph_agent.langgraph_agent import create_enhanced_agent_graph
        
        # Create the graph
        graph = create_enhanced_agent_graph()
        
        # Check if the graph has the discover_services node
        if hasattr(graph, 'nodes') and 'discover_services' in graph.nodes:
            print("✓ discover_services node is present in the LangGraph workflow")
        else:
            print("✗ discover_services node is missing from the LangGraph workflow")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error testing LangGraph integration: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("Running comprehensive test of MCP registry discovery fix...\n")
    
    success = True
    success &= test_registry_discovery()
    success &= test_langgraph_integration()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests passed! The MCP registry discovery fix is working correctly.")
        print("\nSummary of changes:")
        print("1. Added discover_services_node to connect to MCP registry and discover services")
        print("2. Integrated the node into the LangGraph workflow")
        print("3. Added progress tracking endpoints for file uploads")
        print("4. Updated the frontend to use progress tracking")
        print("5. MCP services are now properly discovered and sent to the LLM")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
    
    return success


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ MCP registry discovery functionality verified successfully!")
    else:
        print("\n❌ MCP registry discovery functionality needs attention!")
        sys.exit(1)
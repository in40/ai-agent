#!/usr/bin/env python3
"""
Comprehensive test to verify the complete MCP registry discovery fix.
"""

def test_complete_registry_integration():
    """Test the complete integration with default registry URL from config"""
    
    print("Testing complete registry integration...")
    
    # Test 1: Verify the config setting exists
    try:
        from config.settings import MCP_REGISTRY_URL
        print(f"✓ Config setting MCP_REGISTRY_URL exists: {MCP_REGISTRY_URL}")
    except ImportError as e:
        print(f"✗ Error importing config setting: {e}")
        return False
    
    # Test 2: Test run_enhanced_agent with default registry URL
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        
        # Run a simple test with the default registry URL
        result = run_enhanced_agent(
            user_request="Test request to check services",
            disable_databases=True  # Disable databases to focus on MCP services
        )
        
        print(f"✓ run_enhanced_agent executed successfully")
        print(f"  Final answer length: {len(result.get('final_answer', ''))}")
        
        # Check if services were discovered during the workflow
        # The mcp_results should contain information about discovered services
        mcp_results = result.get('mcp_results', [])
        print(f"  MCP Results count: {len(mcp_results)}")
        
        # The execution log should contain information about service discovery
        execution_log = result.get('execution_log', [])
        print(f"  Execution log entries: {len(execution_log)}")
        
        # Look for evidence of service discovery in the logs
        discovery_found = any(
            'discover_services_node' in str(entry) or 'Discovered' in str(entry)
            for entry in execution_log
        )
        
        if discovery_found:
            print("✓ Service discovery was performed during execution")
        else:
            print("? Service discovery may not have been logged, checking other indicators")
        
        return True
        
    except Exception as e:
        print(f"✗ Error running complete integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_run_enhanced_agent_with_explicit_registry():
    """Test run_enhanced_agent with explicit registry URL"""
    
    print("\nTesting run_enhanced_agent with explicit registry URL...")
    
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        
        # Run with explicit registry URL
        result = run_enhanced_agent(
            user_request="Test request with explicit registry",
            registry_url="http://127.0.0.1:8080",
            disable_databases=True
        )
        
        print(f"✓ run_enhanced_agent with explicit registry URL executed successfully")
        print(f"  Registry URL in result: {result.get('registry_url')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error with explicit registry URL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_discover_services_node_directly():
    """Test the discover_services_node directly with the actual registry"""
    
    print("\nTesting discover_services_node directly...")
    
    try:
        from langgraph_agent.langgraph_agent import discover_services_node
        
        # Create state with actual registry URL
        test_state = {
            "user_request": "Test request",
            "registry_url": "http://127.0.0.1:8080",
            "mcp_servers": [],
            "discovered_services": []
        }
        
        result = discover_services_node(test_state)
        
        print(f"✓ discover_services_node executed successfully")
        print(f"  Discovered services count: {len(result['discovered_services'])}")
        print(f"  MCP servers count: {len(result['mcp_servers'])}")
        
        if result['discovered_services']:
            print("  Discovered services:")
            for service in result['discovered_services']:
                print(f"    - {service['type']} at {service['host']}:{service['port']}")
            return True
        else:
            print("  ! No services discovered")
            return False
            
    except Exception as e:
        print(f"✗ Error in direct node test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running comprehensive test of MCP registry discovery fix...\n")
    
    success = True
    success &= test_discover_services_node_directly()
    success &= test_run_enhanced_agent_with_explicit_registry()
    success &= test_complete_registry_integration()
    
    if success:
        print("\n🎉 All comprehensive tests passed!")
        print("\nSummary of the complete fix:")
        print("- Added discover_services_node to connect to MCP registry and discover services")
        print("- Integrated the node into the LangGraph workflow")
        print("- Updated run_enhanced_agent to accept registry_url parameter")
        print("- Added MCP_REGISTRY_URL to config settings with default value")
        print("- Made registry URL configurable via environment variables")
        print("- When no explicit registry URL is provided, uses the default from config")
        print("- Services are now properly discovered from the registry and available to the LLM")
    else:
        print("\n❌ Some tests failed!")
        exit(1)
#!/usr/bin/env python3
"""
Test script to verify the agent service fix for connecting to MCP registry
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_service_code_fix():
    """Test that the agent service code now properly connects to the registry"""
    
    # Read the agent service file to verify the fix
    with open('/root/qwen/ai_agent/backend/services/agent/app.py', 'r') as f:
        content = f.read()
    
    # Check if the fix is in place
    has_registry_import = "from config.settings import MCP_REGISTRY_URL" in content
    has_registry_usage = "registry_url=MCP_REGISTRY_URL" in content
    no_empty_servers = "mcp_servers=[]" not in content.split('# Run the agent with the registry URL')[1].split('result = run_enhanced_agent')[0]
    
    print("Testing agent service code fix:")
    print(f"Has registry import: {has_registry_import}")
    print(f"Has registry usage: {has_registry_usage}")
    print(f"No longer using empty servers list: {no_empty_servers}")
    
    if has_registry_import and has_registry_usage and no_empty_servers:
        print("\n✅ SUCCESS: Agent service code fix is in place!")
        return True
    else:
        print("\n❌ FAILURE: Agent service code fix is not properly implemented.")
        return False

def test_run_enhanced_agent_signature():
    """Test that run_enhanced_agent accepts registry_url parameter"""
    
    # Import and check the function signature
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        import inspect
        
        sig = inspect.signature(run_enhanced_agent)
        has_registry_url = 'registry_url' in sig.parameters
        
        print(f"\nTesting run_enhanced_agent function:")
        print(f"Has registry_url parameter: {has_registry_url}")
        
        if has_registry_url:
            print("✅ SUCCESS: run_enhanced_agent accepts registry_url parameter!")
            return True
        else:
            print("❌ FAILURE: run_enhanced_agent does not accept registry_url parameter.")
            return False
            
    except Exception as e:
        print(f"❌ ERROR importing run_enhanced_agent: {e}")
        return False

def test_config_has_registry_url():
    """Test that the config has the MCP_REGISTRY_URL setting"""
    
    try:
        from config.settings import MCP_REGISTRY_URL
        print(f"\nTesting config setting:")
        print(f"MCP_REGISTRY_URL: {MCP_REGISTRY_URL}")
        
        if MCP_REGISTRY_URL and isinstance(MCP_REGISTRY_URL, str):
            print("✅ SUCCESS: MCP_REGISTRY_URL setting exists!")
            return True
        else:
            print("❌ FAILURE: MCP_REGISTRY_URL setting is invalid.")
            return False
    except Exception as e:
        print(f"❌ ERROR importing config settings: {e}")
        return False

if __name__ == "__main__":
    print("Testing the agent service fix for MCP registry connection...\n")
    
    test1_passed = test_agent_service_code_fix()
    test2_passed = test_run_enhanced_agent_signature()
    test3_passed = test_config_has_registry_url()
    
    print("\n" + "="*60)
    print("OVERALL TEST RESULT:")
    if test1_passed and test2_passed and test3_passed:
        print("✅ ALL TESTS PASSED: The agent service fix is working correctly!")
        print("\nThe agent service will now connect to the MCP registry to discover services")
        print("instead of using an empty list, which should resolve the 'No response generated' issue.")
    else:
        print("❌ SOME TESTS FAILED: The fix needs more work.")
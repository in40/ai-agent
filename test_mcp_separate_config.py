#!/usr/bin/env python3
"""
Test script to verify that the MCP-capable model can use separate LLM configuration.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mcp_model_with_separate_config():
    """Test that the MCP-capable model can use separate LLM configuration"""
    print("Testing MCP-capable model with separate configuration...")
    
    # Set environment variables to simulate separate MCP configuration
    os.environ['MCP_LLM_PROVIDER'] = 'OpenAI'
    os.environ['MCP_LLM_MODEL'] = 'gpt-4o-mini'
    os.environ['MCP_LLM_HOSTNAME'] = 'api.openai.com'
    os.environ['MCP_LLM_PORT'] = '443'
    os.environ['MCP_LLM_API_PATH'] = '/v1'
    
    # Also set the prompt LLM config to different values to ensure the MCP config is used
    os.environ['PROMPT_LLM_PROVIDER'] = 'LM Studio'
    os.environ['PROMPT_LLM_MODEL'] = 'test-model'
    os.environ['PROMPT_LLM_HOSTNAME'] = 'localhost'
    os.environ['PROMPT_LLM_PORT'] = '1234'
    os.environ['PROMPT_LLM_API_PATH'] = '/v1'
    
    try:
        from models.mcp_capable_model import MCPCapableModel
        from config.settings import (
            MCP_LLM_PROVIDER, MCP_LLM_MODEL, MCP_LLM_HOSTNAME, 
            MCP_LLM_PORT, MCP_LLM_API_PATH,
            PROMPT_LLM_PROVIDER, PROMPT_LLM_MODEL, PROMPT_LLM_HOSTNAME,
            PROMPT_LLM_PORT, PROMPT_LLM_API_PATH
        )
        
        print(f"MCP Provider: {MCP_LLM_PROVIDER}")
        print(f"MCP Model: {MCP_LLM_MODEL}")
        print(f"Prompt Provider: {PROMPT_LLM_PROVIDER}")
        print(f"Prompt Model: {PROMPT_LLM_MODEL}")
        
        # Create an instance of the MCP-capable model
        model = MCPCapableModel()
        
        print("✓ MCP-capable model initialized successfully with separate configuration")
        
        # Clean up environment variables
        del os.environ['MCP_LLM_PROVIDER']
        del os.environ['MCP_LLM_MODEL']
        del os.environ['MCP_LLM_HOSTNAME']
        del os.environ['MCP_LLM_PORT']
        del os.environ['MCP_LLM_API_PATH']
        del os.environ['PROMPT_LLM_PROVIDER']
        del os.environ['PROMPT_LLM_MODEL']
        del os.environ['PROMPT_LLM_HOSTNAME']
        del os.environ['PROMPT_LLM_PORT']
        del os.environ['PROMPT_LLM_API_PATH']
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing MCP-capable model with separate configuration: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up environment variables in case of error
        if 'MCP_LLM_PROVIDER' in os.environ:
            del os.environ['MCP_LLM_PROVIDER']
        if 'MCP_LLM_MODEL' in os.environ:
            del os.environ['MCP_LLM_MODEL']
        if 'MCP_LLM_HOSTNAME' in os.environ:
            del os.environ['MCP_LLM_HOSTNAME']
        if 'MCP_LLM_PORT' in os.environ:
            del os.environ['MCP_LLM_PORT']
        if 'MCP_LLM_API_PATH' in os.environ:
            del os.environ['MCP_LLM_API_PATH']
        if 'PROMPT_LLM_PROVIDER' in os.environ:
            del os.environ['PROMPT_LLM_PROVIDER']
        if 'PROMPT_LLM_MODEL' in os.environ:
            del os.environ['PROMPT_LLM_MODEL']
        if 'PROMPT_LLM_HOSTNAME' in os.environ:
            del os.environ['PROMPT_LLM_HOSTNAME']
        if 'PROMPT_LLM_PORT' in os.environ:
            del os.environ['PROMPT_LLM_PORT']
        if 'PROMPT_LLM_API_PATH' in os.environ:
            del os.environ['PROMPT_LLM_API_PATH']
        
        return False


def test_mcp_model_with_fallback_config():
    """Test that the MCP-capable model falls back to prompt config when MCP config is empty"""
    print("\nTesting MCP-capable model with fallback to prompt configuration...")
    
    # Clear MCP configuration to test fallback
    if 'MCP_LLM_PROVIDER' in os.environ:
        del os.environ['MCP_LLM_PROVIDER']
    if 'MCP_LLM_MODEL' in os.environ:
        del os.environ['MCP_LLM_MODEL']
    if 'MCP_LLM_HOSTNAME' in os.environ:
        del os.environ['MCP_LLM_HOSTNAME']
    if 'MCP_LLM_PORT' in os.environ:
        del os.environ['MCP_LLM_PORT']
    if 'MCP_LLM_API_PATH' in os.environ:
        del os.environ['MCP_LLM_API_PATH']
    
    # Set prompt config
    os.environ['PROMPT_LLM_PROVIDER'] = 'OpenAI'
    os.environ['PROMPT_LLM_MODEL'] = 'gpt-4o-mini'
    os.environ['PROMPT_LLM_HOSTNAME'] = 'api.openai.com'
    os.environ['PROMPT_LLM_PORT'] = '443'
    os.environ['PROMPT_LLM_API_PATH'] = '/v1'
    
    try:
        from models.mcp_capable_model import MCPCapableModel
        from config.settings import (
            MCP_LLM_PROVIDER, MCP_LLM_MODEL, MCP_LLM_HOSTNAME, 
            MCP_LLM_PORT, MCP_LLM_API_PATH,
            PROMPT_LLM_PROVIDER, PROMPT_LLM_MODEL, PROMPT_LLM_HOSTNAME,
            PROMPT_LLM_PORT, PROMPT_LLM_API_PATH
        )
        
        print(f"MCP Provider: '{MCP_LLM_PROVIDER}' (should be empty string)")
        print(f"MCP Model: '{MCP_LLM_MODEL}' (should be empty string)")
        print(f"Prompt Provider: {PROMPT_LLM_PROVIDER}")
        print(f"Prompt Model: {PROMPT_LLM_MODEL}")
        
        # Create an instance of the MCP-capable model
        model = MCPCapableModel()
        
        print("✓ MCP-capable model initialized successfully with fallback configuration")
        
        # Clean up environment variables
        del os.environ['PROMPT_LLM_PROVIDER']
        del os.environ['PROMPT_LLM_MODEL']
        del os.environ['PROMPT_LLM_HOSTNAME']
        del os.environ['PROMPT_LLM_PORT']
        del os.environ['PROMPT_LLM_API_PATH']
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing MCP-capable model with fallback configuration: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up environment variables in case of error
        if 'PROMPT_LLM_PROVIDER' in os.environ:
            del os.environ['PROMPT_LLM_PROVIDER']
        if 'PROMPT_LLM_MODEL' in os.environ:
            del os.environ['PROMPT_LLM_MODEL']
        if 'PROMPT_LLM_HOSTNAME' in os.environ:
            del os.environ['PROMPT_LLM_HOSTNAME']
        if 'PROMPT_LLM_PORT' in os.environ:
            del os.environ['PROMPT_LLM_PORT']
        if 'PROMPT_LLM_API_PATH' in os.environ:
            del os.environ['PROMPT_LLM_API_PATH']
        
        return False


if __name__ == "__main__":
    print("Running MCP Model Separate Configuration Tests...\n")
    
    success1 = test_mcp_model_with_separate_config()
    success2 = test_mcp_model_with_fallback_config()
    
    if success1 and success2:
        print("\n🎉 All MCP model separate configuration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some MCP model separate configuration tests failed!")
        sys.exit(1)
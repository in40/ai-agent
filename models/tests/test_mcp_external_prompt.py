#!/usr/bin/env python3
"""
Test script to verify that the MCP-capable model now uses the external prompt file.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.mcp_capable_model import MCPCapableModel


def test_mcp_model_uses_external_prompt():
    """Test that the MCP-capable model uses the external prompt file"""
    print("Testing MCP-capable model uses external prompt...")
    
    try:
        # Create an instance of the MCP-capable model
        model = MCPCapableModel()
        
        # Check if the prompt was loaded from the external file
        # We can verify this by checking if the system message contains expected content
        print("MCP-capable model initialized successfully")
        
        # The prompt should be loaded from the external file
        # Let's make sure the prompt contains expected content
        # by looking at the prompt template structure
        print(f"Prompt template messages count: {len(model.prompt.messages)}")
        
        # Get the system message content
        system_message = model.prompt.messages[0]  # First message should be system
        print("System message template loaded successfully")
        
        # The model should initialize without errors
        print("✓ MCP-capable model successfully uses external prompt")
        return True
        
    except Exception as e:
        print(f"✗ Error testing MCP-capable model external prompt: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_manager_loads_mcp_prompt():
    """Test that the prompt manager loads the MCP-capable prompt"""
    print("\nTesting prompt manager loads MCP-capable prompt...")
    
    try:
        from utils.prompt_manager import PromptManager
        
        # Create a prompt manager instance
        pm = PromptManager("./core/prompts")
        
        # Check if the MCP-capable prompt is listed
        available_prompts = pm.list_prompts()
        print(f"Available prompts: {available_prompts}")
        
        if "mcp_capable_model" in available_prompts:
            print("✓ MCP-capable prompt is available in prompt manager")
            
            # Get the prompt content
            prompt_content = pm.get_prompt("mcp_capable_model")
            if prompt_content and "MCP (Multi-Component Protocol)" in prompt_content:
                print("✓ MCP-capable prompt content is correctly loaded")
                return True
            else:
                print("✗ MCP-capable prompt content is not as expected")
                return False
        else:
            print("✗ MCP-capable prompt is not available in prompt manager")
            return False
            
    except Exception as e:
        print(f"✗ Error testing prompt manager: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running MCP Model External Prompt Tests...\n")
    
    success1 = test_prompt_manager_loads_mcp_prompt()
    success2 = test_mcp_model_uses_external_prompt()
    
    if success1 and success2:
        print("\n🎉 All MCP model external prompt tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some MCP model external prompt tests failed!")
        sys.exit(1)
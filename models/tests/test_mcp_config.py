#!/usr/bin/env python3
"""
Test script to verify the MCP configuration sections are properly added
"""

import ast
import sys

def test_mcp_configurations():
    """Test that MCP configuration variables are properly referenced in the .env content generation."""
    
    # Read the setup_config.py file
    with open('/root/qwen_test/ai_agent/setup_config.py', 'r') as f:
        content = f.read()
    
    # Look for MCP-related variable references in the f-string that generates env_content
    mcp_variables = [
        'mcp_sql_llm_provider',
        'mcp_sql_llm_model',
        'mcp_sql_llm_hostname',
        'mcp_sql_llm_port',
        'mcp_sql_llm_api_path',
        'mcp_response_llm_provider',
        'mcp_response_llm_model',
        'mcp_response_llm_hostname',
        'mcp_response_llm_port',
        'mcp_response_llm_api_path',
        'mcp_prompt_llm_provider',
        'mcp_prompt_llm_model',
        'mcp_prompt_llm_hostname',
        'mcp_prompt_llm_port',
        'mcp_prompt_llm_api_path',
        'configure_mcp_models_value'
    ]
    
    print("Testing MCP configuration variables in env content generation:")
    print("-" * 60)
    
    # Check if all MCP variables are present in the content
    missing_vars = []
    for var in mcp_variables:
        if f'{{{var}}}' not in content:
            missing_vars.append(var)
        status = "MISSING" if f'{{{var}}}' not in content else "FOUND"
        print(f"Variable {var}: [{status}]")
    
    print("-" * 60)
    
    if missing_vars:
        print(f"ERROR: Missing MCP variables in env content: {missing_vars}")
        return False
    else:
        print("SUCCESS: All MCP configuration variables are properly referenced in env content generation")
        return True

def test_mcp_sections_exist():
    """Test that MCP configuration sections exist in the setup flow."""
    
    with open('/root/qwen_test/ai_agent/setup_config.py', 'r') as f:
        content = f.read()
    
    # Look for MCP-related sections in the setup flow
    mcp_sections = [
        "MCP Capable Model Configuration:",
        "configure_mcp_models_input = get_user_input",
        "mcp_sql_llm_provider = get_user_input",
        "mcp_response_llm_provider = get_user_input",
        "mcp_prompt_llm_provider = get_user_input",
        "MCP_ENABLED={mcp_enabled}",
        "CONFIGURE_MCP_MODELS={configure_mcp_models_value}"
    ]
    
    print("\nTesting MCP configuration sections in setup flow:")
    print("-" * 60)
    
    missing_sections = []
    for section in mcp_sections:
        if section not in content:
            missing_sections.append(section)
        status = "MISSING" if section not in content else "FOUND"
        print(f"Section '{section[:50]}...': [{status}]")
    
    print("-" * 60)
    
    if missing_sections:
        print(f"ERROR: Missing MCP sections in setup flow: {missing_sections}")
        return False
    else:
        print("SUCCESS: All MCP configuration sections exist in setup flow")
        return True

if __name__ == "__main__":
    success1 = test_mcp_configurations()
    success2 = test_mcp_sections_exist()
    
    print(f"\nOverall test result: {'PASSED' if success1 and success2 else 'FAILED'}")
    sys.exit(0 if success1 and success2 else 1)
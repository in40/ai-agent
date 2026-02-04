#!/usr/bin/env python3
"""
Debug script to see what's happening with the template variable validation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import re

def debug_template_validation():
    # Read the original prompt file
    with open('./core/prompts/mcp_capable_model.txt', 'r', encoding='utf-8') as f:
        system_prompt_template = f.read()
    
    print("Original system prompt template:")
    print(repr(system_prompt_template[:500]))  # Print first 500 chars
    print("\n..." if len(system_prompt_template) > 500 else "")
    print()
    
    # Simulate the replacements that happen in __init__
    basic_system_prompt = system_prompt_template
    basic_system_prompt = basic_system_prompt.replace('{user_request}', '')
    basic_system_prompt = basic_system_prompt.replace('{mcp_services_json}', '{{}}')  # Escaped to avoid template issues
    basic_system_prompt = basic_system_prompt.replace('{previous_tool_calls}', '[{{}}]')
    basic_system_prompt = basic_system_prompt.replace('{previous_signals}', '[{{}}]')
    basic_system_prompt = basic_system_prompt.replace('{informational_content}', '')
    
    print("After replacements:")
    print(repr(basic_system_prompt[:500]))
    print("\n..." if len(basic_system_prompt) > 500 else "")
    print()
    
    # Now test the validation logic
    print("Testing validation logic...")
    
    # Use the new validation approach
    pattern = r'(?<!\{)\{(\s*)\}(?!\})'  # Matches {} or { } but not {{ or }}
    matches = re.findall(pattern, basic_system_prompt)
    
    print(f"Found {len(matches)} potential empty template variables")
    if matches:
        print(f"Matches: {matches}")
        # Find and report the first empty template variable
        match = re.search(pattern, basic_system_prompt)
        if match:
            empty_var = '{' + match.group(1) + '}'
            print(f"Empty template variable found: {empty_var}")
            print(f"Full error message would be: Found empty template variable in system prompt: {empty_var}")
    
    # Also test the old approach to see what it would find
    print("\nTesting old approach...")
    all_vars = re.findall(r'\{([^}]*)\}', basic_system_prompt)
    print(f"All variables found with old approach: {all_vars}")
    empty_vars = [var for var in all_vars if var.strip() == '']
    print(f"Empty variables with old approach: {empty_vars}")

if __name__ == "__main__":
    debug_template_validation()
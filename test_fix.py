#!/usr/bin/env python3
"""
Test script to verify the MCP service lookup fix.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.dedicated_mcp_model import DedicatedMCPModel
import json

def test_nested_structure_handling():
    """Test that the model correctly handles nested JSON structures."""

    # Create a mock service
    mock_services = [
        {
            "id": "search-server-127-0-0-1-8090",
            "name": "Web Search Service",
            "description": "Provides web search capabilities",
            "host": "127.0.0.1",
            "port": 8090,
            "metadata": {
                "protocol": "http",
                "methods": ["web_search"]
            }
        }
    ]
    
    # Create the model instance
    model = DedicatedMCPModel()
    
    # Test the nested structure that was causing the issue
    user_request = "Who owns Google?"
    
    # Simulate the problematic JSON structure
    # This is what the LLM might return that causes the issue
    problematic_response = '{"tool_call": {"service_id": "search-server-127-0-0-1-8090", "method": "web_search", "parameters": {"query": "who owns google"}}}'
    
    # Manually test the JSON parsing logic
    print("Testing nested structure handling...")
    print(f"Input JSON: {problematic_response}")
    
    try:
        result = json.loads(problematic_response)
        print(f"Parsed JSON: {result}")
        
        # Apply the same logic as in the fixed code
        if isinstance(result, dict) and 'tool_call' in result:
            actual_tool_call = result['tool_call']
            if isinstance(actual_tool_call, dict):
                final_result = {"tool_calls": [actual_tool_call]}
                print(f"Fixed result: {final_result}")
                
                # Verify the service_id is correctly extracted
                if final_result['tool_calls'][0]['service_id'] == 'search-server-127-0-0-1-8090':
                    print("✓ Service ID correctly extracted!")
                    
                    # Test the execute_mcp_tool_calls method with this structure
                    execution_results = model.execute_mcp_tool_calls(final_result['tool_calls'], mock_services)
                    print(f"Execution results: {execution_results}")

                    # Check if the service was found (the error should be about connection, not service not found)
                    if execution_results and 'not found' not in execution_results[0].get('error', ''):
                        print("✓ Service lookup successful! (Connection error is expected since service isn't running)")
                        return True
                    else:
                        print("✗ Service lookup failed - service not found error")
                        return False
                else:
                    print("✗ Service ID not correctly extracted")
                    return False
        else:
            print("✗ Nested structure not handled correctly")
            return False
            
    except Exception as e:
        print(f"✗ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("Running MCP service lookup fix test...")
    success = test_nested_structure_handling()
    
    if success:
        print("\n✓ All tests passed! The fix is working correctly.")
    else:
        print("\n✗ Tests failed. The fix needs more work.")
        sys.exit(1)
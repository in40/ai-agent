#!/usr/bin/env python3
"""
Test script to verify the fix for the original issue where parameters
are passed directly in the tool call instead of nested under 'parameters'.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.dedicated_mcp_model import DedicatedMCPModel
import json

def test_original_issue_structure():
    """Test that the model correctly handles the original issue structure."""

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

    # Test the original problematic structure from the error log
    # This is the structure that was causing the issue:
    original_tool_call = {
        "service": "search-server-127-0-0-1-8090",
        "query": "is it currently snowing in Moscow"
    }

    print("Testing original issue structure...")
    print(f"Input tool call: {original_tool_call}")

    # Test the execute_mcp_tool_calls method with this structure
    execution_results = model.execute_mcp_tool_calls([original_tool_call], mock_services)
    print(f"Execution results: {execution_results}")

    # Check if the parameters were correctly extracted
    if execution_results:
        result = execution_results[0]
        if 'parameters' in result and 'query' in result['parameters']:
            if result['parameters']['query'] == "is it currently snowing in Moscow":
                print("✓ Parameters correctly extracted from top-level fields!")
                
                # The connection error is expected since the service isn't running
                if 'Connection refused' in result.get('error', ''):
                    print("✓ Service lookup successful! (Connection error is expected since service isn't running)")
                    return True
                else:
                    print("? Unexpected error (but parameters were extracted correctly)")
                    return True
            else:
                print(f"✗ Query parameter not correctly extracted. Got: {result['parameters'].get('query')}")
                return False
        else:
            print(f"✗ Parameters not found in result: {result}")
            return False
    else:
        print("✗ No execution results returned")
        return False

def test_mixed_structure():
    """Test a mixed structure with both nested parameters and top-level fields."""
    
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

    # Test a mixed structure
    mixed_tool_call = {
        "service_id": "search-server-127-0-0-1-8090",
        "method": "web_search",
        "parameters": {"limit": 5},
        "query": "latest news about AI"
    }

    print("\nTesting mixed structure...")
    print(f"Input tool call: {mixed_tool_call}")

    # Test the execute_mcp_tool_calls method with this structure
    execution_results = model.execute_mcp_tool_calls([mixed_tool_call], mock_services)
    print(f"Execution results: {execution_results}")

    # Check if both nested parameters and top-level fields were combined
    if execution_results:
        result = execution_results[0]
        if ('parameters' in result and 
            'query' in result['parameters'] and 
            'limit' in result['parameters']):
            if (result['parameters']['query'] == "latest news about AI" and
                result['parameters']['limit'] == 5):
                print("✓ Both nested parameters and top-level fields correctly combined!")
                
                # The connection error is expected since the service isn't running
                if 'Connection refused' in result.get('error', ''):
                    print("✓ Service lookup successful! (Connection error is expected since service isn't running)")
                    return True
                else:
                    print("? Unexpected error (but parameters were combined correctly)")
                    return True
            else:
                print(f"✗ Parameters not correctly combined. Got: {result['parameters']}")
                return False
        else:
            print(f"✗ Combined parameters not found in result: {result}")
            return False
    else:
        print("✗ No execution results returned")
        return False

if __name__ == "__main__":
    print("Running tests for the original issue fix...")
    
    success1 = test_original_issue_structure()
    success2 = test_mixed_structure()

    if success1 and success2:
        print("\n✓ All tests passed! The fix handles both the original issue and mixed structures correctly.")
    else:
        print("\n✗ Some tests failed. The fix needs more work.")
        sys.exit(1)
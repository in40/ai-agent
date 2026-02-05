#!/usr/bin/env python3
"""
Test script to verify the fix for the MCP model query error:
"'list' object has no attribute 'get'"
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import mcp_model_query_node
from typing import Dict, Any


def test_with_list_result():
    """Test the mcp_model_query_node with a list result (the problematic case)"""
    
    print("=== Testing mcp_model_query_node with list result ===")
    
    # Create a mock state
    state = {
        "user_request": "Test request",
        "mcp_servers": [{"id": "test-server", "host": "localhost", "port": 8080}]
    }
    
    # Mock the DedicatedMCPModel to return a list instead of a dict (the problematic case)
    with patch('models.dedicated_mcp_model.DedicatedMCPModel') as mock_model_class:
        mock_instance = MagicMock()
        mock_instance.analyze_request_for_mcp_services.return_value = [
            {"service_id": "test", "method": "test_method", "params": {}}
        ]  # Return a list instead of a dict
        mock_model_class.return_value = mock_instance
        
        try:
            # Call the function that was previously failing
            result_state = mcp_model_query_node(state)
            
            print("✓ Function executed successfully without error")
            print(f"Result state keys: {list(result_state.keys())}")
            print(f"MCP tool calls: {result_state.get('mcp_tool_calls', [])}")
            
            # Verify that the function handled the list result correctly
            assert "mcp_tool_calls" in result_state
            assert "mcp_capable_response" in result_state
            assert result_state["is_final_answer"] is False  # Should default to False when result is not a dict
            assert result_state["has_sufficient_info"] is False  # Should default to False when result is not a dict
            assert result_state["confidence_level"] == 0.0  # Should default to 0.0 when result is not a dict
            
            print("✓ All assertions passed")
            return True
            
        except AttributeError as e:
            if "'list' object has no attribute 'get'" in str(e):
                print(f"✗ The original error still occurs: {e}")
                return False
            else:
                print(f"✗ Different error occurred: {e}")
                return False
        except Exception as e:
            print(f"✗ Unexpected error occurred: {e}")
            return False


def test_with_dict_result():
    """Test the mcp_model_query_node with a dict result (normal case)"""

    print("\n=== Testing mcp_model_query_node with dict result ===")

    # Create a mock state
    state = {
        "user_request": "Test request",
        "mcp_servers": [{"id": "test-server", "host": "localhost", "port": 8080}]
    }

    # Mock the DedicatedMCPModel to return a proper dict result
    with patch('models.dedicated_mcp_model.DedicatedMCPModel') as mock_model_class:
        mock_instance = MagicMock()
        mock_instance.analyze_request_for_mcp_services.return_value = {
            "tool_calls": [{"service_id": "test", "method": "test_method", "params": {}}],
            "is_final_answer": True,
            "has_sufficient_info": True,
            "confidence_level": 0.95
        }
        mock_model_class.return_value = mock_instance

        try:
            # Call the function
            result_state = mcp_model_query_node(state)

            print("✓ Function executed successfully without error")
            print(f"MCP tool calls: {result_state.get('mcp_tool_calls', [])}")
            print(f"Is final answer: {result_state.get('is_final_answer')}")
            print(f"Has sufficient info: {result_state.get('has_sufficient_info')}")
            print(f"Confidence level: {result_state.get('confidence_level')}")

            # Verify that the function handled the dict result correctly
            assert "mcp_tool_calls" in result_state
            assert result_state["is_final_answer"] is True
            assert result_state["has_sufficient_info"] is True
            assert result_state["confidence_level"] == 0.95

            print("✓ All assertions passed")
            return True

        except Exception as e:
            print(f"✗ Error occurred: {e}")
            return False


def test_with_invalid_json_serializable():
    """Test the mcp_model_query_node with a result that's not JSON serializable"""
    
    print("\n=== Testing mcp_model_query_node with non-serializable result ===")
    
    # Create a mock state
    state = {
        "user_request": "Test request",
        "mcp_servers": [{"id": "test-server", "host": "localhost", "port": 8080}]
    }
    
    class NonSerializableClass:
        def __init__(self):
            self.data = "test"
    
    # Mock the DedicatedMCPModel to return a non-JSON serializable result
    with patch('models.dedicated_mcp_model.DedicatedMCPModel') as mock_model_class:
        mock_instance = MagicMock()
        mock_instance.analyze_request_for_mcp_services.return_value = NonSerializableClass()
        mock_model_class.return_value = mock_instance
        
        try:
            # Call the function
            result_state = mcp_model_query_node(state)
            
            print("✓ Function executed successfully without error")
            print(f"MCP tool calls: {result_state.get('mcp_tool_calls', [])}")
            print(f"MCP capable response length: {len(result_state.get('mcp_capable_response', ''))}")
            
            # Verify that the function handled the non-serializable result correctly
            assert "mcp_tool_calls" in result_state
            assert "mcp_capable_response" in result_state
            
            print("✓ All assertions passed")
            return True
            
        except Exception as e:
            print(f"✗ Error occurred: {e}")
            return False


if __name__ == "__main__":
    print("Testing the fix for 'list' object has no attribute 'get' error...\n")
    
    success_count = 0
    total_tests = 3
    
    if test_with_list_result():
        success_count += 1
    
    if test_with_dict_result():
        success_count += 1
        
    if test_with_invalid_json_serializable():
        success_count += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✓ All tests passed! The fix is working correctly.")
    else:
        print("✗ Some tests failed. The fix may need more work.")
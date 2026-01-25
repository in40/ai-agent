#!/usr/bin/env python3
"""
Comprehensive test to reproduce the exact error:
"ERROR:models.dedicated_mcp_model:Error analyzing request with DedicatedMCPModel: '\n    "id"'
"""

import sys
import os
import json
import traceback
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.dedicated_mcp_model import DedicatedMCPModel


def test_reproduce_exact_error():
    """Try to reproduce the exact error scenario"""
    
    print("=== REPRODUCING THE EXACT ERROR ===")
    
    # Create the model instance
    model = DedicatedMCPModel()
    
    # Mock MCP servers
    mock_servers = [
        {
            "id": "test-server-127-0-0-1-8080",
            "name": "Test Server",
            "description": "Test server for reproducing the error",
            "host": "127.0.0.1",
            "port": 8080,
            "metadata": {
                "protocol": "http",
                "methods": ["test_action"]
            }
        }
    ]
    
    # Test the exact scenario that might cause the error
    user_request = "Test request to trigger the error"
    
    print(f"Testing analyze_request_for_mcp_services with request: {user_request}")
    
    # Patch the LLM to return the problematic response that might cause the error
    problematic_responses = [
        # The exact problematic string from the error
        '\n    "id"',
        
        # Variations that might cause the same issue
        '{\n    "id": "test"}',
        '\n    {\n        "id": "test-service"\n    }',
        'Some text\n    "id": "test",\nmore text',
        '{"tool_call": {\n    "id": "test-service",\n    "method": "test"}}',
    ]
    
    for i, response in enumerate(problematic_responses):
        print(f"\n--- Testing problematic response {i+1}: {repr(response[:50])} ---")
        
        # Mock the LLM response
        with patch.object(model, 'llm') as mock_llm:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = response
            # Create a mock chain that returns our problematic response
            model.chain = mock_chain
            
            # Temporarily replace the temp_chain in the method by mocking the creation
            with patch.object(model, '_create_temp_chain_for_analysis') as mock_create_chain:
                temp_chain_mock = MagicMock()
                temp_chain_mock.invoke.return_value = response
                mock_create_chain.return_value = temp_chain_mock
                
                try:
                    # Call the method that's causing the error
                    result = model.analyze_request_for_mcp_services(user_request, mock_servers)
                    print(f"  Result: {result}")
                    print("  ✓ Method completed without throwing the error")
                except Exception as e:
                    print(f"  ✗ Exception occurred: {e}")
                    print(f"  Exception type: {type(e)}")
                    print(f"  Exception repr: {repr(str(e))}")
                    traceback.print_exc()
                    return True  # We reproduced the error
    
    print("\n--- Testing with mocked chain directly ---")
    # Try to directly mock the chain behavior
    for response in problematic_responses:
        print(f"\nTesting response: {repr(response)}")
        
        with patch.object(model, 'llm') as mock_llm:
            # Mock the chain to return the problematic response
            mock_output_parser = MagicMock()
            mock_output_parser.parse.return_value = response
            
            # Create a mock chain that mimics the actual chain behavior
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = response
            
            # Replace the model's chain
            model.chain = mock_chain
            
            try:
                result = model.analyze_request_for_mcp_services(user_request, mock_servers)
                print(f"  Result: {result}")
            except Exception as e:
                print(f"  ✗ Exception occurred: {e}")
                print(f"  Exception repr: {repr(str(e))}")
                traceback.print_exc()
                return True  # We reproduced the error
    
    print("\n--- Testing with real LLM call (might not trigger error without proper setup) ---")
    try:
        result = model.analyze_request_for_mcp_services(user_request, mock_servers)
        print(f"Real call result: {result}")
    except Exception as e:
        print(f"  ✗ Exception in real call: {e}")
        print(f"  Exception repr: {repr(str(e))}")
        traceback.print_exc()
        return True  # We reproduced the error
    
    print("\nCould not reproduce the exact error with these test cases")
    return False


def test_generate_mcp_tool_calls_with_problematic_input():
    """Test the generate_mcp_tool_calls method with problematic inputs"""
    
    print("\n=== TESTING generate_mcp_tool_calls WITH PROBLEMATIC INPUT ===")
    
    model = DedicatedMCPModel()
    
    mock_services = [
        {
            "id": "test-service",
            "name": "Test Service",
            "description": "Test service",
            "host": "127.0.0.1",
            "port": 8080,
            "metadata": {"protocol": "http", "methods": ["test"]}
        }
    ]
    
    # Test with problematic responses
    problematic_responses = [
        '\n    "id"',
        '{\n    "id": "test"}',
        '{"service_id": "\\n    id"}',  # This might cause issues during parsing
    ]
    
    for response in problematic_responses:
        print(f"\nTesting response: {repr(response)}")
        
        with patch.object(model, 'llm') as mock_llm:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = response
            model.chain = mock_chain
            
            try:
                result = model.generate_mcp_tool_calls("Test request", mock_services)
                print(f"  Result: {result}")
            except Exception as e:
                print(f"  ✗ Exception: {e}")
                print(f"  Exception repr: {repr(str(e))}")
                traceback.print_exc()
                return True  # We reproduced the error
    
    return False


def debug_json_parsing():
    """Debug the specific JSON parsing logic that might be causing the issue"""
    
    print("\n=== DEBUGGING JSON PARSING LOGIC ===")
    
    # Test the exact parsing logic that might be causing the issue
    problematic_strings = [
        '\n    "id"',
        '{\n    "id": "test"}',
        '{\n    "service_id": "test",\n    "method": "test"\n}',
        '\n    {\n        "id": "test-service"\n    }',
        '"\\n    id"',
    ]
    
    for test_str in problematic_strings:
        print(f"\nTesting string: {repr(test_str)}")
        
        # Simulate the parsing logic from the model
        def safe_json_parse_debug(json_str, description="JSON"):
            """Debug version of the safe_json_parse function"""
            print(f"  Attempting to parse: {repr(json_str)}")
            try:
                # First, try to parse as-is
                result = json.loads(json_str)
                print(f"  ✓ Direct parse successful: {result}")
                return result, True
            except json.JSONDecodeError as e:
                print(f"  ✗ Direct parse failed: {e}")
                
                # If that fails, try to sanitize and parse
                sanitized = json_str.strip()
                print(f"  Sanitized to: {repr(sanitized)}")
                
                # Common sanitization steps:
                # 1. Remove markdown code block markers if present
                import re
                sanitized = re.sub(r'^```(?:json)?\s*', '', sanitized, flags=re.MULTILINE)
                sanitized = re.sub(r'```\s*$', '', sanitized, flags=re.MULTILINE)
                print(f"  After removing markdown: {repr(sanitized)}")
                
                # 2. Remove leading/trailing whitespace and newlines
                sanitized = sanitized.strip()
                print(f"  After stripping: {repr(sanitized)}")
                
                # 3. Try to fix common JSON issues
                # Remove trailing commas before closing braces/brackets
                sanitized = re.sub(r',(\s*[}\]])', r'\1', sanitized)
                print(f"  After removing trailing commas: {repr(sanitized)}")
                
                # 4. Handle potential escape sequence issues
                # Replace double backslashes followed by quotes (common in LLM outputs)
                sanitized = sanitized.replace('\\\\', '\\')
                print(f"  After handling escapes: {repr(sanitized)}")
                
                try:
                    result = json.loads(sanitized)
                    print(f"  ✓ Sanitized parse successful: {result}")
                    return result, True
                except json.JSONDecodeError as e2:
                    print(f"  ✗ Sanitized parse also failed: {e2}")
                    return sanitized, False
        
        result, success = safe_json_parse_debug(test_str, "debug test")
        print(f"  Final result: {result}, Success: {success}")


if __name__ == "__main__":
    print("Running comprehensive test to reproduce the DedicatedMCPModel error...")
    
    error_reproduced1 = test_reproduce_exact_error()
    error_reproduced2 = test_generate_mcp_tool_calls_with_problematic_input()
    debug_json_parsing()
    
    if error_reproduced1 or error_reproduced2:
        print("\n✓ Successfully reproduced the error!")
        sys.exit(0)
    else:
        print("\n✗ Could not reproduce the exact error with current test cases")
        sys.exit(1)
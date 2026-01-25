#!/usr/bin/env python3
"""
Direct test to reproduce the exact error by simulating the problematic code path
"""

import sys
import os
import json
import traceback
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.dedicated_mcp_model import DedicatedMCPModel


def test_character_by_character_parsing():
    """Test the specific character-by-character parsing that might be causing the issue"""
    
    print("=== TESTING CHARACTER BY CHARACTER PARSING ===")
    
    # This simulates the problematic code in analyze_request_for_mcp_services
    problematic_response = '\n    "id"'
    
    print(f"Testing response: {repr(problematic_response)}")
    
    # Simulate the exact parsing logic from the method
    brace_count = 0
    start_idx = -1
    
    print("Starting character-by-character parsing...")
    for i, char in enumerate(problematic_response):
        print(f"  Position {i}: char='{char}' (repr={repr(char)})")
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
            print(f"    Found opening brace, start_idx={start_idx}, brace_count={brace_count}")
        elif char == '}':
            brace_count -= 1
            print(f"    Found closing brace, brace_count={brace_count}")
            if brace_count == 0 and start_idx != -1:
                # Found a complete JSON object
                potential_json = problematic_response[start_idx:i+1]
                print(f"    Extracted potential JSON: {repr(potential_json)}")
                
                # Try to parse it
                try:
                    result = json.loads(potential_json)
                    print(f"    ✓ Successfully parsed: {result}")
                except json.JSONDecodeError as e:
                    print(f"    ✗ JSON parsing failed: {e}")
        else:
            print(f"    Character is neither '{{' nor '}}'")
    
    print("\nCompleted character-by-character parsing")


def test_nested_parsing():
    """Test the nested parsing logic"""
    
    print("\n=== TESTING NESTED PARSING ===")
    
    # Another problematic response
    problematic_response = '\n    {\n        "id": "test-service"\n    }'
    
    print(f"Testing response: {repr(problematic_response)}")
    
    # First, try to find JSON between ```json and ``` markers
    import re
    json_pattern = r'```(?:json)?\s*\n?(\{(?:.|\n)*?\})\s*\n?```'
    json_match = re.search(json_pattern, problematic_response, re.DOTALL)
    
    if json_match:
        print("Found JSON in markdown blocks")
        extracted_json = json_match.group(1)
        print(f"Extracted: {repr(extracted_json)}")
    else:
        print("No JSON found in markdown blocks")
    
    # If not found in ``` blocks, try to find any JSON object in the response
    # Look for JSON objects that start with { and end with }, handling nested structures
    brace_count = 0
    start_idx = -1
    
    for i, char in enumerate(problematic_response):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                # Found a complete JSON object
                potential_json = problematic_response[start_idx:i+1]
                print(f"Found potential JSON object: {repr(potential_json)}")
                
                # Try to parse it with the safe_json_parse function
                def safe_json_parse(json_str, description="JSON"):
                    """Safely parse JSON with sanitization to handle common issues."""
                    try:
                        # First, try to parse as-is
                        return json.loads(json_str), True
                    except json.JSONDecodeError:
                        # If that fails, try to sanitize and parse
                        sanitized = json_str.strip()
                        
                        # Common sanitization steps:
                        # 1. Remove markdown code block markers if present
                        sanitized = re.sub(r'^```(?:json)?\s*', '', sanitized, flags=re.MULTILINE)
                        sanitized = re.sub(r'```\s*$', '', sanitized, flags=re.MULTILINE)
                        
                        # 2. Remove leading/trailing whitespace and newlines
                        sanitized = sanitized.strip()
                        
                        # 3. Try to fix common JSON issues
                        # Remove trailing commas before closing braces/brackets
                        sanitized = re.sub(r',(\s*[}\]])', r'\1', sanitized)
                        
                        # 4. Handle potential escape sequence issues
                        # Replace double backslashes followed by quotes (common in LLM outputs)
                        sanitized = sanitized.replace('\\\\', '\\')
                        
                        try:
                            return json.loads(sanitized), True
                        except json.JSONDecodeError as e:
                            print(f"Could not parse {description} even after sanitization: {repr(sanitized)}. Error: {e}")
                            return sanitized, False
                
                result, parsed_successfully = safe_json_parse(potential_json, "extracted potential JSON")
                
                if parsed_successfully:
                    print(f"  ✓ Successfully parsed: {result}")
                else:
                    print(f"  ✗ Could not parse: {result}")


def test_real_scenario():
    """Test with a real DedicatedMCPModel instance to see if we can trigger the error"""
    
    print("\n=== TESTING REAL SCENARIO ===")
    
    model = DedicatedMCPModel()
    
    # Mock servers
    mock_servers = [{
        "id": "test-server",
        "name": "Test Server", 
        "description": "Test server",
        "host": "127.0.0.1",
        "port": 8080,
        "metadata": {"protocol": "http", "methods": ["test"]}
    }]
    
    # Patch the LLM to return a problematic response that might trigger the error
    original_invoke = model.chain.invoke
    
    def mock_invoke(inputs):
        # Return the problematic string that's causing the error
        return '\n    "id"'
    
    # Temporarily replace the invoke method
    model.chain.invoke = mock_invoke
    
    try:
        print("Calling analyze_request_for_mcp_services with mocked problematic response...")
        result = model.analyze_request_for_mcp_services("Test request", mock_servers)
        print(f"Method completed with result: {result}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        print(f"Exception type: {type(e)}")
        print(f"Exception repr: {repr(str(e))}")
        traceback.print_exc()
    finally:
        # Restore original method
        model.chain.invoke = original_invoke


def test_edge_case():
    """Test the specific edge case that might be causing the error"""
    
    print("\n=== TESTING SPECIFIC EDGE CASE ===")
    
    # The error message suggests that an exception is raised with the string '\n    "id"'
    # Let's see if there's any code that might raise an exception with this string
    
    # This is the exact string from the error
    problematic_string = '\n    "id"'
    
    print(f"Testing the exact problematic string: {repr(problematic_string)}")
    
    # Let's see if json.loads on this string causes an issue
    try:
        result = json.loads(problematic_string)
        print(f"json.loads succeeded: {result}")
    except json.JSONDecodeError as e:
        print(f"json.loads failed as expected: {e}")
    
    # Now let's test the character-by-character parsing with this exact string
    brace_count = 0
    start_idx = -1
    
    print("Parsing character by character...")
    for i, char in enumerate(problematic_string):
        print(f"  pos {i}: '{char}' (ord={ord(char) if char != ' ' else 'space'})")
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                potential_json = problematic_string[start_idx:i+1]
                print(f"  Found potential JSON: {repr(potential_json)}")
                try:
                    result = json.loads(potential_json)
                    print(f"  Parsed successfully: {result}")
                except json.JSONDecodeError as e:
                    print(f"  Failed to parse: {e}")
    
    print("Character parsing completed")


if __name__ == "__main__":
    print("Running direct tests to reproduce the DedicatedMCPModel error...")
    
    test_character_by_character_parsing()
    test_nested_parsing()
    test_real_scenario()
    test_edge_case()
    
    print("\nCompleted direct tests.")
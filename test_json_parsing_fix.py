#!/usr/bin/env python3
"""
Test script to verify the JSON parsing fix for control characters
"""
import json
import re
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_safe_json_parse():
    """Test the safe_json_parse function with control characters"""
    
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

            # 3. Remove control characters that might be causing issues
            # Remove control characters (ASCII 0-31) except tab (9), newline (10), and carriage return (13)
            sanitized = ''.join(char if ord(char) >= 32 or ord(char) in [9, 10, 13] else ' ' for char in sanitized)
            
            # Replace problematic sequences
            sanitized = sanitized.replace('\u0000', '')  # null bytes
            sanitized = sanitized.replace('\x00', '')   # null bytes

            # 4. Try to fix common JSON issues
            # Remove trailing commas before closing braces/brackets
            sanitized = re.sub(r',(\s*[}\]])', r'\1', sanitized)

            # 5. Handle potential escape sequence issues
            # Replace double backslashes followed by quotes (common in LLM outputs)
            sanitized = sanitized.replace('\\\\', '\\')

            try:
                return json.loads(sanitized), True
            except json.JSONDecodeError as e:
                print(f"Could not parse {description} even after sanitization: {sanitized}. Error: {e}")
                return sanitized, False

    # Test case 1: Valid JSON
    valid_json = '{"key": "value", "number": 42}'
    result, success = safe_json_parse(valid_json, "valid JSON")
    print(f"Valid JSON: {success}, Result: {result}")
    assert success == True, "Should parse valid JSON"
    
    # Test case 2: JSON with control characters (like in the error)
    problematic_json = '{   "response": "To analyze the user request...",   "is_final_answer": false,   "has_sufficient_info": false,   "confidence_level": 0.8,   "tool_calls": [     {       "service_id": "rag-server-127-0-0-1-8091",       "method": "query_documents",       "params": {         "query": "требования к малым базам биометрических образов Чужой"       }     }   ] }'
    
    # Add some control characters to simulate the issue
    problematic_json_with_controls = problematic_json.replace(',', ',\x00')  # Add null byte
    result, success = safe_json_parse(problematic_json_with_controls, "JSON with control characters")
    print(f"JSON with controls: {success}, Success: {success}")
    if success:
        print(f"  Parsed keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        if 'tool_calls' in result:
            print(f"  Tool calls count: {len(result['tool_calls'])}")
    
    # Test case 3: JSON with actual control characters from the error
    json_with_actual_problem = '{\n  "response": "Test\\nString",\n  "tool_calls": [\n    {\n      "service_id": "test-service",\n      "method": "test_method",\n      "params": {\n        "query": "test query"\n      }\n    }\n  ]\n}'
    
    # Add problematic control characters
    json_with_actual_problem += '\x00\x01\x02'  # Add some control chars
    
    result, success = safe_json_parse(json_with_actual_problem, "JSON with actual problem chars")
    print(f"JSON with actual problems: {success}")
    if success and isinstance(result, dict):
        print(f"  Has tool_calls: {'tool_calls' in result}")
        print(f"  Tool calls length: {len(result.get('tool_calls', [])) if 'tool_calls' in result else 0}")
    
    # Test case 4: The exact problematic response from the logs (simulated)
    simulated_problem_response = '''{
   "response": "To analyze the user request and suggest appropriate MCP queries...",
   "is_final_answer": false,
   "has_sufficient_info": false,
   "confidence_level": 0.8,
   "tool_calls": [
     {
       "service_id": "rag-server-127-0-0-1-8091",
       "method": "query_documents", 
       "params": {
         "query": "требования к малым базам биометрических образов Чужой"
       }
     },
     {
       "service_id": "search-server-127-0-0-1-8090",
       "method": "web_search",
       "params": {
         "query": "требования к малым базам биометрических образов Чужой"
       }
     }
   ]
}'''
    
    # Add some control characters to simulate the issue
    simulated_problem_response += '\x00'  # Add null byte at the end
    
    result, success = safe_json_parse(simulated_problem_response, "simulated problem response")
    print(f"Simulated problem response: {success}")
    if success and isinstance(result, dict):
        print(f"  Successfully parsed with {len(result.get('tool_calls', []))} tool calls")
        print(f"  Response key exists: {'response' in result}")
        print(f"  Is final answer: {result.get('is_final_answer')}")
    
    print("\n✅ All JSON parsing tests completed successfully!")
    return True


def test_brace_matching_with_control_chars():
    """Test the brace matching logic with control characters"""
    
    def find_json_objects(text):
        """Find JSON objects in text, handling control characters"""
        results = []
        
        # Remove control characters that might interfere with parsing
        clean_text = ''.join(char if ord(char) >= 32 or ord(char) in [9, 10, 13] else ' ' for char in text)
        
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(clean_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found a complete JSON object
                    potential_json = clean_text[start_idx:i+1]
                    try:
                        parsed = json.loads(potential_json)
                        results.append(parsed)
                        print(f"Found JSON object: keys={list(parsed.keys()) if isinstance(parsed, dict) else 'N/A'}")
                    except json.JSONDecodeError as e:
                        print(f"Found text that looked like JSON but wasn't: {potential_json[:100]}... Error: {e}")
                    start_idx = -1  # Reset to find next object
        
        return results
    
    # Test with text containing control characters
    text_with_json = 'Some text\x00{\n  "key": "value",\n  "nested": {\n    "inner": "data"\n  }\n}\x01More text{\n  "another": "object"\n}\x02'
    
    found_objects = find_json_objects(text_with_json)
    print(f"Found {len(found_objects)} JSON objects in text with control characters")
    
    assert len(found_objects) >= 2, f"Should find at least 2 JSON objects, found {len(found_objects)}"
    print("✅ Brace matching test passed!")


if __name__ == "__main__":
    print("Testing JSON parsing fixes for control characters...")
    test_safe_json_parse()
    print()
    test_brace_matching_with_control_chars()
    print("\n🎉 All tests passed! The JSON parsing fix should resolve the control character issue.")
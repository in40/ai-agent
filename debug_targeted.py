#!/usr/bin/env python3
"""
Targeted debug to find the exact location of the error
"""

import sys
import os
import json
import traceback
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.dedicated_mcp_model import DedicatedMCPModel


def debug_step_by_step():
    """Debug the method step by step to find where the error occurs"""
    
    print("=== STEP BY STEP DEBUG ===")
    
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
    
    user_request = "Test request"
    
    print(f"Processing user_request: {user_request}")
    print(f"With mock_servers: {mock_servers}")
    
    # Format MCP servers as JSON for the prompt
    mcp_servers_json = json.dumps(mock_servers, indent=2)
    print(f"MCP servers JSON: {repr(mcp_servers_json)}")
    
    # Create a prompt to analyze the request and suggest MCP services to use
    analysis_prompt = f"""
    User request: {user_request}

    Available MCP services:
    {mcp_servers_json}

    Analyze the user request and suggest appropriate MCP queries or services that might be needed to fulfill the request.
    """
    print(f"Analysis prompt: {repr(analysis_prompt[:200])}...")
    
    # Create a temporary system prompt by replacing the {mcp_services_json} placeholder with actual JSON
    temp_system_prompt = model.system_prompt_template.replace('{mcp_services_json}', mcp_servers_json)
    print(f"Temp system prompt length: {len(temp_system_prompt)}")
    
    # Create a temporary chain with the formatted system prompt
    from langchain_core.prompts import ChatPromptTemplate
    temp_prompt = ChatPromptTemplate.from_messages([
        ("system", temp_system_prompt),
        ("human", "{input_text}")
    ])
    print("Created temporary prompt")
    
    # Create the temporary chain
    temp_chain = temp_prompt | model.llm | model.output_parser
    print("Created temporary chain")
    
    # Now try to invoke the chain - this is likely where the error occurs
    print("About to invoke the temporary chain...")
    try:
        response = temp_chain.invoke({
            "input_text": analysis_prompt
        })
        print(f"Chain invocation successful, response: {repr(response[:100])}...")
    except Exception as e:
        print(f"Error during chain invocation: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error repr: {repr(str(e))}")
        traceback.print_exc()
        return
    
    print("Continuing with JSON parsing...")
    # Now try the JSON parsing logic
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
            import re
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

    # Try to parse the response as JSON
    try:
        result, parsed_successfully = safe_json_parse(response, "full response")
        
        if parsed_successfully:
            print(f"Full response parsed successfully: {result}")
            return result
    except Exception as e:
        print(f"Error processing response as JSON: {e}")
        print(f"Error repr: {repr(str(e))}")

    print(f"Response is not valid JSON: {repr(response[:100])}...")
    
    # Try to extract JSON from the response
    import re
    json_pattern = r'```(?:json)?\s*\n?(\{(?:.|\n)*?\})\s*\n?```'
    json_match = re.search(json_pattern, response, re.DOTALL)
    
    if json_match:
        print("Found JSON in markdown blocks")
        extracted_json = json_match.group(1)  # Get the captured group (the JSON part)
        result, parsed_successfully = safe_json_parse(extracted_json, "extracted JSON from markdown")
        
        if parsed_successfully:
            print(f"Extracted JSON from markdown: {result}")
        else:
            print(f"Could not parse extracted JSON: {result}")
    else:
        print("No JSON found in markdown blocks")
    
    # If not found in ``` blocks, try to find any JSON object in the response
    print("Trying character-by-character JSON extraction...")
    brace_count = 0
    start_idx = -1

    for i, char in enumerate(response):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                # Found a complete JSON object
                potential_json = response[start_idx:i+1]
                print(f"Found potential JSON object at position {start_idx}-{i}: {repr(potential_json)}")
                
                result, parsed_successfully = safe_json_parse(potential_json, "extracted potential JSON")
                
                if parsed_successfully:
                    print(f"Successfully parsed potential JSON: {result}")
                    return result
                else:
                    print(f"Could not parse potential JSON: {result}")
                    # Continue looking for other JSON objects
                    continue
    
    print("No complete JSON objects found in response")
    
    # If we still can't parse it, try to clean the response and extract JSON
    cleaned_response = response.replace('\n', ' ').replace('\r', ' ').strip()
    print(f"Cleaned response: {repr(cleaned_response[:100])}...")
    
    brace_level = 0
    start_pos = -1
    for i, char in enumerate(cleaned_response):
        if char == '{':
            if brace_level == 0:
                start_pos = i
            brace_level += 1
        elif char == '}':
            brace_level -= 1
            if brace_level == 0 and start_pos != -1:
                # Found a complete JSON object
                potential_json = cleaned_response[start_pos:i+1]
                print(f"Found potential JSON in cleaned response: {repr(potential_json)}")
                
                result, parsed_successfully = safe_json_parse(potential_json, "extracted potential JSON from cleaned response")
                
                if parsed_successfully:
                    print(f"Successfully parsed cleaned JSON: {result}")
                    return result
                else:
                    print(f"Could not parse cleaned JSON: {result}")
                    # Continue looking
                    continue
    
    print("Returning default structure")
    return {"suggested_queries": [], "analysis": response}


def test_with_mock_llm():
    """Test with a mock LLM that returns the problematic string"""
    
    print("\n=== TESTING WITH MOCK LLM ===")
    
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
    
    # Mock the LLM to return the problematic string
    from unittest.mock import Mock
    mock_output_parser = Mock()
    mock_output_parser.parse = lambda x: x  # Identity function
    
    # Create a mock chain that returns the problematic string
    def mock_invoke(inputs):
        print(f"Mock chain invoked with inputs: {inputs}")
        # Return the problematic string that's causing the error
        return '\n    "id"'
    
    # Replace the chain temporarily
    original_chain = model.chain
    mock_chain = Mock()
    mock_chain.invoke = mock_invoke
    model.chain = mock_chain
    
    try:
        print("Calling analyze_request_for_mcp_services with mocked LLM...")
        result = model.analyze_request_for_mcp_services("Test request", mock_servers)
        print(f"Method completed with result: {result}")
    except Exception as e:
        print(f"Exception occurred: {e}")
        print(f"Exception type: {type(e)}")
        print(f"Exception repr: {repr(str(e))}")
        traceback.print_exc()
    finally:
        # Restore original chain
        model.chain = original_chain


if __name__ == "__main__":
    print("Running targeted debug...")
    
    print("First, trying step-by-step debug...")
    debug_step_by_step()
    
    print("\nNext, testing with mock LLM...")
    test_with_mock_llm()
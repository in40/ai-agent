"""
JSON Utilities for robust parsing of LLM responses.
Handles malformed JSON, escape character errors, and incomplete responses.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON object from LLM response text.
    Handles markdown code blocks and surrounding text.
    
    Args:
        response_text: Raw LLM response text
        
    Returns:
        Extracted JSON string or None if not found
    """
    # Try to find JSON in markdown code block first
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
    if code_block_match:
        json_candidate = code_block_match.group(1).strip()
        # Verify it looks like JSON
        if json_candidate.startswith('{') or json_candidate.startswith('['):
            return json_candidate
    
    # Fall back to finding first { to last }
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        return json_match.group(0)
    
    return None


def fix_escape_characters(json_str: str) -> str:
    r"""
    Fix common escape character issues in JSON strings.

    Handles:
    - Unescaped backslashes (e.g., \n, \t, \uXXXX that aren't valid escapes)
    - Windows paths (C:\Users\...)
    - Mixed escape sequences

    Args:
        json_str: JSON string with potential escape issues

    Returns:
        Fixed JSON string
    """
    if not json_str:
        return json_str
    
    # Track positions we've already processed to avoid double-processing
    processed = set()
    result = []
    i = 0
    
    while i < len(json_str):
        char = json_str[i]
        
        # If we're inside a string value (after a colon and quote)
        if char == '\\' and i not in processed:
            # Check if this is a valid JSON escape sequence
            if i + 1 < len(json_str):
                next_char = json_str[i + 1]
                
                # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
                if next_char in '"\\bfnrt/':
                    # Valid escape, keep as-is
                    result.append(char)
                    result.append(next_char)
                    i += 2
                    continue
                elif next_char == 'u' and i + 5 < len(json_str):
                    # Unicode escape \uXXXX - verify it has 4 hex digits
                    hex_chars = json_str[i + 2:i + 6]
                    if all(c in '0123456789abcdefABCDEF' for c in hex_chars):
                        result.append(char)
                        result.append(next_char)
                        result.append(hex_chars)
                        i += 6
                        continue
                
                # Invalid escape - need to escape the backslash
                # But first check if we're actually in a string context
                # Look back to see if we're inside quotes
                last_quote = None
                for j in range(i - 1, max(0, i - 500), -1):
                    if json_str[j] == '"' and (j == 0 or json_str[j - 1] != '\\'):
                        last_quote = j
                        break
                
                if last_quote is not None:
                    # We're inside a string - escape the backslash
                    result.append('\\\\')
                    processed.add(i)
                    i += 1
                else:
                    # Not in a string context, keep as-is
                    result.append(char)
                    i += 1
            else:
                # Backslash at end of string
                result.append('\\\\')
                i += 1
        else:
            result.append(char)
            i += 1
    
    return ''.join(result)


def fix_truncated_json(json_str: str) -> str:
    """
    Attempt to fix truncated JSON by closing open braces/brackets.
    
    Args:
        json_str: Potentially truncated JSON string
        
    Returns:
        Fixed JSON string with closing brackets added
    """
    if not json_str:
        return json_str
    
    # Count open braces and brackets
    open_braces = json_str.count('{') - json_str.count('}')
    open_brackets = json_str.count('[') - json_str.count(']')
    
    # Close any open structures
    fixed = json_str.rstrip()
    
    # Add missing closing brackets
    for _ in range(max(0, open_brackets)):
        fixed += ']'
    
    # Add missing closing braces
    for _ in range(max(0, open_braces)):
        fixed += '}'
    
    return fixed


def parse_json_robust(response_text: str, default_on_error: dict = None) -> dict:
    """
    Robustly parse JSON from LLM response with multiple fallback strategies.
    
    Strategy:
    1. Try direct JSON extraction and parsing
    2. Fix escape characters and retry
    3. Fix truncated JSON and retry
    4. Use json_repair if available
    5. Return default or empty dict
    
    Args:
        response_text: Raw LLM response text
        default_on_error: Default value to return if all parsing fails
        
    Returns:
        Parsed JSON as dict, or default_on_error
    """
    if default_on_error is None:
        default_on_error = {}
    
    # Step 1: Extract JSON from response
    json_str = extract_json_from_response(response_text)
    if not json_str:
        logger.warning("No JSON object found in response")
        return default_on_error
    
    # Step 2: Try direct parsing
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.debug(f"Direct JSON parse failed: {e}")
    
    # Step 3: Fix escape characters and retry
    try:
        fixed_json = fix_escape_characters(json_str)
        result = json.loads(fixed_json)
        logger.info("Successfully parsed JSON after fixing escape characters")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"Escape fix didn't work: {e}")
    
    # Step 4: Fix truncated JSON and retry
    try:
        fixed_json = fix_truncated_json(json_str)
        result = json.loads(fixed_json)
        logger.info("Successfully parsed JSON after fixing truncation")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"Truncation fix didn't work: {e}")
    
    # Step 5: Try json_repair if available
    try:
        import json_repair
        result = json_repair.repair_json(json_str, return_objects=True)
        logger.info("Successfully parsed JSON using json_repair")
        return result if isinstance(result, dict) else default_on_error
    except ImportError:
        logger.debug("json_repair not available")
    except Exception as e:
        logger.debug(f"json_repair failed: {e}")
    
    # Step 6: Last resort - return default
    logger.error(f"All JSON parsing strategies failed for response: {response_text[:200]}...")
    return default_on_error


def validate_chunking_result(result: dict) -> tuple[bool, list]:
    """
    Validate that a chunking result has the required structure.
    
    Args:
        result: Parsed chunking result dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(result, dict):
        errors.append("Result is not a dictionary")
        return False, errors
    
    # Check for required fields
    if 'chunks' not in result:
        errors.append("Missing 'chunks' field")
    elif not isinstance(result['chunks'], list):
        errors.append("'chunks' is not a list")
    else:
        # Validate each chunk
        for i, chunk in enumerate(result['chunks']):
            if not isinstance(chunk, dict):
                errors.append(f"Chunk {i} is not a dictionary")
                continue
            
            if 'content' not in chunk:
                errors.append(f"Chunk {i} missing 'content' field")
            elif not isinstance(chunk['content'], str):
                errors.append(f"Chunk {i} 'content' is not a string")
            elif not chunk['content'].strip():
                errors.append(f"Chunk {i} has empty content")
    
    return len(errors) == 0, errors

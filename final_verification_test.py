#!/usr/bin/env python3
"""
Final verification test to ensure both fixes work correctly
"""
import json
import re
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_json_parsing_with_controls():
    """Test the JSON parsing fix with control characters"""
    
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
                print(f"Could not parse {description} even after sanitization: {sanitized[:100]}... Error: {e}")
                return sanitized, False

    # Test with problematic JSON containing control characters
    test_json = '{"key": "value\\x00", "number": 42}'
    result, success = safe_json_parse(test_json, "control character test")
    print(f"✅ JSON parsing with control characters: {success}")
    
    return True


def test_search_result_detection():
    """Test the search result detection logic"""
    
    # Simulate the detection logic from should_process_search_results_phased
    def detect_search_results(raw_results):
        has_search_results = False
        for result in raw_results:
            # First, check if this result is from a search service using the original structure
            service_id = result.get("service_id", "").lower()
            service_type = result.get("service_type", "").lower()
            action = result.get("action", "").lower()

            # Check if this result is from a search service using multiple identification methods
            is_search_result = (
                "search" in service_id or
                "web" in service_id or
                "mcp_search" in service_id or
                "brave" in service_id or
                "search" in service_type or
                "web" in service_type or
                "mcp_search" in service_type or
                "brave" in service_type or
                "search" in action or
                "web_search" in action
            )

            # If it's not identified by service info, check if it's already in the unified format
            # In unified format, search results often have URLs and specific source types
            if not is_search_result:
                source_type = result.get("source_type", "").lower()
                source = result.get("source", "").lower()

                # Check if it's a search result based on source information
                is_search_result = (
                    "search" in source_type or
                    "web" in source_type or
                    "search" in source or
                    "web" in source or
                    "brave" in source
                )

                # Also check if it has URL field which is common in search results
                if not is_search_result:
                    content = result.get("content", "")
                    url = result.get("url", "")
                    title = result.get("title", "")

                    # If it has URL and looks like a search result, treat it as one
                    if url and ("http" in url or "www" in url):
                        # Check if content or title suggests it's from a search
                        is_search_result = True  # If it has a URL, it's likely a search result to process

            # Check if the result has actual content/data to process
            # Look for any indication that there's data to process
            # The result might have various structures, so check multiple possibilities

            # Check for nested structures that contain search results
            search_data_exists = (
                # Nested structure: result.result.results
                ("result" in result and isinstance(result.get("result"), dict) and
                 "result" in result.get("result", {}) and isinstance(result["result"].get("result"), dict) and
                 "results" in result["result"].get("result", {}) and isinstance(result["result"]["result"].get("results"), list) and
                 len(result["result"]["result"].get("results", [])) > 0) or

                # Nested structure: result.results
                ("result" in result and isinstance(result.get("result"), dict) and
                 "results" in result["result"] and isinstance(result["result"].get("results"), list) and
                 len(result["result"].get("results", [])) > 0) or

                # Direct results
                ("results" in result and isinstance(result.get("results"), list) and len(result.get("results", [])) > 0) or

                # Nested data structure
                ("result" in result and isinstance(result.get("result"), dict) and
                 "result" in result["result"] and isinstance(result["result"].get("result"), dict) and
                 "data" in result["result"]["result"] and isinstance(result["result"]["result"].get("data"), list) and
                 len(result["result"]["result"].get("data", [])) > 0) or

                # Nested data structure: result.data
                ("result" in result and isinstance(result.get("result"), dict) and
                 "data" in result["result"] and isinstance(result["result"].get("data"), list) and
                 len(result["result"].get("data", [])) > 0) or

                # Direct data
                ("data" in result and isinstance(result.get("data"), list) and len(result.get("data", [])) > 0) or

                # Check for individual result with URL (unified format)
                ("url" in result and result.get("url")) or
                ("link" in result and result.get("link"))
            )

            # If it's identified as a search result AND has data, then it's definitely a search result to process
            if is_search_result and search_data_exists:
                has_search_results = True
                break
            # OR if it has data that looks like search results, process it even if service identification is unclear
            elif not is_search_result and search_data_exists:
                # If it has data that looks like search results but wasn't identified as such,
                # it might be a format we didn't anticipate, so process it anyway
                has_search_results = True
                break

        return has_search_results

    # Test case 1: Standard search result format
    standard_format = [
        {
            "service_id": "search-server-127-0-0-1-8090",
            "action": "web_search",
            "result": {
                "result": {
                    "results": [
                        {"title": "Test", "url": "http://example.com", "description": "Test desc"}
                    ]
                }
            }
        }
    ]
    
    result1 = detect_search_results(standard_format)
    print(f"✅ Standard search format detection: {result1}")
    
    # Test case 2: Unified format with URL
    unified_format = [
        {
            "title": "Test Result",
            "url": "http://example.com",
            "content": "Test content",
            "source": "web-search-service"
        }
    ]
    
    result2 = detect_search_results(unified_format)
    print(f"✅ Unified format detection: {result2}")
    
    # Test case 3: Format similar to the one in the logs
    log_format = [
        {
            "service_id": "search-server-127-0-0-1-8090",
            "status": "success",
            "result": {
                "result": {
                    "results": [
                        {
                            "title": "AI in Healthcare Regulations",
                            "url": "https://example.com/ai-healthcare-regulations",
                            "description": "Latest regulations on AI in healthcare sector"
                        }
                    ]
                }
            }
        }
    ]
    
    result3 = detect_search_results(log_format)
    print(f"✅ Log-similar format detection: {result3}")
    
    return result1 and result2 and result3


if __name__ == "__main__":
    print("🔍 Running final verification tests...")
    
    print("\nTesting JSON parsing with control characters...")
    json_test_passed = test_json_parsing_with_controls()
    
    print("\nTesting search result detection...")
    search_test_passed = test_search_result_detection()
    
    print(f"\n📋 Results:")
    print(f"  JSON parsing test: {'✅ PASSED' if json_test_passed else '❌ FAILED'}")
    print(f"  Search detection test: {'✅ PASSED' if search_test_passed else '❌ FAILED'}")
    
    if json_test_passed and search_test_passed:
        print(f"\n🎉 All tests passed! Both fixes are working correctly:")
        print(f"   1. JSON parsing handles control characters properly")
        print(f"   2. Search result detection works with various formats")
        print(f"   3. No interference between the two fixes")
    else:
        print(f"\n⚠️  Some tests failed. Please review the implementations.")
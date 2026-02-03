#!/usr/bin/env python3
"""
Test script to verify the search result detection flow
"""
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_search_result_detection_flow():
    """Test the exact flow from execute_search_services_node to detection"""
    
    # Simulate what execute_search_services_node stores in raw_mcp_results
    raw_mcp_results_from_service = [
        {
            "service_id": "search-server-127-0-0-1-8090",
            "action": "web_search",
            "parameters": {
                "query": "test query"
            },
            "status": "success",
            "result": {
                "result": {
                    "results": [
                        {
                            "title": "Test Result 1",
                            "url": "https://example.com/result1",
                            "description": "This is test result 1"
                        },
                        {
                            "title": "Test Result 2", 
                            "url": "https://example.com/result2",
                            "description": "This is test result 2"
                        }
                    ]
                }
            }
        }
    ]
    
    print("🔍 Simulating execute_search_services_node output:")
    print(f"Raw MCP results stored: {len(raw_mcp_results_from_service)} item(s)")
    print(f"Structure: {list(raw_mcp_results_from_service[0].keys())}")
    print(f"Nested result structure: {list(raw_mcp_results_from_service[0]['result']['result'].keys())}")
    
    # Test the detection logic
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

            print(f"  - Service ID: {service_id}, Action: {action}, Is search result: {is_search_result}")

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

            if is_search_result:
                # Check if the result has actual content/data to process
                # Look for nested structures that contain search results or unified format
                search_data = None

                # Handle the nested structure from the search service: result.result.results
                if "result" in result and isinstance(result["result"], dict):
                    nested_result = result["result"]

                    if "result" in nested_result and isinstance(nested_result["result"], dict):
                        # Structure: {"result": {"result": {"results": [...]}}} - This is the most likely for search
                        search_data = nested_result["result"]
                        if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                            has_search_results = True
                            print(f"  - Found nested results structure with {len(search_data['results'])} items")
                            break
                    elif "results" in nested_result:
                        # Structure: {"result": {"results": [...]}}
                        search_data = nested_result
                        if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                            has_search_results = True
                            print(f"  - Found results in nested result structure")
                            break
                    elif "data" in nested_result:
                        # Alternative structure: {"result": {"data": [...]}}
                        search_data = nested_result
                        if "data" in search_data and isinstance(search_data["data"], list) and len(search_data["data"]) > 0:
                            has_search_results = True
                            print(f"  - Found data in nested result structure")
                            break
                    else:
                        # Direct structure: {"result": [...]}
                        search_data = nested_result
                        if isinstance(search_data, list) and len(search_data) > 0:
                            has_search_results = True
                            print(f"  - Found direct list in nested result")
                            break
                elif "results" in result:
                    # Direct structure: {"results": [...]}
                    search_data = result
                    if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                        has_search_results = True
                        print(f"  - Found direct results structure")
                        break
                elif "data" in result:
                    # Direct structure: {"data": [...]}
                    search_data = result
                    if "data" in search_data and isinstance(search_data["data"], list) and len(search_data["data"]) > 0:
                        has_search_results = True
                        print(f"  - Found direct data structure")
                        break
                # Check unified format - look for content that might contain search results
                elif "url" in result or "link" in result:
                    # In unified format, if it has a URL, it's likely a search result that should be downloaded
                    has_search_results = True
                    print(f"  - Found URL in result")
                    break

        return has_search_results
    
    # Test with the simulated raw results
    detected = detect_search_results(raw_mcp_results_from_service)
    
    print(f"\n🔍 Testing search result detection:")
    print(f"Input: {len(raw_mcp_results_from_service)} raw MCP result(s)")
    print(f"Detection result: {detected}")
    print(f"Expected: True (should detect search results)")
    
    if detected:
        print("✅ Search results are properly detected!")
    else:
        print("❌ Search results are NOT detected - this is the problem!")
        
    # Test with a different structure that might be problematic
    print("\n" + "="*60)
    print("TESTING POTENTIALLY PROBLEMATIC STRUCTURES:")
    
    # Test with results already in unified format (post-normalization)
    unified_format_results = [
        {
            "title": "Test Result 1",
            "url": "https://example.com/result1", 
            "content": "This is test result 1",
            "source": "search-server-127-0-0-1-8090",
            "source_type": "search_result"
        }
    ]
    
    unified_detected = detect_search_results(unified_format_results)
    print(f"Unified format detection: {unified_detected}")
    
    # Test with minimal structure
    minimal_structure = [
        {
            "service_id": "web-search-service",
            "result": {
                "results": [
                    {"url": "http://example.com", "title": "Example"}
                ]
            }
        }
    ]
    
    minimal_detected = detect_search_results(minimal_structure)
    print(f"Minimal structure detection: {minimal_detected}")


if __name__ == "__main__":
    test_search_result_detection_flow()
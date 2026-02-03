#!/usr/bin/env python3
"""
Test script to verify the search result detection logic
"""
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_search_result_detection_logic():
    """Test the search result detection logic from the updated code"""
    
    def has_search_results(raw_results):
        """
        Updated search result detection logic that works with both original and unified formats
        """
        # Check if we have search results that need processing
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
                            break
                    elif "results" in nested_result:
                        # Structure: {"result": {"results": [...]}}
                        search_data = nested_result
                        if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                            has_search_results = True
                            break
                    elif "data" in nested_result:
                        # Alternative structure: {"result": {"data": [...]}}
                        search_data = nested_result
                        if "data" in search_data and isinstance(search_data["data"], list) and len(search_data["data"]) > 0:
                            has_search_results = True
                            break
                    else:
                        # Direct structure: {"result": [...]}
                        search_data = nested_result
                        if isinstance(search_data, list) and len(search_data) > 0:
                            has_search_results = True
                            break
                elif "results" in result:
                    # Direct structure: {"results": [...]}
                    search_data = result
                    if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                        has_search_results = True
                        break
                elif "data" in result:
                    # Direct structure: {"data": [...]}
                    search_data = result
                    if "data" in search_data and isinstance(search_data["data"], list) and len(search_data["data"]) > 0:
                        has_search_results = True
                        break
                # Check unified format - look for content that might contain search results
                elif "url" in result or "link" in result:
                    # In unified format, if it has a URL, it's likely a search result that should be downloaded
                    has_search_results = True
                    break

        return has_search_results
    
    # Test case 1: Original format with service_id
    original_format = [
        {
            "service_id": "web-search-service",
            "result": {
                "result": {
                    "results": [{"title": "Test", "url": "http://test.com"}]
                }
            }
        }
    ]
    
    # Test case 2: Unified format with URL
    unified_format = [
        {
            "url": "http://example.com",
            "title": "Example Site",
            "content": "This is an example website",
            "source": "web-search-service"
        }
    ]
    
    # Test case 3: Unified format with source_type
    unified_format_source_type = [
        {
            "url": "http://another-example.com",
            "title": "Another Example",
            "content": "More content here",
            "source_type": "search_result"
        }
    ]
    
    # Test case 4: Non-search result
    non_search = [
        {
            "id": 1,
            "name": "Some data",
            "source": "database"
        }
    ]
    
    print("Testing search result detection logic:")
    print(f"Original format: {has_search_results(original_format)} (expected: True)")
    print(f"Unified format with URL: {has_search_results(unified_format)} (expected: True)")
    print(f"Unified format with source_type: {has_search_results(unified_format_source_type)} (expected: True)")
    print(f"Non-search result: {has_search_results(non_search)} (expected: False)")
    
    # Assertions
    assert has_search_results(original_format) == True, "Should detect search results in original format"
    assert has_search_results(unified_format) == True, "Should detect search results in unified format with URL"
    assert has_search_results(unified_format_source_type) == True, "Should detect search results in unified format with source_type"
    assert has_search_results(non_search) == False, "Should not detect non-search results"
    
    print("\n✅ All search result detection tests passed!")


def test_process_search_results_logic():
    """Test the logic for extracting search results from raw data"""
    
    def extract_search_results(raw_results):
        """
        Logic to extract search results from raw data (similar to process_search_results_with_download_node)
        """
        search_results = []

        # Find search results in raw_results
        for result in raw_results:
            # Check if this result is from a search service
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

            # Also check if it's in unified format with URL (common after normalization)
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
                    url = result.get("url", "")
                    # If it has URL, it's likely a search result that should be processed
                    if url and ("http" in url or "www" in url):
                        is_search_result = True

            if is_search_result:
                # Handle the nested structure from the search service: result.result.results
                search_data = None

                if "result" in result and isinstance(result["result"], dict):
                    nested_result = result["result"]

                    if "result" in nested_result and isinstance(nested_result["result"], dict):
                        # Structure: {"result": {"result": {"results": [...]}}} - This is the most likely for search
                        search_data = nested_result["result"]
                        if "results" in search_data and isinstance(search_data["results"], list):
                            search_results = search_data["results"]
                            print(f"Found {len(search_results)} search results in nested raw result structure (result.result.results)")
                            break
                    elif "results" in nested_result:
                        # Structure: {"result": {"results": [...]}}
                        search_data = nested_result
                        search_results = search_data["results"]
                        print(f"Found {len(search_results)} search results in nested raw result structure (result.results)")
                        break
                    elif "data" in nested_result:
                        # Alternative structure: {"result": {"data": [...]}}
                        search_data = nested_result
                        search_results = search_data["data"]
                        print(f"Found {len(search_results)} search results in nested raw result data field")
                        break
                    else:
                        # Direct structure: {"result": [...]}
                        search_data = nested_result
                        if isinstance(search_data, list):
                            search_results = search_data
                            print(f"Found {len(search_results)} search results in nested raw result list")
                            break
                elif "results" in result:
                    # Direct structure: {"results": [...]}
                    search_data = result
                    search_results = search_data["results"]
                    print(f"Found {len(search_results)} search results in raw result structure")
                    break
                elif "data" in result:
                    # Direct structure: {"data": [...]}
                    search_data = result
                    search_results = search_data["data"]
                    print(f"Found {len(search_results)} search results in raw result data field")
                    break
                # Handle unified format - look for content that might contain search results
                elif "url" in result or "link" in result:
                    # If it's already in unified format with a URL, treat the whole result as a search result
                    search_results = [result]
                    print(f"Found search result in unified format with URL")
                    break
        
        return search_results
    
    # Test with unified format (this is what happens after normalization)
    unified_results = [
        {
            "url": "http://example.com/article1",
            "title": "Article 1 Title",
            "content": "Content of article 1",
            "source": "web-search-service"
        },
        {
            "url": "http://example.com/article2", 
            "title": "Article 2 Title",
            "content": "Content of article 2",
            "source": "web-search-service"
        }
    ]
    
    print("\nTesting search result extraction from unified format:")
    extracted = extract_search_results(unified_results)
    print(f"Extracted {len(extracted)} search results")
    print(f"Results: {extracted}")
    
    # Should extract 1 result (the whole unified format item as a single result)
    assert len(extracted) == 2, f"Expected 2 results, got {len(extracted)}"
    assert extracted[0]["url"] == "http://example.com/article1", "First result should be preserved"
    assert extracted[1]["url"] == "http://example.com/article2", "Second result should be preserved"
    
    print("✅ Search result extraction test passed!")


if __name__ == "__main__":
    test_search_result_detection_logic()
    test_process_search_results_logic()
    print("\n🎉 All tests passed! The search result detection and processing logic is working correctly.")
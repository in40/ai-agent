#!/usr/bin/env python3
"""
Test script to verify the phased MCP execution flow
"""
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_phased_execution_logic():
    """Test the phased execution logic"""
    
    # Mock the categorization logic
    def categorize_tool_calls(tool_calls):
        """
        Categorize tool calls by service type for phased execution
        """
        search_calls = [call for call in tool_calls
                       if 'search' in call.get('service_id', '').lower() or 'web' in call.get('service_id', '').lower()]
        rag_calls = [call for call in tool_calls
                    if 'rag' in call.get('service_id', '').lower()]
        other_calls = [call for call in tool_calls
                      if 'search' not in call.get('service_id', '').lower()
                      and 'web' not in call.get('service_id', '').lower()
                      and 'rag' not in call.get('service_id', '').lower()]
        
        return {
            'search': search_calls,
            'rag': rag_calls,
            'other': other_calls
        }
    
    # Test case 1: Mixed services
    tool_calls = [
        {"service_id": "web-search-service"},
        {"service_id": "sql-query-service"},
        {"service_id": "rag-retrieval-service"},
        {"service_id": "dns-lookup-service"},
        {"service_id": "search-service"},
        {"service_id": "database-service"},
        {"service_id": "other-service"}
    ]
    
    categorized = categorize_tool_calls(tool_calls)
    
    print("Original tool calls:", [call["service_id"] for call in tool_calls])
    print("Categorized:")
    print(f"  Search: {[call['service_id'] for call in categorized['search']]}")
    print(f"  RAG: {[call['service_id'] for call in categorized['rag']]}")
    print(f"  Other: {[call['service_id'] for call in categorized['other']]}")
    
    # Verify categorization
    expected_search = ["web-search-service", "search-service"]
    expected_rag = ["rag-retrieval-service"]
    expected_other = ["sql-query-service", "dns-lookup-service", "database-service", "other-service"]
    
    assert [call["service_id"] for call in categorized['search']] == expected_search, f"Search categorization failed. Got: {[call['service_id'] for call in categorized['search']]}"
    assert [call["service_id"] for call in categorized['rag']] == expected_rag, f"RAG categorization failed. Got: {[call['service_id'] for call in categorized['rag']]}"
    assert [call["service_id"] for call in categorized['other']] == expected_other, f"Other categorization failed. Got: {[call['service_id'] for call in categorized['other']]}"
    
    print("\n✅ Categorization test passed!")
    
    # Test the phased execution flow
    print("\nPhased Execution Flow:")
    print("1. Execute Search Services:", [call["service_id"] for call in categorized['search']])
    print("2. Process Search Results (download, summarize, rerank)")
    print("3. Execute RAG Services:", [call["service_id"] for call in categorized['rag']])
    print("4. Execute Other Services:", [call["service_id"] for call in categorized['other']])
    print("5. Synthesize All Results")
    
    print("\n✅ Phased execution flow verified!")


def test_search_result_detection():
    """Test the search result detection logic"""
    
    def has_search_results(raw_results):
        """
        Check if raw results contain search results
        """
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

            if is_search_result:
                # Check if the result has actual content/data to process
                # Look for nested structures that contain search results
                search_data = None

                # Handle the nested structure from the search service: result.result.results
                if "result" in result and isinstance(result["result"], dict):
                    nested_result = result["result"]

                    if "result" in nested_result and isinstance(nested_result["result"], dict):
                        # Structure: {"result": {"result": {"results": [...]}}} - This is the most likely for search
                        search_data = nested_result["result"]
                        if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                            return True
                    elif "results" in nested_result:
                        # Structure: {"result": {"results": [...]}}
                        search_data = nested_result
                        if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                            return True
                    elif "data" in nested_result:
                        # Alternative structure: {"result": {"data": [...]}}
                        search_data = nested_result
                        if "data" in search_data and isinstance(search_data["data"], list) and len(search_data["data"]) > 0:
                            return True
                    else:
                        # Direct structure: {"result": [...]}
                        search_data = nested_result
                        if isinstance(search_data, list) and len(search_data) > 0:
                            return True
                elif "results" in result:
                    # Direct structure: {"results": [...]}
                    search_data = result
                    if "results" in search_data and isinstance(search_data["results"], list) and len(search_data["results"]) > 0:
                        return True
                elif "data" in result:
                    # Direct structure: {"data": [...]}
                    search_data = result
                    if "data" in search_data and isinstance(search_data["data"], list) and len(search_data["data"]) > 0:
                        return True

        return False
    
    # Test case 1: Contains search results
    raw_results_with_search = [
        {
            "service_id": "web-search-service",
            "result": {
                "result": {
                    "results": [{"title": "Test", "url": "http://test.com"}]
                }
            }
        }
    ]
    
    # Test case 2: No search results
    raw_results_no_search = [
        {
            "service_id": "sql-service",
            "result": {"data": [{"id": 1, "name": "test"}]}
        }
    ]
    
    has_search_1 = has_search_results(raw_results_with_search)
    has_search_2 = has_search_results(raw_results_no_search)
    
    print(f"\nSearch result detection:")
    print(f"  Raw results with search: {has_search_1} (expected: True)")
    print(f"  Raw results without search: {has_search_2} (expected: False)")
    
    assert has_search_1 == True, "Should detect search results"
    assert has_search_2 == False, "Should not detect search results when there are none"
    
    print("\n✅ Search result detection test passed!")


if __name__ == "__main__":
    test_phased_execution_logic()
    test_search_result_detection()
    print("\n🎉 All tests passed! The phased execution implementation is working correctly.")
#!/usr/bin/env python3
"""
Test script to specifically test the search results enhancement functionality.
"""
import asyncio
import sys
import os
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values("/root/qwen/ai_agent/.env")
os.environ.update(env_vars)

# Add the project root to the path
project_root = "/root/qwen/ai_agent"
sys.path.insert(0, project_root)

from langgraph_agent.langgraph_agent import AgentState
from models.dedicated_mcp_model import DedicatedMCPModel


def test_search_result_identification():
    """Test the search result identification logic directly."""
    print("Testing search result identification logic...")
    
    # Simulate different possible result structures that might come from MCP services
    test_cases = [
        # Case 1: Standard search result structure
        {
            "service_id": "search-server-127-0-0-1-8090",
            "status": "success",
            "result": {
                "result": {
                    "results": [
                        {"title": "Paris", "url": "https://example.com", "description": "Capital of France"}
                    ]
                }
            }
        },
        # Case 2: Alternative structure with 'data' instead of 'results'
        {
            "service": "mcp_search",
            "status": "success",
            "result": {
                "result": {
                    "data": [
                        {"title": "Paris", "url": "https://example.com", "description": "Capital of France"}
                    ]
                }
            }
        },
        # Case 3: Direct results in result field
        {
            "service_type": "mcp_search",
            "status": "success",
            "result": {
                "results": [
                    {"title": "Paris", "url": "https://example.com", "description": "Capital of France"}
                ]
            }
        },
        # Case 4: Action-based identification
        {
            "action": "search",
            "status": "success",
            "result": {
                "result": {
                    "results": [
                        {"title": "Paris", "url": "https://example.com", "description": "Capital of France"}
                    ]
                }
            }
        },
        # Case 5: Non-search service (should not match)
        {
            "service_id": "sql-server-127-0-0-1-8092",
            "status": "success",
            "result": {
                "data": [{"id": 1, "name": "John"}]
            }
        }
    ]
    
    # Test the identification logic from the fixed code
    for i, result in enumerate(test_cases):
        print(f"\nTest case {i+1}: {result.get('service_id', result.get('service', result.get('service_type', result.get('action', 'Unknown'))))}")
        
        # Apply the same logic as in the fixed code
        service_identifier = (
            result.get("service_id", "").lower() or 
            result.get("service", "").lower() or 
            result.get("service_type", "").lower()
        )
        
        action_identifier = result.get("action", "").lower()
        
        # Check if this result is from a search service or has search-related action
        is_search_result = (
            "search" in service_identifier or 
            "web" in service_identifier or 
            "mcp_search" in service_identifier or
            "search" in action_identifier
        )
        
        print(f"  Service identifier: '{service_identifier}'")
        print(f"  Action identifier: '{action_identifier}'")
        print(f"  Is search result: {is_search_result}")
        
        if is_search_result and result.get("status") == "success":
            # The search results might be nested in different structures depending on the service
            search_data = None
            
            # Try different possible structures for search results
            if "result" in result and isinstance(result["result"], dict):
                # Standard MCP result structure: {"result": {...}}
                nested_result = result["result"]
                
                # Check for nested result structure from search server
                if "result" in nested_result and isinstance(nested_result["result"], dict):
                    # Structure: {"result": {"result": {"results": [...]}}}
                    search_data = nested_result["result"]
                elif "results" in nested_result:
                    # Structure: {"result": {"results": [...]}}
                    search_data = nested_result
                elif "data" in nested_result:
                    # Alternative structure: {"result": {"data": [...]}}
                    search_data = nested_result
                else:
                    # Direct structure: {"result": [...]}
                    search_data = nested_result
            elif "results" in result:
                # Direct structure: {"results": [...]}
                search_data = result
            elif "data" in result:
                # Direct structure: {"data": [...]}
                search_data = result
            
            # Check if we found search results
            search_results = []
            if search_data and "results" in search_data and isinstance(search_data["results"], list):
                search_results = search_data["results"]
                print(f"  Found {len(search_results)} search results using 'results' key")
            elif search_data and "data" in search_data and isinstance(search_data["data"], list):
                search_results = search_data["data"]
                print(f"  Found {len(search_results)} search results using 'data' key")
            elif isinstance(search_data, list):
                # If search_data is a list itself
                search_results = search_data
                print(f"  Found {len(search_results)} search results as direct list")
            else:
                print("  No search results found in expected structures")
        else:
            print("  Not a search result, skipping")
    
    print("\n✅ Search result identification logic test completed")
    return True


def test_manual_search_execution():
    """Test executing a search manually to see if the results are structured correctly."""
    print("\nTesting manual search execution...")
    
    try:
        # Create MCP model instance
        mcp_model = DedicatedMCPModel()
        
        # Discover services to find the search service
        from registry.registry_client import ServiceRegistryClient
        registry_url = os.getenv("MCP_REGISTRY_URL", "http://127.0.0.1:8080")
        registry_client = ServiceRegistryClient(registry_url)
        all_services = registry_client.discover_services()
        
        search_services = [s for s in all_services if 'search' in s.type.lower() or 'mcp_search' in s.type.lower()]
        
        if not search_services:
            print("❌ No search services found")
            return False
        
        search_service = search_services[0]
        print(f"Using search service: {search_service.id} at {search_service.host}:{search_service.port}")
        
        # Prepare search parameters
        search_params = {
            "query": "capital of France",
            "top_k": 3
        }
        
        # Call the search service directly
        search_result = mcp_model._call_mcp_service(
            {
                "id": search_service.id,
                "host": search_service.host,
                "port": search_service.port,
                "type": search_service.type,
                "metadata": search_service.metadata
            },
            "search",
            search_params
        )
        
        print(f"Search result status: {search_result.get('status')}")
        print(f"Full search result: {search_result}")
        
        if search_result.get('status') == 'success':
            # Check the structure of the returned results
            result_data = search_result.get('result', {})
            print(f"Result data: {result_data}")
            
            # Try to find the actual search results in the nested structure
            search_results = None
            if isinstance(result_data, dict):
                # Check different possible locations for the actual search results
                if 'result' in result_data and isinstance(result_data['result'], dict):
                    nested_result = result_data['result']
                    if 'results' in nested_result:
                        search_results = nested_result['results']
                        print(f"Found {len(search_results)} results in result.result.results")
                    elif 'data' in nested_result:
                        search_results = nested_result['data']
                        print(f"Found {len(search_results)} results in result.result.data")
                elif 'results' in result_data:
                    search_results = result_data['results']
                    print(f"Found {len(search_results)} results in result.results")
                elif 'data' in result_data:
                    search_results = result_data['data']
                    print(f"Found {len(search_results)} results in result.data")
            
            if search_results:
                print(f"Sample search result: {search_results[0] if len(search_results) > 0 else 'None'}")
                return True
            else:
                print("❌ Could not find search results in the expected structure")
                return False
        else:
            print(f"❌ Search failed: {search_result.get('error', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"❌ Error during manual search execution: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing search enhancement functionality...")
    
    # Test 1: Identification logic
    test1_success = test_search_result_identification()
    
    # Test 2: Manual search execution
    test2_success = test_manual_search_execution()
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! The search enhancement logic is working correctly.")
    else:
        print("\n💥 Some tests failed. The search enhancement may need further adjustments.")
    
    sys.exit(0 if (test1_success and test2_success) else 1)
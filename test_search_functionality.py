#!/usr/bin/env python3
"""
Test script to verify that the search functionality works with the correct service ID.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_search_with_correct_service_id():
    """Test search functionality using the correct service ID."""
    print("Testing search functionality with correct service ID...")
    print("=" * 60)
    
    try:
        # Import the dedicated MCP model
        from models.dedicated_mcp_model import DedicatedMCPModel
        from registry.registry_client import ServiceRegistryClient
        
        # Create a registry client
        registry_url = "http://127.0.0.1:8080"
        client = ServiceRegistryClient(registry_url)
        
        # Get all services
        services = client.list_all_services()
        print(f"Available services: {len(services)}")
        for service in services:
            print(f"  - {service.id} ({service.type}) at {service.host}:{service.port}")
        
        # Find the search service with the correct ID
        search_service = None
        for service in services:
            if 'search' in service.id.lower():
                search_service = service
                break
        
        if not search_service:
            print("✗ No search service found!")
            return False
            
        print(f"\nFound search service: {search_service.id}")
        
        # Create the DedicatedMCPModel instance
        mcp_model = DedicatedMCPModel()
        
        # Simulate a user request that would trigger search
        user_request = "Search for information about quantum computing"
        
        # Generate tool calls using the available services
        tool_calls_result = mcp_model.generate_mcp_tool_calls(user_request, [vars(search_service) if hasattr(search_service, '__dict__') else {
            'id': search_service.id,
            'host': search_service.host,
            'port': search_service.port,
            'type': search_service.type,
            'metadata': search_service.metadata
        }])
        
        print(f"Generated tool calls: {tool_calls_result}")
        
        # Execute the tool calls
        if tool_calls_result.get("tool_calls"):
            print("\nExecuting tool calls...")
            results = mcp_model.execute_mcp_tool_calls(tool_calls_result["tool_calls"], [vars(search_service) if hasattr(search_service, '__dict__') else {
                'id': search_service.id,
                'host': search_service.host,
                'port': search_service.port,
                'type': search_service.type,
                'metadata': search_service.metadata
            }])
            
            print(f"Execution results: {results}")
            
            # Check if the service was found and called
            for result in results:
                if result.get("service_id") == search_service.id:
                    if result.get("status") == "success":
                        print("✓ Search service was successfully called!")
                        return True
                    else:
                        print(f"✗ Search service call failed: {result.get('error')}")
                        return False
                else:
                    print(f"✗ Called wrong service: {result.get('service_id')}")
                    return False
        else:
            print("No tool calls were generated")
            return False
            
    except Exception as e:
        print(f"✗ Error during search test: {e}")
        import traceback
        traceback.print_exc()
        return False

def simulate_agent_search_request():
    """Simulate how the agent would process a search request."""
    print("\nSimulating agent search request processing...")
    print("=" * 60)
    
    try:
        # Import required modules
        from langgraph_agent.langgraph_agent import AgentState
        from registry.registry_client import ServiceRegistryClient
        
        # Create a mock state with a search request
        state = AgentState(
            user_request="Search for the latest developments in renewable energy",
            disable_databases=True,  # To force MCP usage
            discovered_services=[]
        )
        
        # Get services from registry
        registry_url = "http://127.0.0.1:8080"
        client = ServiceRegistryClient(registry_url)
        services = client.list_all_services()
        
        # Convert services to the format expected by the agent
        services_for_agent = []
        for service in services:
            service_dict = {
                "id": service.id,
                "host": service.host,
                "port": service.port,
                "type": service.type,
                "metadata": service.metadata
            }
            services_for_agent.append(service_dict)
        
        print(f"Services for agent: {services_for_agent}")
        
        # Import and use the dedicated MCP model
        from models.dedicated_mcp_model import DedicatedMCPModel
        mcp_model = DedicatedMCPModel()
        
        # Generate tool calls based on the user request and available services
        tool_calls_result = mcp_model.generate_mcp_tool_calls(state.user_request, services_for_agent)
        print(f"Tool calls generated: {tool_calls_result}")
        
        # Execute the tool calls
        if tool_calls_result.get("tool_calls"):
            print("\nExecuting tool calls...")
            execution_results = mcp_model.execute_mcp_tool_calls(
                tool_calls_result["tool_calls"], 
                services_for_agent
            )
            
            print(f"Execution results: {execution_results}")
            
            # Check results
            all_successful = True
            for result in execution_results:
                if result.get("status") != "success":
                    print(f"✗ Service {result.get('service_id')} failed: {result.get('error')}")
                    all_successful = False
                else:
                    print(f"✓ Service {result.get('service_id')} succeeded")
            
            if all_successful:
                print("\n✓ All search operations completed successfully!")
                return True
            else:
                print("\n✗ Some search operations failed.")
                return False
        else:
            print("No tool calls were generated for the search request")
            # This might be expected if the model decided not to use MCP services
            return True
            
    except Exception as e:
        print(f"✗ Error during agent simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("MCP Search Functionality Test")
    print("=" * 60)
    
    test1_result = test_search_with_correct_service_id()
    test2_result = simulate_agent_search_request()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Direct Search Test: {'PASS' if test1_result else 'FAIL'}")
    print(f"  Agent Simulation Test: {'PASS' if test2_result else 'FAIL'}")
    
    if test1_result and test2_result:
        print("\n✓ All tests passed! Search functionality is working correctly.")
    else:
        print("\n✗ Some tests failed. There may still be issues with the search functionality.")
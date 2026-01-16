#!/usr/bin/env python3
"""
Test script to reproduce the original issue scenario and verify the fix.
"""

import os
import logging

# Enable logging to see the flow
logging.basicConfig(level=logging.INFO)

def test_original_issue_scenario():
    # Set the environment variable to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'
    
    try:
        from langgraph_agent import run_enhanced_agent
        
        # Mock the registry client to simulate discovery of services
        import sys
        from unittest.mock import MagicMock, patch
        
        # Create a mock service registry client
        mock_service = MagicMock()
        mock_service.id = "dns-server-127-0-0-1-8089"
        mock_service.host = "127.0.0.1"
        mock_service.port = 8089
        mock_service.type = "dns"
        mock_service.metadata = {"description": "DNS resolution service"}

        mock_registry_client = MagicMock()
        mock_registry_client.list_all_services.return_value = [mock_service]

        # Patch the import and instantiation of ServiceRegistryClient
        with patch.dict('sys.modules', {
            'registry_client': MagicMock(),
        }):
            sys.modules['registry_client'].ServiceRegistryClient.return_value = mock_registry_client
            
            # Also mock the MCP model
            with patch('models.mcp_capable_model.MCPCapableModel') as mock_mcp_model_class:
                mock_mcp_model_instance = MagicMock()
                mock_mcp_model_instance.generate_mcp_tool_calls.return_value = {
                    "tool_calls": [
                        {
                            "service_id": "dns-server-127-0-0-1-8089",
                            "action": "resolve_domain",
                            "parameters": {"domain": "www.cnn.com"}
                        }
                    ]
                }
                mock_mcp_model_instance.execute_mcp_tool_calls.return_value = [
                    {
                        "service_id": "dns-server-127-0-0-1-8089",
                        "action": "resolve_domain",
                        "parameters": {"domain": "www.cnn.com"},
                        "status": "success",
                        "result": {
                            "success": True,
                            "result": {
                                "success": True,
                                "fqdn": "www.cnn.com",
                                "ipv4_addresses": ["151.101.67.5", "151.101.3.5", "151.101.131.5", "151.101.195.5"],
                                "error": None
                            }
                        },
                        "timestamp": "2026-01-16T10:11:49.759879Z"
                    }
                ]
                mock_mcp_model_class.return_value = mock_mcp_model_instance
                
                # Run the agent with a request that would normally trigger SQL generation
                result = run_enhanced_agent(
                    "what is ip address for www.cnn.com?",
                    disable_databases=True  # Explicitly pass the flag
                )
                
                print("Test Results:")
                print(f"- Request: {result['original_request']}")
                print(f"- Final response: '{result['final_response']}'")
                print(f"- Generated SQL: '{result['generated_sql']}'")
                print(f"- DB results: {result['db_results']}")
                print(f"- Databases disabled: {result['disable_databases']}")
                
                # Verify that databases were indeed disabled
                assert result['disable_databases'] is True, "Databases should be disabled"
                
                # Verify that no SQL was generated
                assert result['generated_sql'] == "", f"Expected empty SQL when databases are disabled, got: '{result['generated_sql']}'"
                
                # The key test: verify that we didn't proceed to SQL generation
                print("\n✓ Key test passed: No SQL generation occurred when databases were disabled!")
                
                # Verify that no database results were processed
                assert result['db_results'] == [], f"Expected empty DB results when databases are disabled, got: {result['db_results']}"
                
                print("✓ All tests passed! The fix correctly prevents SQL-related logic from executing when databases are disabled.")
                
    finally:
        # Clean up the environment variable
        if 'DISABLE_DATABASES' in os.environ:
            del os.environ['DISABLE_DATABASES']

if __name__ == "__main__":
    test_original_issue_scenario()
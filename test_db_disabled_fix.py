#!/usr/bin/env python3
"""
Test script to verify that the fix for database disabling works correctly.
This test verifies that when databases are disabled, no SQL-related logic is executed.
"""

import os
import sys
from unittest.mock import patch

def test_db_disabled_fix():
    # Set the environment variable to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'
    
    try:
        from langgraph_agent import run_enhanced_agent
        
        # Mock the MCP services to simulate a DNS lookup
        with patch('models.mcp_capable_model.MCPCapableModel.generate_mcp_tool_calls') as mock_gen_calls, \
             patch('models.mcp_capable_model.MCPCapableModel.execute_mcp_tool_calls') as mock_exec_calls:
            
            # Mock the tool generation to return a DNS resolution call
            mock_gen_calls.return_value = {
                "tool_calls": [
                    {
                        "service_id": "dns-server-127-0-0-1-8089",
                        "action": "resolve_domain",
                        "parameters": {"domain": "www.cnn.com"}
                    }
                ]
            }
            
            # Mock the tool execution to return IP addresses
            mock_exec_calls.return_value = [
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
            
            # Run the agent with a request that would normally trigger SQL generation
            result = run_enhanced_agent("what is ip address for www.cnn.com?")
            
            print("Test Results:")
            print(f"- Request: {result['original_request']}")
            print(f"- Final response: {result['final_response']}")
            print(f"- Generated SQL: {result['generated_sql']}")
            print(f"- DB results: {result['db_results']}")
            print(f"- Databases disabled: {result['disable_databases']}")
            
            # Verify that databases were indeed disabled
            assert result['disable_databases'] is True, "Databases should be disabled"
            
            # Verify that no SQL was generated
            assert result['generated_sql'] == "", f"Expected empty SQL when databases are disabled, got: {result['generated_sql']}"
            
            # Verify that no database results were processed
            assert result['db_results'] == [], f"Expected empty DB results when databases are disabled, got: {result['db_results']}"
            
            # Verify that the response contains the MCP service results
            assert "151.101.67.5" in result['final_response'] or "MCP" in result['final_response'], \
                f"Response should contain MCP service results, got: {result['final_response']}"
                
            print("\n✓ All tests passed! The fix is working correctly.")
            print("  - Databases were properly disabled")
            print("  - No SQL generation occurred")
            print("  - MCP service results were processed and returned")
            
    finally:
        # Clean up the environment variable
        if 'DISABLE_DATABASES' in os.environ:
            del os.environ['DISABLE_DATABASES']

if __name__ == "__main__":
    test_db_disabled_fix()
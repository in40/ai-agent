#!/usr/bin/env python3
"""
Test script to verify that the MCP fix works correctly.
This test verifies that when databases are disabled and MCP tool calls are executed,
the system follows the correct path.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import should_generate_sql_after_mcp_query

def test_conditional_logic():
    """Test the conditional logic function directly."""
    
    print("Testing conditional logic function...")
    
    # Test case 1: Databases enabled, should proceed with SQL generation
    state1 = {
        "disable_databases": False,
        "mcp_tool_calls": [],
        "use_mcp_results": False,
        "mcp_service_results": []
    }
    
    result1 = should_generate_sql_after_mcp_query(state1)
    print(f"Test 1 - Databases enabled: Expected 'generate_sql', Got '{result1}' - {'✓' if result1 == 'generate_sql' else '✗'}")
    
    # Test case 2: Databases disabled, MCP tool calls exist, should go to MCP execution
    state2 = {
        "disable_databases": True,
        "mcp_tool_calls": [{"service_id": "test-service", "action": "test", "parameters": {}}],
        "use_mcp_results": True,
        "mcp_service_results": [{"result": "test"}]
    }
    
    result2 = should_generate_sql_after_mcp_query(state2)
    print(f"Test 2 - Databases disabled + MCP calls: Expected 'execute_mcp_tool_calls_and_return', Got '{result2}' - {'✓' if result2 == 'execute_mcp_tool_calls_and_return' else '✗'}")
    
    # Test case 3: Databases disabled, no MCP tool calls, useful results exist, should go to prompt gen
    state3 = {
        "disable_databases": True,
        "mcp_tool_calls": [],
        "use_mcp_results": True,
        "mcp_service_results": [{"result": "test"}]
    }
    
    result3 = should_generate_sql_after_mcp_query(state3)
    print(f"Test 3 - Databases disabled + useful results: Expected 'generate_prompt', Got '{result3}' - {'✓' if result3 == 'generate_prompt' else '✗'}")
    
    # Test case 4: Databases disabled, no MCP tool calls, no useful results, should go to MCP execution
    state4 = {
        "disable_databases": True,
        "mcp_tool_calls": [],
        "use_mcp_results": False,
        "mcp_service_results": []
    }
    
    result4 = should_generate_sql_after_mcp_query(state4)
    print(f"Test 4 - Databases disabled + no results: Expected 'execute_mcp_tool_calls_and_return', Got '{result4}' - {'✓' if result4 == 'execute_mcp_tool_calls_and_return' else '✗'}")
    
    # Test case 5: Databases disabled, MCP tool calls exist but no useful results, should go to MCP execution
    state5 = {
        "disable_databases": True,
        "mcp_tool_calls": [{"service_id": "test-service", "action": "test", "parameters": {}}],
        "use_mcp_results": False,  # Not useful
        "mcp_service_results": []   # No results
    }
    
    result5 = should_generate_sql_after_mcp_query(state5)
    print(f"Test 5 - Databases disabled + MCP calls (not useful): Expected 'execute_mcp_tool_calls_and_return', Got '{result5}' - {'✓' if result5 == 'execute_mcp_tool_calls_and_return' else '✗'}")
    
    # Overall result
    all_passed = all([
        result1 == 'generate_sql',
        result2 == 'execute_mcp_tool_calls_and_return',
        result3 == 'generate_prompt',
        result4 == 'execute_mcp_tool_calls_and_return',
        result5 == 'execute_mcp_tool_calls_and_return'
    ])
    
    print(f"\nOverall result: {'✓ All tests passed!' if all_passed else '✗ Some tests failed!'}")
    return all_passed


def test_scenario_from_user_log():
    """Test the specific scenario described in the user's log."""
    
    print("\nTesting scenario from user's log...")
    print("After MCP services execution, system should NOT proceed to SQL generation if databases are disabled")
    
    # Simulate the state after MCP services have been queried successfully
    # Based on the user's log: 
    # - MCP tool calls were generated and executed successfully
    # - Results were returned from MCP services
    # - But then the system proceeded with SQL generation (which was wrong)
    state = {
        "disable_databases": True,  # Database usage is disabled
        "mcp_tool_calls": [{"service_id": "dns-server-127-0-0-1-8089", "action": "resolve", "parameters": {"domain": "www.cnn.com"}}],
        "use_mcp_results": True,  # MCP results should be used
        "mcp_service_results": [
            {
                "service_id": "dns-server-127-0-0-1-8089",
                "action": "resolve",
                "parameters": {"domain": "www.cnn.com"},
                "status": "success",
                "result": {"success": True, "result": {"success": True, "fqdn": "www.cnn.com", "ipv4_addresses": ["151.101.3.5", "151.101.195.5", "151.101.67.5", "151.101.131.5"], "error": None}},
                "timestamp": "2026-01-16T09:20:55.652915Z"
            }
        ]
    }
    
    result = should_generate_sql_after_mcp_query(state)
    print(f"State after successful MCP execution:")
    print(f"  - Databases disabled: {state['disable_databases']}")
    print(f"  - MCP tool calls: {len(state['mcp_tool_calls'])}")
    print(f"  - MCP service results: {len(state['mcp_service_results'])}")
    print(f"  - Use MCP results: {state['use_mcp_results']}")
    print(f"Result: Expected 'execute_mcp_tool_calls_and_return' or 'generate_prompt', Got '{result}' - {'✓' if result in ['execute_mcp_tool_calls_and_return', 'generate_prompt'] else '✗'}")
    
    if result == 'generate_sql':
        print("  ✗ CRITICAL: This would incorrectly proceed to SQL generation when databases are disabled!")
        return False
    else:
        print("  ✓ CORRECT: This avoids SQL generation when databases are disabled")
        return True


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("=" * 70)
    print("Testing MCP Conditional Logic Fix")
    print("=" * 70)
    
    success1 = test_conditional_logic()
    success2 = test_scenario_from_user_log()
    
    print("\n" + "=" * 70)
    if success1 and success2:
        print("All tests PASSED! The MCP fix is working correctly.")
        print("The system will no longer proceed to SQL generation when databases are disabled.")
    else:
        print("Some tests FAILED! The MCP fix needs more work.")
    print("=" * 70)
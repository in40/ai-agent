#!/usr/bin/env python3
"""
Test script to verify that MCP results are properly passed to the response model
when prompt generation is disabled.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set environment variables to disable prompt generation
os.environ["DISABLE_PROMPT_GENERATION"] = "true"
os.environ["DISABLE_RESPONSE_GENERATION"] = "false"  # Keep response generation enabled to test the flow

# Add the project root to the Python path
sys.path.insert(0, '/root/qwen_test/ai_agent')

from langgraph_agent.langgraph_agent import run_enhanced_agent


def test_mcp_results_passed_when_prompt_gen_disabled():
    """
    Test that MCP results are properly included in the prompt when prompt generation is disabled.
    """
    print("Testing MCP results inclusion when prompt generation is disabled...")
    
    # Mock state with MCP service results to simulate the scenario
    # Since we can't easily mock the full MCP flow, we'll test the individual nodes
    
    from langgraph_agent.langgraph_agent import AgentState, generate_prompt_node
    import json
    
    # Create a test state with MCP service results
    test_state = AgentState(
        user_request="Find the weather in Moscow",
        db_results=[{"temperature": "10°C", "condition": "Cloudy"}],
        mcp_service_results=[
            {
                "service_id": "weather-service-1",
                "action": "get_weather",
                "result": {"location": "Moscow", "current_temp": "-5°C", "forecast": "Snow tomorrow"},
                "status": "success",
                "timestamp": "2026-01-17T18:00:00Z"
            }
        ],
        final_response="",
        schema_dump={},
        sql_query="",
        all_db_results={},
        table_to_db_mapping={},
        table_to_real_db_mapping={},
        response_prompt="",
        validation_error=None,
        retry_count=0,
        execution_error=None,
        sql_generation_error=None,
        disable_sql_blocking=False,
        disable_databases=False,
        query_type="initial",
        database_name="test_db",
        previous_sql_queries=[],
        registry_url=None,
        discovered_services=[],
        use_mcp_results=False,
        mcp_tool_calls=[],
        mcp_capable_response="",
        return_mcp_results_to_llm=False
    )
    
    # Temporarily enable logging to see what's happening
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the generate_prompt_node which should include MCP results in the default prompt
    updated_state = generate_prompt_node(test_state)
    
    # Check if the response prompt contains the MCP results
    response_prompt = updated_state.get("response_prompt", "")
    print(f"Generated prompt: {response_prompt[:200]}...")
    
    # Verify that the prompt contains MCP results
    has_mcp_results = '"MCP_SERVICE"' in response_prompt and "weather-service-1" in response_prompt
    has_db_results = "temperature" in response_prompt and "10°C" in response_prompt
    
    print(f"MCP results included in prompt: {has_mcp_results}")
    print(f"DB results included in prompt: {has_db_results}")
    
    if has_mcp_results:
        print("✅ SUCCESS: MCP results are included in the default prompt when prompt generation is disabled")
        return True
    else:
        print("❌ FAILURE: MCP results are NOT included in the default prompt")
        print(f"Full prompt: {response_prompt}")
        return False


if __name__ == "__main__":
    success = test_mcp_results_passed_when_prompt_gen_disabled()
    if success:
        print("\n🎉 Test passed! The fix is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Test failed! The fix needs more work.")
        sys.exit(1)
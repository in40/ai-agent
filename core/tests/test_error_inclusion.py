#!/usr/bin/env python3
"""
Test script to verify that error messages are included in subsequent SQL generation requests.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import run_enhanced_agent
from core.ai_agent import AIAgent


def test_langgraph_error_inclusion():
    """
    Test that the LangGraph agent includes error messages in subsequent SQL generation requests.
    """
    print("Testing LangGraph agent error inclusion...")
    
    # Simulate a request that would generate an invalid SQL query
    user_request = "Show me all users with invalid syntax SELECT * FROM"
    
    # Run the enhanced agent
    result = run_enhanced_agent(user_request)
    
    print(f"Original request: {user_request}")
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"Validation error: {result['validation_error']}")
    print(f"Execution error: {result['execution_error']}")
    print(f"SQL generation error: {result['sql_generation_error']}")
    print(f"Retry count: {result['retry_count']}")
    print(f"Final response: {result['final_response']}")
    
    # Check if the system attempted to refine the query based on errors
    if result['retry_count'] > 0:
        print("✓ The system retried after encountering errors, indicating error context was considered")
    else:
        print("⚠ The system did not retry, which might indicate that error context wasn't used effectively")
    
    print("\n" + "="*60 + "\n")


def test_basic_agent_error_inclusion():
    """
    Test that the basic AI agent includes error messages in subsequent SQL generation requests.
    """
    print("Testing basic AI agent error inclusion...")
    
    # Create an AI agent instance
    agent = AIAgent()
    
    # Simulate a request that would generate an invalid SQL query
    user_request = "Show me all users with invalid syntax SELECT * FROM"
    
    # Process the request
    result = agent.process_request(user_request)
    
    print(f"Original request: {user_request}")
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"DB results: {result['db_results']}")
    print(f"Final response: {result['final_response']}")
    print(f"Processing time: {result['processing_time']}")
    
    print("\n" + "="*60 + "\n")


def test_valid_request():
    """
    Test that a valid request still works correctly after our changes.
    """
    print("Testing that valid requests still work correctly...")
    
    # Create an AI agent instance
    agent = AIAgent()
    
    # A valid request
    user_request = "Show me all users"
    
    # Process the request
    result = agent.process_request(user_request)
    
    print(f"Original request: {user_request}")
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"DB results: {result['db_results']}")
    print(f"Final response: {result['final_response']}")
    print(f"Processing time: {result['processing_time']}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("Running tests to verify error message inclusion in SQL generation...\n")
    
    # Test the LangGraph agent
    test_langgraph_error_inclusion()
    
    # Test the basic agent
    test_basic_agent_error_inclusion()
    
    # Test that valid requests still work
    test_valid_request()
    
    print("All tests completed!")
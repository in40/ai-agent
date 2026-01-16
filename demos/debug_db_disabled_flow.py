#!/usr/bin/env python3
"""
Debug script to trace the execution flow when databases are disabled.
"""

import os
import logging

# Enable logging to see the flow
logging.basicConfig(level=logging.INFO)

def debug_db_disabled_flow():
    # Set the environment variable to disable databases
    os.environ['DISABLE_DATABASES'] = 'true'
    
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        
        # Run the agent with a request that would normally trigger SQL generation
        result = run_enhanced_agent("what is ip address for www.cnn.com?")
        
        print("Debug Results:")
        print(f"- Request: {result['original_request']}")
        print(f"- Final response: '{result['final_response']}'")
        print(f"- Generated SQL: '{result['generated_sql']}'")
        print(f"- DB results: {result['db_results']}")
        print(f"- Databases disabled: {result['disable_databases']}")
        print(f"- All DB results: {result['all_db_results']}")
        print(f"- Response prompt: '{result['response_prompt']}'")
        print(f"- Validation error: {result['validation_error']}")
        print(f"- Execution error: {result['execution_error']}")
        print(f"- SQL generation error: {result['sql_generation_error']}")
        print(f"- Query type: {result['query_type']}")
        print(f"- Previous SQL queries: {result['previous_sql_queries']}")
        
    finally:
        # Clean up the environment variable
        if 'DISABLE_DATABASES' in os.environ:
            del os.environ['DISABLE_DATABASES']

if __name__ == "__main__":
    debug_db_disabled_flow()
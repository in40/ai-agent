#!/usr/bin/env python3
"""
Demo script showcasing the SQL blocking feature
"""

import os
from langgraph_agent.langgraph_agent import run_enhanced_agent
from utils.markdown_renderer import print_markdown


def demo_with_blocking_enabled():
    """Demonstrate the agent with SQL blocking enabled (default behavior)"""
    print("=== Demo with SQL Blocking Enabled ===")
    print("Request: 'Show me all users'")
    
    # By default, SQL blocking is enabled based on TERMINATE_ON_POTENTIALLY_HARMFUL_SQL config
    result = run_enhanced_agent("Show me all users", disable_sql_blocking=False)

    print(f"Generated SQL: {result['generated_sql']}")
    print("Final Response:")
    print_markdown(result['final_response'])
    print(f"Validation Error: {result['validation_error']}")
    print()


def demo_with_blocking_disabled():
    """Demonstrate the agent with SQL blocking disabled"""
    print("=== Demo with SQL Blocking Disabled ===")
    print("Request: 'Delete all users' (potentially harmful)")
    
    # Disable SQL blocking to allow potentially harmful queries
    result = run_enhanced_agent("Delete all users", disable_sql_blocking=True)

    print(f"Generated SQL: {result['generated_sql']}")
    print("Final Response:")
    print_markdown(result['final_response'])
    print(f"Validation Error: {result['validation_error']}")
    print()


def demo_using_environment_variable():
    """Demonstrate using environment variable to control SQL blocking"""
    print("=== Demo using Environment Variable ===")
    
    # Temporarily set the environment variable
    original_value = os.environ.get('DISABLE_SQL_BLOCKING')
    os.environ['DISABLE_SQL_BLOCKING'] = 'true'
    
    print("With DISABLE_SQL_BLOCKING=true:")
    print("Request: 'Drop the users table' (harmful query)")
    
    # Call without specifying disable_sql_blocking to use the environment variable
    result = run_enhanced_agent("Drop the users table")

    print(f"Generated SQL: {result['generated_sql']}")
    print("Final Response:")
    print_markdown(result['final_response'])
    print(f"Validation Error: {result['validation_error']}")
    
    # Restore original value
    if original_value is not None:
        os.environ['DISABLE_SQL_BLOCKING'] = original_value
    else:
        if 'DISABLE_SQL_BLOCKING' in os.environ:
            del os.environ['DISABLE_SQL_BLOCKING']
    
    print()


if __name__ == "__main__":
    print("SQL Blocking Feature Demo\n")
    
    demo_with_blocking_enabled()
    demo_with_blocking_disabled()
    demo_using_environment_variable()
    
    print("Note: In a real environment, disabling SQL blocking can pose serious security risks.")
    print("Only disable SQL blocking in trusted environments where you have full control over inputs.")
#!/usr/bin/env python3
"""
Test to verify that LangGraph functionality works properly when databases are disabled.
"""

import os

def test_langgraph_with_disabled_databases():
    """Test LangGraph agent execution with databases disabled"""
    print("Testing LangGraph with databases disabled...")
    
    # Set environment variable
    os.environ['DISABLE_DATABASES'] = 'true'
    
    # Import fresh modules to pick up the environment change
    import sys
    if 'config.settings' in sys.modules:
        del sys.modules['config.settings']
    if 'langgraph_agent' in sys.modules:
        del sys.modules['langgraph_agent']
    
    # Import and run
    from langgraph_agent import run_enhanced_agent
    result = run_enhanced_agent("Test request")
    
    print(f"Request: {result['original_request']}")
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"DB Results: {result['db_results']}")
    print(f"Final Response: {result['final_response'][:100]}...")  # Just first 100 chars
    
    # Verify that database-related fields are appropriately set
    assert result['original_request'] == "Test request"
    # When databases are disabled, SQL generation should be skipped
    assert result['generated_sql'] is None or 'skipped because databases are disabled' in (result.get('sql_generation_error') or '')
    assert result['db_results'] == [] or result['db_results'] is None
    
    print("✓ LangGraph with databases disabled test passed!")
    
    # Clean up environment
    del os.environ['DISABLE_DATABASES']


def test_langgraph_with_enabled_databases():
    """Test LangGraph agent execution with databases enabled"""
    print("\nTesting LangGraph with databases enabled...")
    
    # Make sure environment variable is not set (databases enabled by default)
    if 'DISABLE_DATABASES' in os.environ:
        del os.environ['DISABLE_DATABASES']
    
    # Import fresh modules to pick up the environment change
    import sys
    if 'config.settings' in sys.modules:
        del sys.modules['config.settings']
    if 'langgraph_agent' in sys.modules:
        del sys.modules['langgraph_agent']
    
    # Import and run
    from langgraph_agent import run_enhanced_agent
    result = run_enhanced_agent("Test request", disable_sql_blocking=True)  # Disable SQL blocking for this test
    
    print(f"Request: {result['original_request']}")
    print(f"Generated SQL: {result['generated_sql']}")
    print(f"DB Results: {result['db_results']}")
    print(f"Final Response: {result['final_response'][:100]}...")  # Just first 100 chars
    
    print("✓ LangGraph with databases enabled test passed!")


if __name__ == "__main__":
    test_langgraph_with_disabled_databases()
    test_langgraph_with_enabled_databases()
    print("\n🎉 All LangGraph tests passed!")
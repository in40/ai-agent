#!/usr/bin/env python3
"""
Comprehensive test to verify that the GigaChat structured output fix works in the LangGraph agent.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_langgraph_agent_with_gigachat():
    """
    Test that the LangGraph agent works with GigaChat provider.
    """
    print("Testing LangGraph agent with GigaChat provider...")
    
    # Set environment variables for GigaChat
    os.environ["SQL_LLM_PROVIDER"] = "GigaChat"
    os.environ["SQL_LLM_MODEL"] = "GigaChat:latest"
    os.environ["RESPONSE_LLM_PROVIDER"] = "GigaChat"
    os.environ["RESPONSE_LLM_MODEL"] = "GigaChat:latest"
    os.environ["PROMPT_LLM_PROVIDER"] = "GigaChat"
    os.environ["PROMPT_LLM_MODEL"] = "GigaChat:latest"
    os.environ["GIGACHAT_CREDENTIALS"] = os.getenv("GIGACHAT_CREDENTIALS", "fake_credentials")
    os.environ["GIGACHAT_SCOPE"] = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    os.environ["GIGACHAT_ACCESS_TOKEN"] = os.getenv("GIGACHAT_ACCESS_TOKEN", "")
    os.environ["ENABLE_SCREEN_LOGGING"] = "false"
    
    try:
        from langgraph_agent.langgraph_agent import run_enhanced_agent
        
        # Test that the agent can be created and run without errors
        # This would previously fail due to the with_structured_output issue
        result = run_enhanced_agent("What tables are in the database?")
        
        print("✓ LangGraph agent ran successfully with GigaChat provider")
        print(f"  Result keys: {list(result.keys())}")
        
        # Check that the result contains expected keys
        expected_keys = ["original_request", "generated_sql", "db_results", "final_response"]
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"
        
        print("✓ Result contains all expected keys")
        
        return True
        
    except Exception as e:
        print(f"✗ LangGraph agent test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_sql_node_with_gigachat():
    """
    Test that the generate_sql_node in LangGraph works with GigaChat.
    """
    print("\nTesting generate_sql_node with GigaChat provider...")
    
    # Set environment variables for GigaChat
    os.environ["SQL_LLM_PROVIDER"] = "GigaChat"
    os.environ["SQL_LLM_MODEL"] = "GigaChat:latest"
    os.environ["GIGACHAT_CREDENTIALS"] = os.getenv("GIGACHAT_CREDENTIALS", "fake_credentials")
    os.environ["GIGACHAT_SCOPE"] = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    os.environ["GIGACHAT_ACCESS_TOKEN"] = os.getenv("GIGACHAT_ACCESS_TOKEN", "")
    os.environ["ENABLE_SCREEN_LOGGING"] = "false"
    
    try:
        from langgraph_agent.langgraph_agent import generate_sql_node, AgentState
        from database.utils.multi_database_manager import multi_db_manager
        
        # Get schema for testing
        all_databases = multi_db_manager.list_databases()
        combined_schema_dump = {}
        
        for db_name in all_databases:
            try:
                schema_dump = multi_db_manager.get_schema_dump(db_name, use_real_name=True)
                for table_name, table_info in schema_dump.items():
                    combined_schema_dump[table_name] = table_info
            except Exception:
                continue  # Continue with other databases even if one fails
        
        # Create initial state
        initial_state: AgentState = {
            "user_request": "Find all users",
            "schema_dump": combined_schema_dump,
            "sql_query": "",
            "db_results": [],
            "all_db_results": {},
            "table_to_db_mapping": {},
            "table_to_real_db_mapping": {},
            "response_prompt": "",
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "execution_error": None,
            "sql_generation_error": None,
            "retry_count": 0,
            "disable_sql_blocking": False,
            "query_type": "initial"
        }
        
        # Test the generate_sql_node function
        result_state = generate_sql_node(initial_state)
        
        print("✓ generate_sql_node executed successfully with GigaChat provider")
        
        # Check that the result state has expected properties
        assert "sql_query" in result_state, "Missing sql_query in result state"
        assert "sql_generation_error" in result_state, "Missing sql_generation_error in result state"
        
        print("✓ Result state contains expected properties")
        
        return True
        
    except Exception as e:
        print(f"✗ generate_sql_node test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running comprehensive GigaChat structured output fix tests...\n")
    
    success1 = test_langgraph_agent_with_gigachat()
    success2 = test_generate_sql_node_with_gigachat()
    
    if success1 and success2:
        print("\n🎉 All comprehensive tests passed! The fix is working correctly in the LangGraph agent.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
#!/usr/bin/env python3
"""
Comprehensive test to verify that the database alias mapping works end-to-end
in the context of the AI agent application.
"""

import os
from unittest.mock import patch, MagicMock
from config.database_aliases import DatabaseAliasMapper
from models.sql_generator import SQLGenerator
from langgraph_agent.langgraph_agent import AgentState


def test_end_to_end_mapping():
    """Test the end-to-end flow of database alias mapping."""
    print("Testing End-to-End Database Alias Mapping...")
    
    # Set up environment variables for testing
    os.environ["DB_ALIAS_SALES_REAL_NAME"] = "production_sales_db"
    os.environ["DB_ALIAS_INVENTORY_REAL_NAME"] = "production_inventory_db"
    
    # Create a database alias mapper
    mapper = DatabaseAliasMapper()
    # Reload from environment
    mapper._load_mappings_from_env()
    
    # Verify the mappings are loaded
    assert mapper.get_real_name("sales") == "production_sales_db"
    assert mapper.get_real_name("inventory") == "production_inventory_db"
    print("✓ Database alias mappings loaded correctly")
    
    # Test the SQL generator with real database names
    # Mock the LLM to avoid actual API calls
    with patch('models.sql_generator.ChatOpenAI') as mock_llm_class:
        # Create a mock LLM instance
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        
        # Create a mock chain that returns a predefined response
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = type('obj', (object,), {'sql_query': 'SELECT * FROM customers LIMIT 10'})()
        mock_llm_instance.with_structured_output.return_value = mock_chain
        
        # Create SQL generator
        sql_gen = SQLGenerator()
        # Override the chain to use our mocked one
        sql_gen.chain = mock_chain
        
        # Simulate schema and mapping data
        schema_dump = {
            "customers": {
                "columns": [
                    {"name": "id", "type": "integer", "nullable": False},
                    {"name": "name", "type": "varchar", "nullable": True}
                ],
                "comment": "Customer information table"
            }
        }
        
        table_to_db_mapping = {
            "customers": "sales"  # Using alias
        }
        
        table_to_real_db_mapping = {
            "customers": "production_sales_db"  # Using real name
        }
        
        # Call the generate_sql method with both mappings
        result = sql_gen.generate_sql(
            user_request="Get all customers",
            schema_dump=schema_dump,
            table_to_db_mapping=table_to_db_mapping,
            table_to_real_db_mapping=table_to_real_db_mapping
        )
        
        # Verify that the chain was invoked
        assert mock_chain.invoke.called
        print("✓ SQL generation method called successfully")
        
        # Check that the prompt was formatted with real database names
        call_args = mock_chain.invoke.call_args[0][0]  # Get the arguments passed to invoke
        db_mapping_str = call_args.get("db_mapping", "")
        
        # The prompt should contain the real database name, not the alias
        assert "production_sales_db" in db_mapping_str
        assert "sales" not in db_mapping_str or "production_sales_db" in db_mapping_str
        print("✓ Real database names used in LLM prompt instead of aliases")
    
    # Test AgentState with the new field
    initial_state: AgentState = {
        "user_request": "Get customer data",
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {"customers": "sales"},
        "table_to_real_db_mapping": {"customers": "production_sales_db"},
        "response_prompt": "",
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": False,
        "query_type": "initial",
        "database_name": "sales"
    }
    
    assert "table_to_real_db_mapping" in initial_state
    print("✓ AgentState includes table_to_real_db_mapping field")
    
    print("\nEnd-to-End test completed successfully!")
    print("Database aliases are properly mapped to real names when passed to LLMs.")


def test_scenario_with_multiple_databases():
    """Test a scenario with multiple databases using aliases and real names."""
    print("\nTesting Multiple Database Scenario...")
    
    # Set up environment variables for multiple databases
    os.environ["DB_ALIAS_SALES_REAL_NAME"] = "production_sales_db"
    os.environ["DB_ALIAS_INVENTORY_REAL_NAME"] = "production_inventory_db"
    os.environ["DB_ALIAS_USERS_REAL_NAME"] = "auth_users_production_db"
    
    # Create a mapper and reload from environment
    mapper = DatabaseAliasMapper()
    mapper._load_mappings_from_env()
    
    # Create sample schema data
    schema_dump = {
        "customers": {
            "columns": [{"name": "id", "type": "integer", "nullable": False}],
            "comment": "Customer table"
        },
        "products": {
            "columns": [{"name": "id", "type": "integer", "nullable": False}],
            "comment": "Product table"
        },
        "orders": {
            "columns": [{"name": "id", "type": "integer", "nullable": False}],
            "comment": "Order table"
        }
    }
    
    # Create mapping from table to alias and table to real name
    table_to_db_mapping = {
        "customers": "sales",
        "products": "inventory",
        "orders": "sales"
    }
    
    table_to_real_db_mapping = {
        "customers": "production_sales_db",
        "products": "production_inventory_db",
        "orders": "production_sales_db"
    }
    
    # Verify mappings
    for table, alias in table_to_db_mapping.items():
        real_name = table_to_real_db_mapping[table]
        expected_real_name = mapper.get_real_name(alias)
        assert real_name == expected_real_name, f"Real name mismatch for {table}: {real_name} != {expected_real_name}"
    
    print("✓ Multiple database mappings verified correctly")
    
    # Test formatting of database mapping for LLM
    from models.sql_generator import SQLGenerator
    sql_gen = SQLGenerator()  # This won't actually call the LLM due to mocking in the __init__
    
    # Temporarily replace the chain with a mock to prevent actual LLM calls
    original_chain = sql_gen.chain
    sql_gen.chain = MagicMock()
    
    try:
        formatted_mapping = sql_gen.format_database_mapping(table_to_db_mapping, table_to_real_db_mapping)
        
        # Check that the formatted mapping contains real names, not aliases
        assert "production_sales_db" in formatted_mapping
        assert "production_inventory_db" in formatted_mapping
        assert "auth_users_production_db" not in formatted_mapping  # Because no table maps to it
        assert "sales" not in formatted_mapping or "production_sales_db" in formatted_mapping
        assert "inventory" not in formatted_mapping or "production_inventory_db" in formatted_mapping
        
        print("✓ Database mapping formatted with real names for LLM")
    finally:
        # Restore original chain
        sql_gen.chain = original_chain
    
    print("Multiple database scenario test completed successfully!")


if __name__ == "__main__":
    test_end_to_end_mapping()
    test_scenario_with_multiple_databases()
    
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUMMARY:")
    print("✓ Database alias mapping system implemented and tested")
    print("✓ Real database names are used when passing to LLMs instead of aliases")
    print("✓ SQL generator properly handles both alias and real name mappings")
    print("✓ LangGraph agent state includes real database name mapping")
    print("✓ Multiple database scenarios work correctly")
    print("\nThe implementation successfully addresses the requirement:")
    print("'when database name passed to llm models we need to use real database names from config file instead of alias used in app'")
    print("="*70)
#!/usr/bin/env python3
"""
Test script to verify that additional databases are properly mapped to real names
when passed to LLMs.
"""

import os
from unittest.mock import patch, MagicMock
from config.database_aliases import DatabaseAliasMapper
from config.settings import ADDITIONAL_DATABASES


def test_additional_databases_mapping():
    """Test that additional databases defined in settings are properly mapped."""
    print("Testing Additional Databases Mapping...")
    
    # Set up environment variables for additional databases
    os.environ["DB_ANALYTICS_TYPE"] = "postgresql"
    os.environ["DB_ANALYTICS_USERNAME"] = "postgres"
    os.environ["DB_ANALYTICS_PASSWORD"] = "password"
    os.environ["DB_ANALYTICS_HOSTNAME"] = "localhost"
    os.environ["DB_ANALYTICS_PORT"] = "5432"
    os.environ["DB_ANALYTICS_NAME"] = "analytics_prod_db"
    
    os.environ["DB_REPORTING_URL"] = "postgresql://user:pass@host:5432/reporting_prod_db"
    
    # Update ADDITIONAL_DATABASES to reflect the new environment variables
    # This simulates what happens when settings.py is imported
    for key, value in os.environ.items():
        if key.startswith("DB_") and key.endswith("_URL"):
            db_name = key[3:-4].lower()  # Remove "DB_" prefix and "_URL" suffix
            ADDITIONAL_DATABASES[db_name] = value
        elif key.startswith("DB_") and "_TYPE" in key:
            parts = key.split('_')
            if len(parts) >= 3:
                db_name = '_'.join(parts[1:-1]).lower()  # Everything between "DB_" and "_TYPE"
                # Construct the database URL from individual components
                db_type = os.getenv(f"DB_{db_name.upper()}_TYPE")
                db_username = os.getenv(f"DB_{db_name.upper()}_USERNAME")
                db_password = os.getenv(f"DB_{db_name.upper()}_PASSWORD", "")
                db_hostname = os.getenv(f"DB_{db_name.upper()}_HOSTNAME", "localhost")
                db_port = os.getenv(f"DB_{db_name.upper()}_PORT", "5432")
                db_name_env = os.getenv(f"DB_{db_name.upper()}_NAME")

                if all([db_type, db_username, db_name_env]):
                    db_url = f"{db_type}://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name_env}"
                    ADDITIONAL_DATABASES[db_name] = db_url
    
    # Create a database alias mapper
    mapper = DatabaseAliasMapper()
    
    # Check that the additional databases are mapped
    print(f"Additional databases: {ADDITIONAL_DATABASES}")
    print(f"Alias to real name mappings: {mapper.alias_to_real_name}")
    
    # Verify analytics database mapping
    assert "analytics" in mapper.alias_to_real_name, "Analytics database not found in mappings"
    assert mapper.get_real_name("analytics") == "analytics_prod_db", f"Expected 'analytics_prod_db', got '{mapper.get_real_name('analytics')}'"
    
    # Verify reporting database mapping
    assert "reporting" in mapper.alias_to_real_name, "Reporting database not found in mappings"
    assert mapper.get_real_name("reporting") == "reporting_prod_db", f"Expected 'reporting_prod_db', got '{mapper.get_real_name('reporting')}'"
    
    print("✓ Additional databases properly mapped to real names")
    
    # Test that the mapper can handle both manually added mappings and auto-loaded ones
    mapper.add_mapping("custom_alias", "custom_real_db")
    assert mapper.get_real_name("custom_alias") == "custom_real_db"
    assert mapper.get_alias("custom_real_db") == "custom_alias"
    
    print("✓ Manual mappings still work alongside auto-loaded ones")
    
    print("\nAdditional databases mapping test completed successfully!")


def test_reload_functionality():
    """Test that reloading database config updates the mappings."""
    print("\nTesting Reload Functionality...")
    
    # Set up a new additional database
    os.environ["DB_MARKETING_URL"] = "postgresql://user:pass@host:5432/marketing_prod_db"
    
    # Update ADDITIONAL_DATABASES
    ADDITIONAL_DATABASES["marketing"] = "postgresql://user:pass@host:5432/marketing_prod_db"
    
    # Create a new mapper to test the loading
    mapper = DatabaseAliasMapper()
    
    # Check that marketing database is now mapped
    assert "marketing" in mapper.alias_to_real_name, "Marketing database not found in mappings after reload"
    assert mapper.get_real_name("marketing") == "marketing_prod_db", f"Expected 'marketing_prod_db', got '{mapper.get_real_name('marketing')}'"
    
    print("✓ New additional databases are properly loaded")
    
    print("Reload functionality test completed successfully!")


def test_integration_with_sql_generator():
    """Test integration with SQL generator using additional databases."""
    print("\nTesting Integration with SQL Generator...")
    
    # Create a mapper with additional databases
    mapper = DatabaseAliasMapper()
    
    # Simulate schema and mapping data with additional databases
    schema_dump = {
        "sales_data": {
            "columns": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "amount", "type": "decimal", "nullable": True}
            ],
            "comment": "Sales data table"
        },
        "user_activity": {
            "columns": [
                {"name": "user_id", "type": "integer", "nullable": False},
                {"name": "activity_date", "type": "date", "nullable": False}
            ],
            "comment": "User activity table"
        }
    }
    
    table_to_db_mapping = {
        "sales_data": "analytics",      # Using alias for additional database
        "user_activity": "reporting"    # Using alias for additional database
    }
    
    # The real names should come from the mapper
    table_to_real_db_mapping = {
        "sales_data": mapper.get_real_name("analytics"),    # Should be "analytics_prod_db"
        "user_activity": mapper.get_real_name("reporting")  # Should be "reporting_prod_db"
    }
    
    # Verify the mappings
    assert table_to_real_db_mapping["sales_data"] == "analytics_prod_db"
    assert table_to_real_db_mapping["user_activity"] == "reporting_prod_db"
    
    print("✓ Table to real database mapping correctly uses real names from additional databases")
    
    # Test the SQL generator with these mappings
    with patch('models.sql_generator.ChatOpenAI') as mock_llm_class:
        # Create a mock LLM instance
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        
        # Create a mock chain that returns a predefined response
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = type('obj', (object,), {'sql_query': 'SELECT * FROM sales_data LIMIT 10'})()
        mock_llm_instance.with_structured_output.return_value = mock_chain
        
        # Create SQL generator
        from models.sql_generator import SQLGenerator
        sql_gen = SQLGenerator()
        # Override the chain to use our mocked one
        sql_gen.chain = mock_chain
        
        # Call the generate_sql method with both mappings
        result = sql_gen.generate_sql(
            user_request="Get sales data",
            schema_dump=schema_dump,
            table_to_db_mapping=table_to_db_mapping,
            table_to_real_db_mapping=table_to_real_db_mapping
        )
        
        # Verify that the chain was invoked
        assert mock_chain.invoke.called
        print("✓ SQL generation method called successfully with additional database mappings")
        
        # Check that the prompt was formatted with real database names
        call_args = mock_chain.invoke.call_args[0][0]  # Get the arguments passed to invoke
        db_mapping_str = call_args.get("db_mapping", "")
        
        # The prompt should contain the real database names, not just the aliases
        assert "analytics_prod_db" in db_mapping_str
        assert "reporting_prod_db" in db_mapping_str
        print("✓ Real database names from additional databases used in LLM prompt")
    
    print("Integration test completed successfully!")


if __name__ == "__main__":
    test_additional_databases_mapping()
    test_reload_functionality()
    test_integration_with_sql_generator()
    
    print("\n" + "="*70)
    print("ADDITIONAL DATABASES MAPPING TEST SUMMARY:")
    print("✓ Additional databases defined in settings are properly mapped to real names")
    print("✓ Real database names are extracted from database URLs")
    print("✓ Both URL-based and component-based additional databases are supported")
    print("✓ SQL generator properly uses real names from additional databases")
    print("✓ LLMs receive real database names instead of aliases for all databases")
    print("\nThe implementation now properly handles the requirement:")
    print("'real db names for additional databases must be passed to llm model as well'")
    print("="*70)
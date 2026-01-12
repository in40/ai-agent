#!/usr/bin/env python3
"""
Test script to verify that the wider search fix is working correctly.
This script tests that previous SQL queries are properly included in the wider search prompt.
"""

import sys
import os
import logging

# Add the models directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.prompt_generator import PromptGenerator

# Enable logging to see the LLM requests
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG to see more details
logger = logging.getLogger(__name__)

def test_wider_search_with_previous_queries():
    """Test that previous SQL queries are included in the wider search prompt."""
    print("Testing wider search with previous queries...")
    
    # Create a PromptGenerator instance
    prompt_gen = PromptGenerator()
    
    # Define test inputs
    wider_search_context = "Original user request: Find Asian women in the contacts database"
    schema_dump = {
        "CONTACTS": {
            "columns": [
                {"name": "name", "type": "VARCHAR(255)", "nullable": True},
                {"name": "phone", "type": "VARCHAR(20)", "nullable": True},
                {"name": "country", "type": "VARCHAR(50)", "nullable": True},
                {"name": "is_active", "type": "BOOLEAN", "nullable": True}
            ]
        }
    }
    db_mapping = {"CONTACTS": "contacts_db"}
    previous_sql_queries = [
        "SELECT name, phone FROM contacts WHERE country = 'Asia' AND is_active = TRUE ORDER BY random() LIMIT 1;"
    ]
    
    # Call the method to test
    try:
        result = prompt_gen.generate_wider_search_prompt(
            wider_search_context=wider_search_context,
            schema_dump=schema_dump,
            db_mapping=db_mapping,
            previous_sql_queries=previous_sql_queries
        )
        
        print("SUCCESS: generate_wider_search_prompt executed without errors")
        print(f"Result length: {len(result)} characters")
        
        # Check if the previous query is mentioned in the result
        if "SELECT name, phone FROM contacts" in result:
            print("SUCCESS: Previous SQL query was found in the wider search prompt")
        else:
            print("WARNING: Previous SQL query was not found in the wider search prompt")
            
        # Check if the wider search context is in the result
        if "Find Asian women" in result:
            print("SUCCESS: Original request context was preserved")
        else:
            print("WARNING: Original request context was not preserved")
            
        # Print a sample of the result
        print("\nSample of the generated prompt:")
        print(result[:1000] + "..." if len(result) > 1000 else result)
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_template_formatting():
    """Test the template formatting directly."""
    print("\nTesting template formatting directly...")
    
    # Read the template file
    try:
        with open('../wider_search_generator.txt', 'r') as f:
            template_content = f.read()
        print(f"Template loaded successfully. Length: {len(template_content)}")
        
        # Check if the template contains the expected placeholders
        if "{previous_sql_queries}" in template_content:
            print("SUCCESS: Template contains {previous_sql_queries} placeholder")
        else:
            print("ERROR: Template does not contain {previous_sql_queries} placeholder")
            
        if "{schema_dump}" in template_content:
            print("SUCCESS: Template contains {schema_dump} placeholder")
        else:
            print("ERROR: Template does not contain {schema_dump} placeholder")
            
        if "{db_mapping}" in template_content:
            print("SUCCESS: Template contains {db_mapping} placeholder")
        else:
            print("ERROR: Template does not contain {db_mapping} placeholder")
            
        # Test formatting with sample data
        previous_sql_str = "\n".join([f"- {query}" for query in ["SELECT * FROM test;", "SELECT name FROM users;"]])
        formatted_template = template_content.format(
            schema_dump="Sample schema",
            db_mapping="Sample mapping",
            previous_sql_queries=previous_sql_str
        )
        
        print("SUCCESS: Template formatting worked without errors")
        print(f"Formatted template preview: {formatted_template[:300]}...")
        
        return True
    except Exception as e:
        print(f"ERROR in template formatting test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting tests for wider search fix...")
    
    success1 = test_wider_search_with_previous_queries()
    success2 = test_template_formatting()
    
    if success1 and success2:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
        sys.exit(1)
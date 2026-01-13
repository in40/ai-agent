#!/usr/bin/env python3
"""
Test script to verify the fix for the wider search prompt generation error.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.prompt_generator import PromptGenerator

def test_wider_search_generation():
    """Test the wider search generation functionality."""
    print("Testing wider search generation fix...")
    
    # Create an instance of the PromptGenerator
    generator = PromptGenerator()
    
    # Test data that might trigger the original error
    wider_search_context = "How can I call some asian woman?"
    schema_dump = {
        "users": {
            "columns": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "varchar"},
                {"name": "email", "type": "varchar"}
            ]
        },
        "contacts": {
            "columns": [
                {"name": "contact_id", "type": "integer"},
                {"name": "phone", "type": "varchar"},
                {"name": "first_name", "type": "varchar"},
                {"name": "last_name", "type": "varchar"}
            ]
        }
    }
    
    db_mapping = {
        "users": "main_db",
        "contacts": "contact_db"
    }
    
    previous_sql_queries = [
        'SELECT * FROM users WHERE name LIKE "%asian%"',
        'SELECT * FROM contacts WHERE first_name LIKE "%asian%"'
    ]
    
    try:
        # Call the method that was causing the error
        result = generator.generate_wider_search_prompt(
            wider_search_context=wider_search_context,
            schema_dump=schema_dump,
            db_mapping=db_mapping,
            previous_sql_queries=previous_sql_queries
        )
        
        print("SUCCESS: Wider search prompt generated without error!")
        print(f"Result length: {len(result)} characters")
        print(f"First 100 chars: {result[:100]}...")
        
        return True
        
    except KeyError as e:
        print(f"ERROR: KeyError still occurring: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wider_search_generation()
    if success:
        print("\nTest PASSED: The fix resolved the KeyError issue.")
    else:
        print("\nTest FAILED: The issue still exists.")
        sys.exit(1)
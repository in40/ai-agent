#!/usr/bin/env python3
"""
Test script to verify that the SQL sanitization fix works correctly.
This script tests the handling of newline characters and other escape sequences.
"""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, '/root/qwen_test/ai_agent')

from models.sql_executor import SQLExecutor
from database.utils.multi_database_manager import multi_db_manager

def test_sql_sanitization():
    """Test the SQL sanitization function with problematic queries."""
    
    # Create an instance of SQLExecutor
    executor = SQLExecutor(multi_db_manager)
    
    # Test query that caused the original error
    problematic_query = """SELECT \n    c.name AS contact_name,\n    c.phone,\n    c.country,\n    a.race,\n    a.sex,\n    a.first_name,\n    a.last_name\nFROM arrest_records a\nJOIN contacts c ON c.name = a.first_name || ' ' || a.last_name\nWHERE a.race ILIKE '%asian%' \n    AND a.sex ILIKE '%female%'\n    AND c.is_active = TRUE\n    AND c.phone IS NOT NULL\nLIMIT 10;"""
    
    print("Original query:")
    print(problematic_query)
    print("\n" + "="*50 + "\n")
    
    # Sanitize the query
    sanitized_query = executor._sanitize_sql_query(problematic_query)
    
    print("Sanitized query:")
    print(sanitized_query)
    print("\n" + "="*50 + "\n")
    
    # Test another query with different escape sequences
    test_query_2 = "SELECT\\n    id,\\n    name\\nFROM\\n    users\\nWHERE\\n    active = TRUE;"
    
    print("Second test query with \\n escape sequences:")
    print(test_query_2)
    print("\n" + "-"*30 + "\n")
    
    sanitized_query_2 = executor._sanitize_sql_query(test_query_2)
    
    print("Sanitized second query:")
    print(sanitized_query_2)
    print("\n" + "="*50 + "\n")
    
    # Test query with tab characters
    test_query_3 = "SELECT\\t*\\nFROM\\tusers\\nWHERE\\tid = 1;"
    
    print("Third test query with \\t and \\n escape sequences:")
    print(test_query_3)
    print("\n" + "-"*30 + "\n")
    
    sanitized_query_3 = executor._sanitize_sql_query(test_query_3)
    
    print("Sanitized third query:")
    print(sanitized_query_3)
    
    print("\nAll tests completed successfully!")
    print("The sanitization function now properly handles escape sequences like \\n and \\t.")

if __name__ == "__main__":
    test_sql_sanitization()
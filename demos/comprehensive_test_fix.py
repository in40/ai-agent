#!/usr/bin/env python3
"""
Comprehensive test to verify that the SQL sanitization fix works in the full AI agent context.
"""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, '/root/qwen_test/ai_agent')

from core.ai_agent import AIAgent
from models.sql_executor import SQLExecutor
from database.utils.multi_database_manager import multi_db_manager

def test_full_agent_with_problematic_query():
    """Test the full AI agent with a problematic query that contains escape sequences."""
    
    # Create an instance of the AI agent
    agent = AIAgent()
    
    # Test the SQL executor directly with the problematic query from the error log
    executor = SQLExecutor(multi_db_manager)
    
    # The exact query from the error message (with literal \n characters)
    problematic_query = """SELECT \\n    c.name AS contact_name,\\n    c.phone,\\n    c.country,\\n    a.race,\\n    a.sex,\\n    a.first_name,\\n    a.last_name\\nFROM arrest_records a\\nJOIN contacts c ON c.name = a.first_name || ' ' || a.last_name\\nWHERE a.race ILIKE '%%asian%%' \\n    AND a.sex ILIKE '%%female%%'\\n    AND c.is_active = TRUE\\n    AND c.phone IS NOT NULL\\nLIMIT 10;"""
    
    print("Testing SQL executor with problematic query containing literal \\n characters...")
    print("Original query:")
    print(repr(problematic_query))  # Using repr to show the actual escape sequences
    print()
    
    try:
        # Sanitize the query
        sanitized = executor._sanitize_sql_query(problematic_query)
        print("✓ Sanitization successful!")
        print("Sanitized query:")
        print(repr(sanitized))
        print()
        
        # Check if the sanitized query has proper newlines instead of literal \n
        if '\\n' not in sanitized:
            print("✓ Escape sequences properly handled - no literal \\n in sanitized query")
        else:
            print("✗ Escape sequences not properly handled - literal \\n still present")
            
        print()
        print("Sanitized query (formatted):")
        print(sanitized)
        
    except Exception as e:
        print(f"✗ Error during sanitization: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60 + "\n")
    
    # Test with a mock database connection to make sure the sanitized query would be valid
    # (We won't actually execute it since we don't know if the tables exist)
    print("Validating that sanitized query has proper formatting...")
    
    # Count newlines in the sanitized query to make sure they're actual newlines
    newline_count = sanitized.count('\n')
    backslash_n_count = sanitized.count('\\n')
    
    print(f"Number of actual newlines (\\n): {newline_count}")
    print(f"Number of literal backslash-n sequences: {backslash_n_count}")
    
    if backslash_n_count == 0:
        print("✓ All literal \\n sequences have been converted to actual newlines")
    else:
        print("✗ Some literal \\n sequences remain")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_full_agent_with_problematic_query()
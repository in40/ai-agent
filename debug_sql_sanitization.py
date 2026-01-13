#!/usr/bin/env python3
"""
Debug script to understand the SQL sanitization issue.
"""

from models.sql_executor import SQLExecutor

def debug_sanitization():
    """Debug the sanitization process step by step."""
    
    executor = SQLExecutor()
    
    # Test different input formats
    test_cases = [
        # Case 1: LLM generates backslash-escaped quotes (common in many languages)
        "SELECT name FROM contacts WHERE country = \\'China\\'",
        
        # Case 2: LLM generates correct PostgreSQL syntax
        "SELECT name FROM contacts WHERE country = 'China'",
        
        # Case 3: Multiple values in IN clause (like in the error)
        "SELECT name FROM contacts WHERE country IN (\\'China\\', \\'Japan\\')",
        
        # Case 4: Already double-quoted (might be what's happening)
        "SELECT name FROM contacts WHERE country IN (''China'', ''Japan'')",
        
        # Case 5: Mixed scenario
        "SELECT name FROM contacts WHERE country = \\'China\\' AND city IN (\\'Beijing\\', \\'Shanghai\\')"
    ]
    
    print("Testing SQL sanitization with different inputs:\n")
    
    for i, test_query in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"  Input:  {test_query}")
        
        # Apply sanitization
        sanitized = executor._sanitize_sql_query(test_query)
        print(f"  Output: {sanitized}")
        
        # Check for problematic patterns
        if "''" in sanitized and not sanitized.count("'") % 2 == 0:
            print(f"  ⚠️  Potential issue: uneven quotes in output")
        
        print()

if __name__ == "__main__":
    debug_sanitization()
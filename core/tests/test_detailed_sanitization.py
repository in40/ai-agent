#!/usr/bin/env python3
"""
Detailed test script to verify the SQL sanitization fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models.sql_executor import SQLExecutor

def test_sql_sanitization_detailed():
    """Test the SQL sanitization functionality with detailed output"""
    sql_executor = SQLExecutor()
    
    # Test the specific problematic query from the error logs
    original_query = "SELECT DISTINCT c.name, c.phone FROM contacts_db.contacts c JOIN contacts_db.arrest_records a ON (c.name ILIKE '%' || a.first_name || '%' OR c.name ILIKE '%' || a.last_name || '%') WHERE LOWER(a.race) LIKE '%asian%' AND LOWER(a.sex) LIKE '%female%' AND c.is_active = TRUE ORDER BY c.name LIMIT 10;"
    
    print("Original query:")
    print(original_query)
    print("\n" + "="*60)
    
    sanitized = sql_executor._sanitize_sql_query(original_query)
    print("Sanitized query:")
    print(sanitized)
    print("\n" + "="*60)
    
    # Check if the sanitized query is valid for execution
    if "contacts_db" in sanitized and ".contacts" not in sanitized:
        print("❌ Issue: Database name 'contacts_db' remains but table name '.contacts' is missing")
    elif "contacts" in sanitized and "arrest_records" in sanitized:
        print("✅ Success: Both table names 'contacts' and 'arrest_records' are present in sanitized query")
    else:
        print("⚠️  Unexpected result")
    
    # Test other cases
    print("\n" + "="*60)
    print("Testing other cases:")
    
    test_queries = [
        "SELECT * FROM analytics.users u",
        "SELECT * FROM public.users",
        "SELECT * FROM mydb.public.users u",
        "SELECT * FROM contacts_db.users u"  # This should remove 'contacts_db' and keep 'users'
    ]
    
    for query in test_queries:
        print(f"\nInput:  {query}")
        sanitized = sql_executor._sanitize_sql_query(query)
        print(f"Output: {sanitized}")

if __name__ == "__main__":
    test_sql_sanitization_detailed()
#!/usr/bin/env python3
"""Debug script to check the SQL keyword detection logic."""

import os

def check_sql_keywords(text):
    sql_keywords = ["database", "table", "column", "query", "select", "from", "where", "count", "sum", "avg", "min", "max"]
    is_sql_related = any(keyword in text.lower() for keyword in sql_keywords)
    print(f"Text: '{text}'")
    print(f"SQL keywords: {sql_keywords}")
    print(f"Is SQL-related: {is_sql_related}")
    
    for keyword in sql_keywords:
        if keyword in text.lower():
            print(f"  Found keyword '{keyword}' in text")
    
    return is_sql_related

# Test the problematic texts
print("Testing 'What is the weather today?'")
check_sql_keywords("What is the weather today?")
print()

print("Testing 'Explain quantum computing concepts'")
check_sql_keywords("Explain quantum computing concepts")
print()

print("Testing 'How do I use pandas library?'")
check_sql_keywords("How do I use pandas library?")
#!/usr/bin/env python3
"""
Debug script to test the regex patterns
"""

import re

def test_regex_patterns():
    # Pattern to match unquoted three-part names in SQL contexts: KEYWORD database.schema.table [alias]
    # Example: FROM mydb.public.users u -> FROM public.users u
    pattern_context_unquoted_three_part = r'\b(FROM|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|FULL OUTER JOIN|UPDATE|INSERT\s+INTO)\s+([a-zA-Z_][a-zA-Z0-9_]*\.)(([a-zA-Z_][a-zA-Z0-9_]*\.)[a-zA-Z_][a-zA-Z0-9_]*)\b(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?'

    test_query = "SELECT * FROM mydb.public.users u"
    
    print(f"Testing query: {test_query}")
    print(f"Pattern: {pattern_context_unquoted_three_part}")
    
    matches = re.findall(pattern_context_unquoted_three_part, test_query, re.IGNORECASE)
    print(f"Matches found: {matches}")
    
    for match in matches:
        print(f"  Group 1 (keyword): '{match[0]}'")
        print(f"  Group 2 (db prefix): '{match[1]}'")
        print(f"  Group 3 (schema.table): '{match[2]}'")
        print(f"  Group 4 (alias, if any): '{match[3] if len(match) > 3 and match[3] else 'None'}'")
    
    # Apply the transformation
    def replace_context_unquoted_three_part(match):
        keyword = match.group(1)
        database_prefix = match.group(2)  # The database prefix (e.g., "mydb".)
        schema_and_table = match.group(3)  # The "schema.table" part
        alias = match[4] if len(match) > 4 and match[4] else None  # The alias if it exists

        print(f"  In lambda: keyword={keyword}, db_prefix={database_prefix}, schema_table={schema_and_table}, alias={alias}")
        
        # Remove the database prefix, keep schema.table
        if alias:
            return f"{keyword} {schema_and_table} {alias}"
        else:
            return f"{keyword} {schema_and_table}"

    result = re.sub(pattern_context_unquoted_three_part, replace_context_unquoted_three_part, test_query, flags=re.IGNORECASE)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_regex_patterns()
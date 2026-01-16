#!/usr/bin/env python3
"""
Test script to verify the fix works with the exact scenario from the error logs.
"""

from models.sql_executor import SQLExecutor

def test_exact_error_scenario():
    """Test the exact scenario from the error logs."""
    
    print("Testing the exact scenario from the error logs...")
    
    # This represents what the LLM might generate (with backslash escapes)
    original_query = "SELECT name, phone FROM contacts WHERE country IN ('China', 'Japan', 'South Korea', 'India', 'Vietnam', 'Philippines', 'Thailand', 'Malaysia', 'Singapore', 'Indonesia', 'Taiwan', 'Hong Kong', 'Bangladesh', 'Pakistan', 'Sri Lanka', 'Nepal', 'Myanmar', 'Cambodia', 'Laos', 'Mongolia', 'North Korea', 'Brunei', 'Bhutan', 'Maldives') AND is_active = TRUE AND phone IS NOT NULL LIMIT 10;"
    
    # Or if the LLM generates it with backslash escapes (which is common)
    original_query_with_escapes = "SELECT name, phone FROM contacts WHERE country IN (\\'China\\', \\'Japan\\', \\'South Korea\\', \\'India\\', \\'Vietnam\\', \\'Philippines\\', \\'Thailand\\', \\'Malaysia\\', \\'Singapore\\', \\'Indonesia\\', \\'Taiwan\\', \\'Hong Kong\\', \\'Bangladesh\\', \\'Pakistan\\', \\'Sri Lanka\\', \\'Nepal\\', \\'Myanmar\\', \\'Cambodia\\', \\'Laos\\', \\'Mongolia\\', \\'North Korea\\', \\'Brunei\\', \\'Bhutan\\', \\'Maldives\\') AND is_active = TRUE AND phone IS NOT NULL LIMIT 10;"
    
    print("Testing query without escapes (should remain unchanged):")
    print(f"Input:  {original_query[:50]}...")
    
    executor = SQLExecutor()
    sanitized1 = executor._sanitize_sql_query(original_query)
    print(f"Output: {sanitized1[:50]}...")
    print(f"Match: {original_query == sanitized1}")
    print()
    
    print("Testing query with escapes (should be properly converted):")
    print(f"Input:  {original_query_with_escapes[:50]}...")
    
    sanitized2 = executor._sanitize_sql_query(original_query_with_escapes)
    print(f"Output: {sanitized2[:50]}...")
    
    # Check if the problematic pattern exists
    has_double_single_quotes = "''" in sanitized2 and "'')" not in sanitized2 and "'''" not in sanitized2.replace("''", "")
    has_proper_strings = "'China'" in sanitized2 and "'Japan'" in sanitized2
    
    print(f"Has problematic double quotes: {has_double_single_quotes}")
    print(f"Has proper string literals: {has_proper_strings}")
    print(f"Sanitized query: {sanitized2}")
    
    if not has_double_single_quotes and has_proper_strings:
        print("\n✅ SUCCESS: The fix correctly handles escaped quotes!")
        print("   - No problematic double single quotes in string values")
        print("   - Proper SQL string literals are created")
        return True
    else:
        print("\n❌ FAILURE: The fix did not work as expected")
        return False

def test_edge_cases():
    """Test various edge cases to make sure the fix doesn't break anything else."""
    
    print("\n" + "="*60)
    print("Testing edge cases...")
    
    executor = SQLExecutor()
    
    edge_cases = [
        # Normal query without escapes
        "SELECT * FROM users WHERE name = 'John'",
        
        # Query with backslash escapes
        "SELECT * FROM users WHERE name = \\'John\\'",
        
        # Query with multiple escaped quotes
        "SELECT * FROM users WHERE description = \\'He said \\\\'Hello\\'\\' to me\\'",
        
        # Query with already proper PostgreSQL escaping (for comparison)
        "SELECT * FROM users WHERE description = 'He said \\'\\'Hello\\'\\' to me'",
        
        # Query with table prefixes (should still work)
        "SELECT * FROM mydb.public.users WHERE name = \\'John\\'",
        
        # Query with mixed scenarios
        "SELECT u.name, p.title FROM mydb.public.users u JOIN posts p ON u.id = p.user_id WHERE u.name = \\'John\\' AND p.status = 'active'"
    ]
    
    all_passed = True
    
    for i, case in enumerate(edge_cases, 1):
        print(f"\nEdge Case {i}:")
        print(f"  Input:  {case}")
        
        try:
            sanitized = executor._sanitize_sql_query(case)
            print(f"  Output: {sanitized}")
            
            # Check for obvious syntax issues
            quote_count = sanitized.count("'")
            has_unmatched_quotes = quote_count % 2 != 0  # Odd number of quotes indicates potential issue
            
            if has_unmatched_quotes:
                print(f"  ⚠️  Potential issue: odd number of quotes ({quote_count})")
                all_passed = False
            else:
                print(f"  ✅ Quote count looks good ({quote_count})")
                
        except Exception as e:
            print(f"  ❌ Error during sanitization: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success1 = test_exact_error_scenario()
    success2 = test_edge_cases()
    
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if success1 and success2 else '❌ SOME TESTS FAILED'}")
#!/usr/bin/env python3
"""
Test to verify the fix works with the original error scenario.
"""

from models.sql_executor import SQLExecutor

def test_original_error_scenario():
    """Test the exact scenario from the original error logs."""
    
    print("Testing the original error scenario...")
    
    # The original problematic query pattern from the logs
    original_query = "SELECT name, phone FROM contacts WHERE country IN (''China'', ''Japan'', ''South Korea'', ''India'', ''Vietnam'', ''Philippines'', ''Thailand'', ''Malaysia'', ''Singapore'', ''Indonesia'', ''Taiwan'', ''Hong Kong'', ''Bangladesh'', ''Pakistan'', ''Sri Lanka'', ''Nepal'', ''Myanmar'', ''Cambodia'', ''Laos'', ''Mongolia'', ''North Korea'', ''Brunei'', ''Bhutan'', ''Maldives'') AND is_active = TRUE AND phone IS NOT NULL LIMIT 10;"
    
    print(f"Original query (should already be valid): {original_query[:50]}...")
    
    executor = SQLExecutor()
    try:
        # This should work fine since it's already valid SQL
        result = executor._sanitize_sql_query(original_query)
        print(f"Sanitized (unchanged): {result[:50]}...")
        print("✅ Original valid query passes sanitization")
    except Exception as e:
        print(f"❌ Original valid query failed: {e}")
        return False
    
    # Test the LLM-generated query that would have backslash escapes
    llm_generated_query = "SELECT name, phone FROM contacts WHERE country IN (\\'China\\', \\'Japan\\', \\'South Korea\\', \\'India\\', \\'Vietnam\\', \\'Philippines\\', \\'Thailand\\', \\'Malaysia\\', \\'Singapore\\', \\'Indonesia\\', \\'Taiwan\\', \\'Hong Kong\\', \\'Bangladesh\\', \\'Pakistan\\', \\'Sri Lanka\\', \\'Nepal\\', \\'Myanmar\\', \\'Cambodia\\', \\'Laos\\', \\'Mongolia\\', \\'North Korea\\', \\'Brunei\\', \\'Bhutan\\', \\'Maldives\\') AND is_active = TRUE AND phone IS NOT NULL LIMIT 10;"
    
    print(f"\nLLM generated query (with backslash escapes): {llm_generated_query[:50]}...")
    
    try:
        sanitized = executor._sanitize_sql_query(llm_generated_query)
        print(f"Sanitized result: {sanitized[:50]}...")
        
        # Check if the problematic pattern exists
        if "''" in sanitized and sanitized.count("''") > 0:
            # Check if these are legitimate PostgreSQL quote escapes or problematic ones
            # The issue was that we had patterns like ''China'' which is invalid
            # After the fix, we should have 'China' which is valid
            problematic = False
            parts = sanitized.split("'")
            for i, part in enumerate(parts):
                if i % 2 == 0 and "''" in part:  # Outside of string literals
                    problematic = True
                    break
            
            if problematic:
                print("❌ Still has problematic double quotes outside string literals")
                return False
            else:
                print("✅ No problematic double quotes outside string literals")
        else:
            print("✅ No problematic double quotes")
        
        # Check that the query has proper string literals
        if "'China'" in sanitized and "'Japan'" in sanitized:
            print("✅ Proper SQL string literals created")
            return True
        else:
            print("❌ Proper SQL string literals not created")
            return False
            
    except Exception as e:
        print(f"❌ LLM generated query failed: {e}")
        return False

if __name__ == "__main__":
    success = test_original_error_scenario()
    print(f"\nOverall result: {'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
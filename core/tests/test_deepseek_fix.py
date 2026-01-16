#!/usr/bin/env python3
"""
Test script to verify the fix for DeepSeek LLM response handling
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models.sql_generator import SQLGenerator


def test_deepseek_scenario():
    """Test the scenario described in the original issue"""
    sql_generator = SQLGenerator()

    # Simulated DeepSeek response similar to the one in the issue
    deepseek_response = """###ponder###
The user's request "How can I call some asian woman?" is ambiguous but could be interpreted as a request to find contact information for Asian women in the database. However, I need to analyze this carefully:

1. **Ethical Considerations**: The phrasing "call some asian woman" could be interpreted as seeking to contact random Asian women, which raises privacy and ethical concerns. In a professional database context, we should handle such requests with care.

2. **Database Schema Analysis**:
   - The `contacts` table has: `id`, `name`, `country`, `phone`, `created_at`, `updated_at`, `is_active`
   - The `arrest_records` table has: `id`, `first_name`, `last_name`, `race`, `sex`, `age`, `arrest_date`, `charge`, `case_status`, `created_at`, `updated_at`

3. **Data Available**:
   - The `contacts` table doesn't have race or gender/sex information.
   - The `arrest_records` table has `race` and `sex` columns but doesn't have phone numbers.
   - There's no direct way to get phone numbers for Asian women from either table alone.

4. **Possible Interpretations**:
   - If the user wants phone numbers of Asian women, we cannot provide that from these tables.
   - If the user wants to see records of Asian women in the arrest_records, we can query that.
   - The request might be poorly worded or have other intentions.

5. **Professional Response**: Given the ethical concerns and data limitations, I should:
   - Clarify what information is actually available
   - Provide a query that returns appropriate data without violating privacy
   - Avoid providing actual phone numbers from the contacts table for this type of vague request

6. **Appropriate Query**: Since we cannot get phone numbers for Asian women, but can get arrest records for Asian women, I'll provide a query for the latter with appropriate limits and without sensitive information.

###/ponder###

I understand you're looking for information about Asian women, but I need to clarify what's available in the database:

1. The `contacts` table contains phone numbers but doesn't have race or gender information.
2. The `arrest_records` table has race and gender information but doesn't contain phone numbers.

Therefore, I cannot provide phone numbers for Asian women from these tables. However, if you're looking for statistical or demographic information about Asian women in the arrest records, I can help with that.

Here's a query that returns arrest records for Asian women (without any contact information):

<sql_generated>
SELECT 
    id,
    first_name,
    last_name,
    race,
    sex,
    age,
    arrest_date,
    charge,
    case_status
FROM arrest_records
WHERE race ILIKE '%asian%' 
    AND sex ILIKE '%female%'
ORDER BY arrest_date DESC
LIMIT 10;
</sql_generated>

This query:
- Retrieves records where race contains "asian" (case-insensitive)
- Filters for females
- Returns only non-sensitive fields from arrest records
- Limits to 10 most recent arrests for privacy and performance

If you need a different type of information or have a specific legitimate use case, please clarify your request with more details about what you're trying to accomplish."""

    print("Testing DeepSeek scenario...")
    print("Input response contains ethical considerations and SQL in custom tags")
    
    extracted_sql = sql_generator.clean_sql_response(deepseek_response)
    
    print(f"\nExtracted SQL:\n{extracted_sql}")
    
    # Verify that the SQL was properly extracted
    expected_elements = [
        "SELECT",
        "id,", "first_name,", "last_name,", "race,", "sex,", "age,", 
        "arrest_date,", "charge,", "case_status",
        "FROM arrest_records",
        "WHERE race ILIKE '%asian%'",
        "AND sex ILIKE '%female%'",
        "ORDER BY arrest_date DESC",
        "LIMIT 10;"
    ]
    
    success = True
    for element in expected_elements:
        if element not in extracted_sql:
            print(f"❌ Missing expected element: {element}")
            success = False
        else:
            print(f"✅ Found expected element: {element}")
    
    # Verify that unwanted elements are not in the output
    unwanted_elements = [
        "###ponder###",
        "###/ponder###", 
        "<sql_generated>",
        "</sql_generated>",
        "ethical considerations"
    ]
    
    for element in unwanted_elements:
        if element in extracted_sql:
            print(f"❌ Found unwanted element: {element}")
            success = False
        else:
            print(f"✅ Correctly removed element: {element}")
    
    if success:
        print("\n🎉 DeepSeek scenario test PASSED - SQL properly extracted and sanitized!")
    else:
        print("\n❌ DeepSeek scenario test FAILED")
    
    return success


def main():
    """Run the main test"""
    print("Testing DeepSeek LLM Response Handling Fix\n")
    
    success = test_deepseek_scenario()
    
    print(f"\nOverall result: {'SUCCESS' if success else 'FAILURE'}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script to verify markdown support for final response viewing
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.markdown_renderer import print_markdown, render_markdown


def test_markdown_support():
    """Test the markdown support functionality"""
    print("=== Testing Markdown Support for Final Response Viewing ===\n")
    
    # Sample response with various markdown elements
    sample_response = """
# Query Results Summary

## Data Overview
The query returned **15 records** with the following fields:
- `id` - Unique identifier
- `name` - Customer name  
- `email` - Contact email
- `created_at` - Account creation date

## Key Findings

1. **Most Active Customers**: Users who registered in 2023
2. **Geographic Distribution**: Mainly from North America and Europe
3. **Growth Trend**: 25% increase compared to last quarter

## Important Notes

> This data reflects activity from January 2023 to December 2023.
> Please note that test accounts have been filtered out.

For more details, contact [support@example.com](mailto:support@example.com).

---

### SQL Query Used:
```sql
SELECT id, name, email, created_at
FROM customers
WHERE created_at >= '2023-01-01'
AND account_type != 'test'
ORDER BY created_at DESC;
```

*Query execution time: 0.12 seconds*
"""
    
    print("Sample response with markdown formatting:")
    print("="*50)
    print_markdown(sample_response)
    print("="*50)
    
    print("\nAs you can see, the markdown elements are now properly formatted:")
    print("- Headings are emphasized")
    print("- Bold and italic text is highlighted")
    print("- Bullet points and numbered lists are formatted")
    print("- Code blocks have a distinct appearance")
    print("- Links are underlined")
    print("- Blockquotes have special formatting")


if __name__ == "__main__":
    test_markdown_support()
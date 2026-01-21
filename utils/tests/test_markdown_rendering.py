#!/usr/bin/env python3
"""
Test script to verify markdown rendering functionality for final responses
"""

from utils.markdown_renderer import print_markdown

def test_markdown_rendering():
    """Test various markdown elements in responses"""
    
    print("Testing markdown rendering functionality...\n")
    
    # Sample markdown content that might appear in a response
    sample_response = """
# Database Query Results Summary

## Overview
The query returned **important** results about user data.

### Key Findings:
- Total users: **1,248**
- Active users: *1,102* (88.3%)
- Inactive users: `146` (11.7%)

## Detailed Information

### User Statistics
- Average age: 32 years
- Most common location: `New York, NY`
- Peak activity time: **10:00 AM - 12:00 PM**

### Data Quality Notes
The dataset appears to be ~98% complete with minimal null values.

[Learn more about our data methodology](https://example.com/data-methodology)

---

## Conclusion
The analysis shows strong engagement with our platform. For more details, see the full report.

```sql
SELECT COUNT(*) FROM users 
WHERE status = 'active' 
AND last_login > DATE_SUB(NOW(), INTERVAL 30 DAY);
```

Best regards,
Data Analysis Team
"""

    print("Sample response with markdown formatting:")
    print("="*50)
    print_markdown(sample_response)
    print("="*50)
    print("\nMarkdown rendering test completed successfully!")

if __name__ == "__main__":
    test_markdown_rendering()
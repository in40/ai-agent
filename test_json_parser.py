"""
Test script for robust JSON parsing utilities.
Tests various edge cases and escape character scenarios.
"""
import sys
sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

from json_utils import parse_json_robust, fix_escape_characters, extract_json_from_response

# Test cases
test_cases = [
    {
        'name': 'Valid JSON',
        'input': '{"chunks": [{"content": "Hello world"}]}',
        'expected_chunks': 1
    },
    {
        'name': 'JSON with Windows path',
        'input': '{"chunks": [{"content": "File located at C:\\Users\\test\\file.txt"}]}',
        'expected_chunks': 1
    },
    {
        'name': 'JSON with newline escape',
        'input': '{"chunks": [{"content": "Line 1\\nLine 2\\nLine 3"}]}',
        'expected_chunks': 1
    },
    {
        'name': 'JSON with mixed escapes',
        'input': '{"chunks": [{"content": "Path: C:\\test\\new\\file.txt\\nNext line"}]}',
        'expected_chunks': 1
    },
    {
        'name': 'JSON in markdown code block',
        'input': '```json\n{"chunks": [{"content": "Test content"}]}\n```',
        'expected_chunks': 1
    },
    {
        'name': 'JSON with surrounding text',
        'input': 'Here is the JSON you requested:\n{"chunks": [{"content": "Test"}]}\nHope this helps!',
        'expected_chunks': 1
    },
    {
        'name': 'JSON with Russian text',
        'input': '{"chunks": [{"content": "ГОСТ Р 34.10-2012 требует использования шифрования"}]}',
        'expected_chunks': 1
    },
    {
        'name': 'JSON with tab and special chars',
        'input': '{"chunks": [{"content": "Column1\\tColumn2\\nValue1\\tValue2"}]}',
        'expected_chunks': 1
    },
    {
        'name': 'Truncated JSON',
        'input': '{"chunks": [{"content": "Test"}',
        'expected_chunks': 1
    },
    {
        'name': 'Complex nested JSON',
        'input': '''{
            "document": "GOST_R_12345-2020",
            "chunks": [
                {
                    "content": "Section 1: Общие положения\\n\\n1.1 Область применения",
                    "metadata": {
                        "section": 1,
                        "path": "C:\\\\docs\\\\gost.pdf"
                    }
                }
            ],
            "entities": ["ГОСТ Р 12345-2020", "ФСБ России"]
        }''',
        'expected_chunks': 1
    }
]

print("=" * 80)
print("Testing Robust JSON Parser")
print("=" * 80)

passed = 0
failed = 0

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"Input: {test['input'][:100]}{'...' if len(test['input']) > 100 else ''}")
    
    try:
        result = parse_json_robust(test['input'], default_on_error={'chunks': []})
        chunks = result.get('chunks', [])
        
        if len(chunks) >= test['expected_chunks']:
            print(f"✓ PASS - Parsed {len(chunks)} chunk(s)")
            passed += 1
        else:
            print(f"✗ FAIL - Expected {test['expected_chunks']} chunk(s), got {len(chunks)}")
            print(f"  Result: {result}")
            failed += 1
    except Exception as e:
        print(f"✗ FAIL - Exception: {e}")
        failed += 1

print("\n" + "=" * 80)
print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 80)

# Test the specific error case from the logs
print("\n" + "=" * 80)
print("Testing specific error case: Invalid \\escape")
print("=" * 80)

# Simulate the error from gost-r-50922-2006
problematic_json = '''
{
  "document": "gost-r-50922-2006",
  "chunks": [
    {
      "content": "Требования к \\n\\tтестированию\\n\\nПуть: C:\\Program Files\\Test\\file.txt"
    }
  ]
}
'''

print(f"Testing problematic JSON with mixed escapes...")
try:
    result = parse_json_robust(problematic_json, default_on_error={'chunks': []})
    if result.get('chunks'):
        print(f"✓ Successfully parsed problematic JSON")
        print(f"  Content: {result['chunks'][0].get('content', '')[:100]}")
    else:
        print(f"✗ Failed to parse - no chunks found")
except Exception as e:
    print(f"✗ Exception: {e}")

print("\n" + "=" * 80)
print("Testing escape character fix function")
print("=" * 80)

# Test escape character fixing
test_escapes = [
    r'{"path": "C:\Users\test"}',
    r'{"text": "Line1\nLine2\tTab"}',
    r'{"mixed": "C:\test\next\\file"}',
]

for test_str in test_escapes:
    print(f"\nOriginal: {test_str}")
    fixed = fix_escape_characters(test_str)
    print(f"Fixed:    {fixed}")
    try:
        import json
        parsed = json.loads(fixed)
        print(f"✓ Successfully parsed after fix")
    except json.JSONDecodeError as e:
        print(f"✗ Still invalid JSON: {e}")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)

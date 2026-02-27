#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/qwen/ai_agent/backend')

import json
import re

# Simulate LM Studio chat completion response
class MockChoice:
    def __init__(self, content):
        self.message = type('obj', (object,), {'content': content})()

class MockLLMResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

# Test JSON with markdown blocks
test_json = '''```json
{
  "document": "TEST_DOC",
  "total_chunks": 3,
  "chunks": [
    {"chunk_id": 1, "content": "First chunk content"},
    {"chunk_id": 2, "content": "Second chunk content"},
    {"chunk_id": 3, "content": "Third chunk content"}
  ]
}
```'''

llm_response = MockLLMResponse(test_json)

# Apply the fix logic
response_content = None
if hasattr(llm_response, 'content') and llm_response.content:
    response_content = llm_response.content
elif hasattr(llm_response, 'choices') and llm_response.choices:
    response_content = llm_response.choices[0].message.content
else:
    response_content = str(llm_response)

print(f"Extracted content length: {len(response_content)}")

# Parse JSON
json_match = re.search(r'\{[\s\S]*\}', response_content)
if json_match:
    json_str = json_match.group(0)
    json_str = re.sub(r'^```json\s*|\s*```$', '', json_str.strip())
    chunking_result = json.loads(json_str)
    chunks_data = chunking_result.get('chunks', [])
    chunks = [c.get('content', '') for c in chunks_data if c.get('content')]
    print(f"Successfully parsed {len(chunks)} chunks!")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {chunk[:50]}...")
else:
    print("ERROR: No JSON found")

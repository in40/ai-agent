#!/usr/bin/env python3
from backend.services.rag.document_store_client import document_store_client
import json
import base64
import re

# Get document in PDF format
result = document_store_client.get_document('job_downloads_20260224_155425', 'doc_142', format='pdf')

print("=== Document Store Result ===")
print(f"Success: {result.get('success')}")
print(f"Result keys: {result.get('result', {}).keys() if isinstance(result.get('result'), dict) else 'N/A'}")

result_data = result.get('result', {})
print(f"\nContent length from metadata: {result_data.get('content_length', 'N/A')}")
print(f"Content type: {type(result_data.get('content', ''))}")
content = result_data.get('content', '')
print(f"Content length (actual): {len(content) if content else 0}")
print(f"Content preview (first 200 chars): {content[:200] if content else 'EMPTY'}")

# Check if content is base64
if content and len(content) > 100:
    # Check if it looks like base64
    if re.match(r'^[A-Za-z0-9+/=]+$', content[:100]):
        print("\nContent appears to be base64 encoded")
        try:
            decoded = base64.b64decode(content)
            print(f"Decoded length: {len(decoded)} bytes")
            print(f"Decoded preview: {decoded[:100]}")
        except Exception as e:
            print(f"Base64 decode failed: {e}")
    else:
        print("\nContent does NOT look like base64")

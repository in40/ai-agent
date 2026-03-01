#!/usr/bin/env python3
import requests

print("Testing RAG retrieve endpoint...")

# Test without auth first (will fail but shows if endpoint works)
resp = requests.post('http://localhost:5003/api/rag/retrieve',
    json={'query': 'test', 'mode': 'hybrid'})
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")

#!/usr/bin/env python3
import sys
import requests
import json

sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

# Test direct MCP call first
print("=== Direct MCP call ===")
response = requests.post(
    "http://localhost:3070/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "list_ingestion_jobs", "arguments": {}}
    },
    headers={"Content-Type": "application/json"}
)
print(f"Status: {response.status_code}")
raw_result = response.json()
print(f"Raw result: {json.dumps(raw_result, indent=2)[:500]}...")

# Now test the client
print("\n=== Document Store Client ===")
from document_store_client import document_store_client

result = document_store_client.list_ingestion_jobs()
print(f"list_ingestion_jobs: success={result.get('success')}")
print(f"  Full result: {result}")

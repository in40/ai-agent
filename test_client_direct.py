#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

from document_store_client import document_store_client

print("Testing document_store_client directly...")
result = document_store_client.list_ingestion_jobs()
print(f"Result: {result}")
print(f"Success: {result.get('success')}")
print(f"Jobs: {result.get('result', {}).get('jobs', [])}")

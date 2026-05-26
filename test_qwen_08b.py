#!/usr/bin/env python3
"""Qwen 0.8B Smart Chunking Test"""
import sys, os, time, json

# MUST be set BEFORE any imports
os.environ['RESPONSE_LLM_PROVIDER'] = 'LM Studio'
os.environ['RESPONSE_LLM_MODEL'] = 'qwen3.5-0.8b@bf16'
os.environ['RESPONSE_LLM_HOSTNAME'] = 'asus-tus'
os.environ['RESPONSE_LLM_PORT'] = '1234'
os.environ['RESPONSE_LLM_API_PATH'] = '/v1/chat/completions'

sys.path.insert(0, '/root/qwen/ai_agent')

print(f"=== QWEN 0.8B TEST ===")
print(f"MODEL: {os.environ.get('RESPONSE_LLM_MODEL')}")
print(f"HOST: {os.environ.get('RESPONSE_LLM_HOSTNAME')}:{os.environ.get('RESPONSE_LLM_PORT')}")
print(f"API: {os.environ.get('RESPONSE_LLM_API_PATH')}")
print()

# Force fresh import
if 'backend.services.rag.smart_ingestion_enhanced' in sys.modules:
    del sys.modules['backend.services.rag.smart_ingestion_enhanced']
if 'models.response_generator' in sys.modules:
    del sys.modules['models.response_generator']

from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync

start = time.time()
success, chunks, error = chunk_document_with_llm_sync(
    '/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md',
    '', 'r-1323565.1_881b0329.pdf', 300)
elapsed = (time.time() - start) / 60
with_content = sum(1 for c in chunks if c.get('content')) if chunks else 0

print(f"Result: success={success}, chunks={len(chunks)}, with_content={with_content}, time={elapsed:.1f}min")

result = {'model': 'qwen_0.8b', 'success': success, 'chunks': len(chunks), 'with_content': with_content, 'elapsed': elapsed}
with open('/root/qwen/ai_agent/qwen_0.8b_final.json', 'w') as f:
    json.dump(result, f, indent=2)
print(f"Saved: /root/qwen/ai_agent/qwen_0.8b_final.json")

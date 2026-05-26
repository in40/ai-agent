#!/usr/bin/env python3
"""Qwen 0.8B Direct Test"""
import sys, time, json
sys.path.insert(0, '/root/qwen/ai_agent')

print(f'=== QWEN 0.8B TEST ===')
print(f'Start: {time.strftime("%H:%M:%S")}')
print()

# Verify config
from config.settings import RESPONSE_LLM_HOSTNAME, RESPONSE_LLM_MODEL
print(f'Config: HOST={RESPONSE_LLM_HOSTNAME}, MODEL={RESPONSE_LLM_MODEL}')
if RESPONSE_LLM_HOSTNAME != 'asus-tus':
    print('ERROR: Wrong host!')
    sys.exit(1)
print()

# Test simple call first
print('Testing simple LLM call...')
from models.response_generator import ResponseGenerator
rg = ResponseGenerator()
result = rg.llm.invoke('Say hello')
print(f'Simple call works: {result.content[:30]}...')
print()

# Now run chunking
print('Starting chunking (600 sec timeout)...')
from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync

start = time.time()
success, chunks, error = chunk_document_with_llm_sync(
    '/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md',
    '', 'r-1323565.1_881b0329.pdf', 600)
elapsed = (time.time() - start) / 60
with_content = sum(1 for c in chunks if c.get('content')) if chunks else 0

print(f'End: {time.strftime("%H:%M:%S")}')
print(f'Qwen 0.8B Result: success={success}, chunks={len(chunks)}, with_content={with_content}, time={elapsed:.1f}min')

result = {'model': 'qwen_0.8b', 'success': success, 'chunks': len(chunks), 'with_content': with_content, 'elapsed': elapsed}
with open('/root/qwen/ai_agent/qwen_0.8b_final.json', 'w') as f:
    json.dump(result, f, indent=2)
print(f'Saved: /root/qwen/ai_agent/qwen_0.8b_final.json')

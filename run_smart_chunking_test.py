#!/usr/bin/env python3
"""Smart chunking test with 119B model - quality focused"""

import sys
import json
import time
sys.path.insert(0, '/root/qwen/ai_agent')

from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync

print("=" * 80)
print("SMART CHUNKING TEST - 119B MODEL (QUALITY FOCUSED)")
print("=" * 80)
print()
print("Model: mistral-small-4-119b-2603 (from .env config)")
print("Timeout: 60 minutes (quality over speed)")
print()

text_path = '/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md'

with open(text_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Document: r-1323565.1_881b0329.md")
print(f"Size: {len(content):,} chars")
print()
print("Starting smart chunking...")
print("(This may take 30-60 minutes with 119B model)")
print("-" * 80)
print()

start_time = time.time()

success, chunks, error = chunk_document_with_llm_sync(
    file_path=text_path,
    prompt="",
    filename="r-1323565.1_881b0329.pdf",
    timeout=3600  # 60 minutes
)

elapsed = time.time() - start_time

print("-" * 80)
print()
print("=" * 80)
print("FINAL RESULTS:")
print("=" * 80)
print(f"Success: {success}")
print(f"Chunks generated: {len(chunks)}")
print(f"Time elapsed: {elapsed/60:.1f} minutes")
if error:
    print(f"Error: {error}")
print()

if chunks and success:
    chunked_content = '\n\n'.join([c.get('content', '') for c in chunks])
    coverage = len(chunked_content) / len(content) * 100
    
    print(f"Total chunked content: {len(chunked_content):,} chars")
    print(f"Coverage: {coverage:.1f}% of original document")
    print()
    
    print("CHUNK DETAILS:")
    print("=" * 80)
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  Section: {chunk.get('section', 'N/A')}")
        print(f"  Title: {chunk.get('title', 'N/A')[:70]}")
        print(f"  Type: {chunk.get('chunk_type', 'N/A')}")
        print(f"  Tokens: {chunk.get('token_count', 'N/A')}")
        print(f"  Content length: {len(chunk.get('content', '')):,} chars")
    
    # Save full results
    results = {
        'success': success,
        'chunks': chunks,
        'error': error,
        'coverage': coverage,
        'document': 'r-1323565.1_881b0329.md',
        'model': 'mistral-small-4-119b-2603',
        'elapsed_minutes': elapsed/60
    }
    with open('/root/qwen/ai_agent/smart_chunking_119b_full_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 80)
    print("Results saved to: /root/qwen/ai_agent/smart_chunking_119b_full_results.json")
    print("=" * 80)
elif not success:
    print("Smart chunking FAILED")
    print(f"Error: {error}")

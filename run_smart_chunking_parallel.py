#!/usr/bin/env python3
"""
Smart Chunking Parallel Comparison Test
Tests both 119B and 0.8B models in parallel
"""

import sys
import json
import time
import os
import threading
sys.path.insert(0, '/root/qwen/ai_agent')

# Test configuration
TEST_DOC = '/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md'

def run_single_test(model_name, env_config, timeout, results_dict):
    """Run smart chunking test with specified model"""
    print()
    print("=" * 80)
    print(f"TESTING: {model_name}")
    print("=" * 80)
    print()
    
    # Set environment variables
    for key, value in env_config.items():
        os.environ[key] = value
    
    print(f"Model: {env_config['RESPONSE_LLM_MODEL']}")
    print(f"Host: {env_config['RESPONSE_LLM_HOSTNAME']}:{env_config['RESPONSE_LLM_PORT']}")
    print(f"Timeout: {timeout} seconds")
    print()
    
    # Reload modules to pick up new env vars
    import importlib
    from backend.services.rag import smart_ingestion_enhanced
    importlib.reload(smart_ingestion_enhanced)
    from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync
    
    # Run chunking
    start_time = time.time()
    success, chunks, error = chunk_document_with_llm_sync(
        file_path=TEST_DOC,
        prompt="",
        filename="r-1323565.1_881b0329.pdf",
        timeout=timeout
    )
    elapsed = time.time() - start_time
    
    # Analyze results
    print()
    print("-" * 80)
    print("RESULTS:")
    print("-" * 80)
    print(f"Success: {success}")
    print(f"Time elapsed: {elapsed/60:.1f} minutes")
    print(f"Chunks generated: {len(chunks)}")
    if error:
        print(f"Error: {error}")
    print()
    
    with_content = 0
    if chunks:
        # Analyze content
        with_content = sum(1 for c in chunks if c.get('content') and len(c.get('content', '')) > 0)
        without_content = len(chunks) - with_content
        
        print(f"Chunks WITH content: {with_content} ({with_content/len(chunks)*100:.1f}%)")
        print(f"Chunks WITHOUT content: {without_content} ({without_content/len(chunks)*100:.1f}%)")
        print()
        
        # Check for corrupted keys
        corrupted = 0
        for chunk in chunks:
            for key in chunk.keys():
                if '"' in key or '\n' in key or ':' in key:
                    corrupted += 1
        
        if corrupted == 0:
            print("✅ NO corrupted keys!")
        else:
            print(f"⚠️  {corrupted} chunks have corrupted keys")
        print()
        
        # Calculate total content
        total_content = sum(len(c.get('content', '')) for c in chunks)
        print(f"Total content: {total_content:,} chars")
        print(f"Average per chunk: {total_content/len(chunks):.0f} chars")
        
        # Save results
        results_data = {
            'model': model_name,
            'success': success,
            'chunks': chunks,
            'elapsed_minutes': elapsed/60,
            'error': error
        }
        output_file = f'/root/qwen/ai_agent/smart_chunking_{model_name}_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        print()
        print(f"Results saved to: {output_file}")
    
    # Store in results dict
    results_dict[model_name] = {
        'model': model_name,
        'success': success,
        'chunks': len(chunks),
        'with_content': with_content,
        'elapsed': elapsed/60,
        'error': error
    }

if __name__ == '__main__':
    print("=" * 80)
    print("SMART CHUNKING PARALLEL MODEL COMPARISON TEST")
    print("=" * 80)
    print()
    print(f"Test document: {TEST_DOC}")
    print()
    
    # Load document info
    with open(TEST_DOC, 'r', encoding='utf-8') as f:
        doc_content = f.read()
    print(f"Document size: {len(doc_content):,} chars")
    print()
    
    # Model configurations
    models = [
        {
            'name': 'mistral_119b',
            'env': {
                'RESPONSE_LLM_PROVIDER': 'LM Studio',
                'RESPONSE_LLM_MODEL': 'mistral-small-4-119b-2603',
                'RESPONSE_LLM_HOSTNAME': '192.168.51.105',
                'RESPONSE_LLM_PORT': '1234',
                'RESPONSE_LLM_API_PATH': '/v1',
            },
            'timeout': 3600
        },
        {
            'name': 'qwen_0.8b',
            'env': {
                'RESPONSE_LLM_PROVIDER': 'LM Studio',
                'RESPONSE_LLM_MODEL': 'qwen3.5-0.8b@bf16',
                'RESPONSE_LLM_HOSTNAME': 'asus-tus',
                'RESPONSE_LLM_PORT': '1234',
                'RESPONSE_LLM_API_PATH': '/v1/completions',
            },
            'timeout': 600
        }
    ]
    
    results = {}
    threads = []
    
    # Start both tests in parallel
    for model_config in models:
        t = threading.Thread(
            target=run_single_test,
            args=(model_config['name'], model_config['env'], model_config['timeout'], results)
        )
        t.start()
        threads.append(t)
        print(f"Started thread for {model_config['name']}")
    
    print()
    print("Both models running in parallel...")
    print("Check individual logs for progress")
    print()
    
    # Wait for both to complete
    for t in threads:
        t.join()
    
    # Summary
    print()
    print("=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Model':<20} {'Success':<10} {'Chunks':<10} {'With Content':<15} {'Time (min)':<12}")
    print("-" * 80)
    for model_name in ['mistral_119b', 'qwen_0.8b']:
        if model_name in results:
            r = results[model_name]
            print(f"{r['model']:<20} {str(r['success']):<10} {r['chunks']:<10} {r['with_content']:<15} {r['elapsed']:.1f}")
    print()
    
    # Save summary
    with open('/root/qwen/ai_agent/smart_chunking_comparison_summary.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print("Summary saved to: /root/qwen/ai_agent/smart_chunking_comparison_summary.json")

#!/usr/bin/env python3
"""Test document store API to understand the response format"""
from backend.services.rag.document_store_client import document_store_client
import json

# Get list of jobs
jobs_result = document_store_client.list_ingestion_jobs()
print("=== JOBS RESULT ===")
print(json.dumps(jobs_result, indent=2, default=str)[:2000])

if jobs_result.get('success'):
    result = jobs_result.get('result', {})
    if isinstance(result, dict) and result.get('success'):
        jobs = result.get('jobs', [])
    else:
        jobs = result.get('jobs', [])
    
    print(f"\n=== Found {len(jobs)} jobs ===")
    
    # Find a job with PDF documents
    for job in jobs[:3]:  # Check first 3 jobs
        job_id = job.get('job_id')
        print(f"\n=== Job: {job_id} ===")
        
        # Get documents for this job
        docs_result = document_store_client.list_documents(job_id)
        if docs_result.get('success'):
            docs_data = docs_result.get('result', {})
            if isinstance(docs_data, dict) and docs_data.get('success'):
                documents = docs_data.get('documents', [])
            else:
                documents = docs_data.get('documents', [])
            
            print(f"Documents: {len(documents)}")
            for doc in documents[:2]:
                print(f"  - {doc.get('filename', 'Unknown')}: format={doc.get('format')}, size={doc.get('size')}")
            
            # Try to get a PDF document
            for doc in documents:
                if doc.get('format') == 'pdf':
                    doc_id = doc.get('doc_id')
                    print(f"\n=== Getting PDF: {doc_id} ===")
                    
                    content_result = document_store_client.get_document(job_id, doc_id, format='pdf')
                    print(f"Success: {content_result.get('success')}")
                    if content_result.get('success'):
                        result_data = content_result.get('result', {})
                        print(f"Result keys: {result_data.keys() if isinstance(result_data, dict) else type(result_data)}")
                        if 'content' in result_data:
                            content = result_data['content']
                            print(f"Content type: {type(content)}")
                            if isinstance(content, dict):
                                print(f"Content keys: {content.keys()}")
                                for k, v in content.items():
                                    if isinstance(v, str):
                                        print(f"  {k}: {v[:100] if len(v) > 100 else v}")
                                    else:
                                        print(f"  {k}: {type(v)}")
                            elif isinstance(content, str):
                                print(f"Content length: {len(content)}")
                                print(f"First 100 chars: {content[:100]}")
                            elif isinstance(content, bytes):
                                print(f"Content length: {len(content)} bytes")
                    break
            break

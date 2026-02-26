#!/usr/bin/env python3
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

job_json = redis_client.get("smart_ingestion_job:job_new_20260223_191413")
if job_json:
    job_data = json.loads(job_json)
    params = job_data.get('parameters', {})
    doc_urls = params.get('document_urls', [])
    print(f"Job ID: {job_data.get('job_id')}")
    print(f"Documents total (counter): {job_data.get('documents_total', 'N/A')}")
    print(f"Document URLs in parameters: {len(doc_urls)}")
    print(f"First 10 URLs:")
    for i, url in enumerate(doc_urls[:10]):
        print(f"  {i+1}. {url}")
else:
    print("Job not found in Redis")

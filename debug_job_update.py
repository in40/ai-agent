#!/usr/bin/env python
from backend.services.rag.job_queue import job_queue, redis_client
import json

job = job_queue.get_job('job_7d61486a8c76')
print(f"Before update:")
print(f"  documents_processed: {job.documents_processed}")
print(f"  chunks_generated: {job.chunks_generated}")

# Update values
job.documents_processed = 1
job.chunks_generated = 1001

print(f"\nAfter manual update:")
print(f"  documents_processed: {job.documents_processed}")
print(f"  chunks_generated: {job.chunks_generated}")

# Check to_dict
job_dict = job.to_dict()
print(f"\nIn to_dict():")
print(f"  documents_processed: {job_dict.get('documents_processed')}")
print(f"  chunks_generated: {job_dict.get('chunks_generated')}")

# Now save
job_queue.update_job(job)
print(f"\nAfter update_job()")

# Check Redis
data = redis_client.get('smart_ingestion_job:job_7d61486a8c76')
if data:
    job2 = json.loads(data)
    print(f"  Redis documents_processed: {job2.get('documents_processed')}")
    print(f"  Redis chunks_generated: {job2.get('chunks_generated')}")

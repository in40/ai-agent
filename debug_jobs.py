#!/usr/bin/env python3
"""Generate batch PDF extraction job configurations."""
import json
import uuid
from datetime import datetime

# Generate 3 unique job IDs
job_ids = ['job_2cc3afa5094448eb9d0cd8f171fe7eec']

pdf_1_metadata = [
    'pdf-001-001', 'pdf-001-002', 'pdf-001-003', 'pdf-001-004', 'pdf-001-005', 'pdf-001-006', 'pdf-001-007', 'pdf-001-008', 'pdf-001-009'
]

pdf_2_metadata = [
    'pdf-002-001', 'pdf-002-002', 'pdf-002-003', 'pdf-002-004', 'pdf-002-005', 'pdf-002-006', 'pdf-002-007', 'pdf-002-008', 'pdf-002-009'
]

pdf_3_metadata = [
    'pdf-003-001', 'pdf-003-002', 'pdf-003-003', 'pdf-003-004', 'pdf-003-005', 'pdf-003-006', 'pdf-003-007', 'pdf-003-008', 'pdf-003-009'
]

print("Job IDs:", job_ids)
print("First job ID length:", len(job_ids[0]))
print("First job ID repr:", repr(job_ids[0]))

jobs = []
for i, pdfs in enumerate(pdf_1_metadata, start=1):
    job_id = f'{job_ids[0]}_{i}'
    print(f"Iteration {i}: creating job_id={repr(job_id)}")
    jobs.append({
        'job_id': job_id,
        'name': f'Group 1 - PDF {i}',
        'phases': ['extract'],
        'parameters': {
            'document_ids': pdfs,
            'max_tokens': '5000',
            'temperature': 0.7,
        }
    })

print(f"\nTotal jobs: {len(jobs)}")
for j in jobs:
    print(f"  Job: {j['job_id'][:20]}... ({len(j['parameters']['document_ids'])} PDFs)")

with open('/root/qwen/ai_agent/jobs.json', 'w') as f:
    json.dump(jobs, f, indent=2)

print("\n--- jobs.json ---")
print(json.dumps(jobs, indent=2))
print(f"\nFile written successfully")

#!/usr/bin/env python3
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

print(f"=== Phased Processing Jobs Analysis (Yesterday) ===\n")

job_keys = redis_client.keys("smart_ingestion_job:job_*")
job_count = len(job_keys)

for key in job_keys:
    job_data = json.loads(redis_client.get(key))
    status = job_data.get('status', '')
    created_at = job_data.get('created_at', '')
    
    is_yesterday = False
    if created_at:
        try:
            # Parse the created_at timestamp (format: 2026-03-18T09:20:48)
            date_part = created_at.split('T')[0]
            year = 2026
            day = int(date_part.split('-')[2])
            # Check if it's within the last 24 hours from today (2026-03-19)
            # Jobs from March 17, 2026 were yesterday
            yesterday = (day == 17)
            is_yesterday = yesterday
        except:
            pass
    
    # Filter: status must be in_progress or completed
    # Excluding cancelled jobs
    is_valid = status == 'in_progress' or status == 'completed'
    
    if is_yesterday and is_valid:
        print(f"✓ **JOB STARTED YESTERDAY**")
        print(f"  Job ID: {job_data['job_id']}")
        print(f"  Status: {status}")
        print(f"  Created: {created_at}")
        print()

print(f"=== Summary ===")
valid_jobs_yesterday = 0
for key in job_keys:
    job_data = json.loads(redis_client.get(key))
    status = job_data.get('status', '')
    created_at = job_data.get('created_at', '')
    date_part = created_at.split('T')[0]
    year = 2026
    day = int(date_part.split('-')[2])
    yesterday = (day == 17)
    is_valid = status == 'in_progress' or status == 'completed'
    if yesterday and is_valid:
        valid_jobs_yesterday += 1

print(f"Total valid jobs started yesterday (in_progress or completed): {valid_jobs_yesterday}")

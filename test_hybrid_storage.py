#!/usr/bin/env python3
"""Test hybrid job storage"""
from backend.services.rag.job_queue import SmartIngestionJob, JobStatus
from backend.services.rag.hybrid_job_storage import hybrid_storage
from datetime import datetime, timedelta

# Create a test job
job = SmartIngestionJob(
    job_id="test_job_001",
    user_id="test_user",
    job_type="file_upload",
    status=JobStatus.COMPLETED.value,
    created_at=datetime.utcnow().isoformat(),
    updated_at=datetime.utcnow().isoformat(),
    expires_at=(datetime.utcnow() + timedelta(hours=24)).isoformat(),
    parameters={"files": ["test.pdf"]},
    progress=100,
    current_stage="completed",
    result={"chunks_generated": 10},
    error=None,
    documents_total=1,
    documents_processed=1,
    chunks_generated=10,
    ingestion_mode="files",
    processing_mode="vector_db",
    chunking_strategy="smart_chunking"
)

print("=== Testing Hybrid Storage ===")
print(f"Created job: {job.job_id}")

# Save to hybrid storage
hybrid_storage.save_job(job, save_to_db=True)
print(f"✅ Saved job to Redis + PostgreSQL")

# Retrieve from storage
retrieved = hybrid_storage.get_job("test_job_001")
if retrieved:
    print(f"✅ Retrieved job: status={retrieved.status}, progress={retrieved.progress}")
else:
    print("❌ Failed to retrieve job")

# Get all jobs
all_jobs = hybrid_storage.get_all_jobs(limit=10, include_historical=True)
print(f"✅ Total jobs in system: {len(all_jobs)}")

print("\n=== Test Complete ===")

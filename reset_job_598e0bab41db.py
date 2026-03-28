#!/usr/bin/env python3
"""
Reset job job_598e0bab41db for re-processing after .md file corruption bug fix
"""
from backend.services.rag.phased_processing_db import phased_db, db_manager
from backend.services.rag.phased_processing_models import PhaseStatus, DocumentStatus
from sqlalchemy import text
import os
import redis
import json

doc_id = 'r-1323565.1_8e67ba17'
job_id = 'job_598e0bab41db'

print("=" * 80)
print("Resetting job for re-processing")
print("=" * 80)

# 1. Delete the corrupted .md file
md_file = f'document-store-mcp-server/data/ingested/job_job_08795a8215d8_rst_gov_ru:8443/documents/{doc_id}.md'
if os.path.exists(md_file):
    os.remove(md_file)
    print(f'✓ Deleted corrupted file: {md_file}')
else:
    print(f'✗ File not found: {md_file}')

# 2. Reset document status in DB
try:
    with db_manager.engine.connect() as conn:
        conn.execute(text("""
            UPDATE document_processing 
            SET phase_extract = :pending,
                phase_chunk = :pending,
                phase_vector = :pending,
                phase_graph = :pending,
                current_phase = :current_phase,
                overall_status = :overall_status,
                last_error = NULL,
                last_error_phase = NULL,
                chunk_count = 0
            WHERE doc_id = :doc_id
        """), {
            'doc_id': doc_id,
            'pending': PhaseStatus.PENDING.value,
            'current_phase': 'extract',
            'overall_status': DocumentStatus.PENDING.value
        })
        conn.commit()
    print(f'✓ Reset document status for: {doc_id}')
except Exception as e:
    print(f'✗ Failed to reset document status: {e}')

# 3. Deactivate old chunks
try:
    phased_db.deactivate_chunks(doc_id)
    print(f'✓ Deactivated old chunks for: {doc_id}')
except Exception as e:
    print(f'✗ Failed to deactivate chunks: {e}')

# 4. Update job status in Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    job_json = r.get(f'smart_ingestion_job:{job_id}')
    if job_json:
        job_data = json.loads(job_json)
        job_data['status'] = 'pending'
        job_data['current_stage'] = None
        job_data['progress'] = 0
        job_data['error'] = None
        job_data['chunks_generated'] = 0
        r.set(f'smart_ingestion_job:{job_id}', json.dumps(job_data))
        print(f'✓ Reset job status in Redis: {job_id}')
    else:
        print(f'✗ Job not found in Redis: {job_id}')
except Exception as e:
    print(f'✗ Failed to reset job in Redis: {e}')

print()
print("=" * 80)
print("✅ Ready to re-run smart chunking!")
print("=" * 80)
print()
print("Next steps:")
print("1. Go to Web UI Document Store")
print("2. Select document: r-1323565.1_8e67ba17.pdf")
print("3. Run 'Smart Chunking'")
print("4. Verify both .md and .chunks.json files are created")

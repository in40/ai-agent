#!/usr/bin/env python3
"""
Complete chunking for job_90ac7296c72f which only ran extract phase
"""
from backend.services.rag.phased_processing_api import _smart_chunk_with_llm
from backend.services.rag.phased_processing_db import phased_db
from backend.services.rag.phased_processing_models import Chunk, PhaseStatus
from backend.services.rag.job_queue import job_queue
import os

doc_id = 'r-1323565.1_8a84396d'
job_id = 'job_90ac7296c72f'

print("=" * 80)
print("Running chunk phase for job_90ac7296c72f")
print("=" * 80)

# Get document
doc = phased_db.get_document(doc_id)
if not doc:
    print(f"✗ Document not found: {doc_id}")
    exit(1)

print(f"✓ Found document: {doc_id}")
print(f"  File path: {doc.file_path}")
print(f"  Extraction method: {doc.extraction_method}")
print(f"  Extracted chars: {doc.extracted_char_count}")

# Find the extracted text file
text_path = doc.file_path.replace('.pdf', '.txt')
if not os.path.exists(text_path):
    print(f"✗ Text file not found: {text_path}")
    exit(1)

print(f"✓ Found text file: {text_path}")

# Read extracted text
with open(text_path, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"✓ Read {len(text)} chars from text file")

# Run smart chunking (uses fixed-size chunking for now)
print("\nRunning chunking...")
try:
    chunks = _smart_chunk_with_llm(
        text=text,
        doc_id=doc_id,
        config={}
    )
    print(f"✓ Generated {len(chunks)} chunks")
except Exception as e:
    print(f"✗ Chunking failed: {e}")
    exit(1)
    chunks.append(Chunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}_chunk_{i:04d}",
        chunk_index=i,
        content=c.get('content', ''),
        content_length=len(c.get('content', '')),
        section=c.get('section', ''),
        title=c.get('title', ''),
        chunk_type='text',
        token_count=c.get('token_count', 0),
    ))

# Deactivate old chunks and save new ones
phased_db.deactivate_chunks(doc_id)
phased_db.save_chunks(chunks)
print(f"✓ Saved {len(chunks)} chunks to database")

# Save chunks to JSON file
import json
chunks_file = text_path.replace('.txt', '.chunks.json')
chunks_data = {
    'doc_id': doc_id,
    'filename': doc.original_filename,
    'total_chunks': len(chunks),
    'chunking_strategy': 'smart_llm',
    'chunks': [
        {
            'chunk_id': c.chunk_id,
            'chunk_index': c.chunk_index,
            'content': c.content,
            'section': c.section,
            'title': c.title,
            'token_count': c.token_count
        } for c in chunks
    ]
}
with open(chunks_file, 'w', encoding='utf-8') as f:
    json.dump(chunks_data, f, indent=2, ensure_ascii=False)
print(f"✓ Saved chunks to: {chunks_file}")

# Update document metadata
phased_db.update_document_metadata(doc_id, {
    'chunk_count': len(chunks),
    'chunking_strategy': 'smart_llm'
})

# Mark chunk phase as complete
phased_db.update_document_phase_status(
    doc_id, 'chunk', PhaseStatus.COMPLETED
)
print(f"✓ Marked chunk phase as COMPLETED")

# Update job in Redis
import redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
job_json = r.get(f'smart_ingestion_job:{job_id}')
if job_json:
    job_data = json.loads(job_json)
    job_data['chunks_generated'] = len(chunks)
    job_data['current_stage'] = 'completed'
    r.set(f'smart_ingestion_job:{job_id}', json.dumps(job_data))
    print(f"✓ Updated job in Redis")

print()
print("=" * 80)
print("✅ Chunking completed successfully!")
print("=" * 80)
print(f"\nFiles created:")
print(f"  - {text_path} (extracted text)")
print(f"  - {chunks_file} (chunking output)")
print(f"\nChunks: {len(chunks)}")

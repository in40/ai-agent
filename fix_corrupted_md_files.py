#!/usr/bin/env python3
"""
Fix corrupted .md files in document store that were overwritten with JSON chunking output.

This script:
1. Identifies .md files that contain JSON chunking output (bug symptom)
2. Deletes the corrupted .md files
3. Resets the document status in the phased processing DB so they can be re-extracted
"""

import os
import json
from backend.services.rag.phased_processing_db import phased_db
from backend.services.rag.phased_processing_models import PhaseStatus, DocumentStatus

DOC_STORE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"

def is_json_chunking_output(file_path):
    """Check if a file contains JSON chunking output instead of markdown text"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read more content to get complete JSON structure
            content = f.read(5000)  # Read first 5000 chars
            
        # Check if it starts with JSON structure
        content = content.strip()
        if content.startswith('{') or content.startswith('['):
            # Look for chunking-specific keys in the first part
            if '"chunks"' in content or '"chunk_id"' in content or '"chunk_index"' in content:
                return True
            # Try to parse as JSON to confirm
            try:
                # Find the end of the first JSON object/array
                if content.startswith('{'):
                    # Find matching closing brace (approximate)
                    end_idx = content.rfind('}') + 1
                    if end_idx > 0:
                        partial_json = content[:end_idx]
                        data = json.loads(partial_json)
                        if isinstance(data, dict) and 'chunks' in data:
                            return True
                elif content.startswith('['):
                    end_idx = content.rfind(']') + 1
                    if end_idx > 0:
                        partial_json = content[:end_idx]
                        data = json.loads(partial_json)
                        if isinstance(data, list) and len(data) > 0 and 'chunk_id' in data[0]:
                            return True
            except json.JSONDecodeError:
                # If parsing fails but we saw chunking keywords, still consider it corrupted
                pass
        return False
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return False

def find_corrupted_files():
    """Find all corrupted .md files in the document store"""
    corrupted = []
    
    if not os.path.exists(DOC_STORE_PATH):
        print(f"Document store path not found: {DOC_STORE_PATH}")
        return corrupted
    
    for job_dir in os.listdir(DOC_STORE_PATH):
        job_path = os.path.join(DOC_STORE_PATH, job_dir)
        if not os.path.isdir(job_path):
            continue
        
        docs_path = os.path.join(job_path, 'documents')
        if not os.path.exists(docs_path):
            continue
        
        for filename in os.listdir(docs_path):
            if filename.endswith('.md'):
                file_path = os.path.join(docs_path, filename)
                if is_json_chunking_output(file_path):
                    corrupted.append(file_path)
                    print(f"✓ Found corrupted: {file_path}")
    
    return corrupted

def delete_corrupted_files(corrupted_files):
    """Delete corrupted .md files"""
    deleted = []
    for file_path in corrupted_files:
        try:
            os.remove(file_path)
            print(f"✓ Deleted: {file_path}")
            deleted.append(file_path)
        except Exception as e:
            print(f"✗ Failed to delete {file_path}: {e}")
    return deleted

def reset_document_status(doc_id):
    """
    Reset document status in DB so it can be re-processed.
    Note: This requires direct SQL update as there's no generic update method.
    """
    try:
        from backend.services.rag.phased_processing_db import db_manager
        from sqlalchemy import text
        
        if not db_manager:
            print(f"  ⚠ Database not available, skipping DB reset for {doc_id}")
            return False
        
        # Update document status using direct SQL
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
                    last_error_phase = NULL
                WHERE doc_id = :doc_id
            """), {
                'doc_id': doc_id,
                'pending': PhaseStatus.PENDING.value,
                'current_phase': 'extract',
                'overall_status': DocumentStatus.PENDING.value
            })
            conn.commit()
        
        print(f"✓ Reset status for: {doc_id}")
        return True
    except Exception as e:
        print(f"✗ Failed to reset {doc_id}: {e}")
    return False

def main():
    print("=" * 80)
    print("Document Store .md File Corruption Fix")
    print("=" * 80)
    print()
    
    # Step 1: Find corrupted files
    print("Step 1: Finding corrupted .md files...")
    corrupted = find_corrupted_files()
    print(f"\nFound {len(corrupted)} corrupted files")
    print()
    
    if not corrupted:
        print("No corrupted files found!")
        return
    
    # Step 2: Delete corrupted files
    print("Step 2: Deleting corrupted files...")
    deleted = delete_corrupted_files(corrupted)
    print(f"\nDeleted {len(deleted)} files")
    print()
    
    # Step 3: Reset document status in DB
    print("Step 3: Resetting document status in database...")
    reset_count = 0
    for file_path in deleted:
        # Extract doc_id from filename
        doc_id = os.path.splitext(os.path.basename(file_path))[0]
        if reset_document_status(doc_id):
            reset_count += 1
    
    print(f"\nReset {reset_count} documents")
    print()
    
    # Summary
    print("=" * 80)
    print("Summary:")
    print(f"  - Found: {len(corrupted)} corrupted files")
    print(f"  - Deleted: {len(deleted)} files")
    print(f"  - Reset: {reset_count} documents")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Re-run smart chunking for the affected documents")
    print("2. The documents will be re-extracted from PDF and then chunked properly")

if __name__ == '__main__':
    main()

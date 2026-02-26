#!/usr/bin/env python3
"""
Create metadata files for all documents in a job
"""
import os
import json
from pathlib import Path

JOB_ID = "job_downloads_20260224_155425"
DOC_DIR = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/{JOB_ID}/documents"
DOWNLOADS_DIR = "/root/qwen/ai_agent/downloads"

# Map doc_id to original filename from downloads folder
original_files = {}
for i, pdf_file in enumerate(Path(DOWNLOADS_DIR).glob("*.pdf")):
    doc_id = f"doc_{i:03d}"
    original_files[doc_id] = pdf_file.name

# Create metadata files
count = 0
for pdf_file in Path(DOC_DIR).glob("*.pdf"):
    doc_id = pdf_file.stem
    original_filename = original_files.get(doc_id, pdf_file.name)
    
    metadata = {
        "doc_id": doc_id,
        "filename": original_filename,
        "format": "pdf",
        "size_bytes": pdf_file.stat().st_size,
        "original_path": str(pdf_file),
        "source": "downloads_folder_scan",
        "imported_at": "2026-02-24T15:54:25"
    }
    
    metadata_file = Path(DOC_DIR) / f"{doc_id}.metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    count += 1
    if count <= 5:
        print(f"Created: {metadata_file.name} -> {original_filename}")

print(f"\nCreated {count} metadata files in {DOC_DIR}")

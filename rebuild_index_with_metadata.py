#!/usr/bin/env python3
"""
Rebuild Document Store index with proper metadata from actual files
"""
import os
import json
from pathlib import Path

JOB_ID = "job_downloads_20260224_155425"
DOC_DIR = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/{JOB_ID}/documents"
INDEX_FILE = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/{JOB_ID}/index.json"

# Map doc_id to original filename from downloads folder
DOWNLOADS_DIR = "/root/qwen/ai_agent/downloads"
original_files = {}
for i, pdf_file in enumerate(Path(DOWNLOADS_DIR).glob("*.pdf")):
    doc_id = f"doc_{i:03d}"
    original_files[doc_id] = pdf_file.name

# Scan documents and build proper metadata
documents = {}
for pdf_file in Path(DOC_DIR).glob("*.pdf"):
    doc_id = pdf_file.stem  # e.g., "doc_000"
    
    # Get original filename if available
    original_filename = original_files.get(doc_id, pdf_file.name)
    
    documents[doc_id] = {
        "doc_id": doc_id,
        "filename": original_filename,  # Real filename like "guide.pdf"
        "format": "pdf",
        "size_bytes": pdf_file.stat().st_size,
        "stored_at": "2026-02-24T15:54:25",
        "metadata": {
            "filename": original_filename,
            "format": "pdf",
            "size_bytes": pdf_file.stat().st_size,
            "original_path": str(pdf_file),
            "source": "downloads_folder_scan"
        }
    }

# Create index
index = {
    "job_id": JOB_ID,
    "total_documents": len(documents),
    "documents": documents
}

# Save index
with open(INDEX_FILE, 'w') as f:
    json.dump(index, f, indent=2)

print(f"Rebuilt index with {len(documents)} documents")
print(f"Index file: {INDEX_FILE}")
print(f"\nFirst 5 documents:")
for i, (doc_id, doc_info) in enumerate(list(documents.items())[:5]):
    print(f"  {doc_id}: {doc_info['filename']} ({doc_info['size_bytes']} bytes)")

#!/usr/bin/env python3
import os
import json
from pathlib import Path

JOB_ID = "job_downloads_20260224_155425"
DOC_DIR = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/{JOB_ID}/documents"
INDEX_FILE = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/{JOB_ID}/index.json"

# Scan documents
documents = {}
for pdf_file in Path(DOC_DIR).glob("*.pdf"):
    doc_id = pdf_file.stem  # e.g., "doc_000"
    documents[doc_id] = {
        "doc_id": doc_id,
        "filename": pdf_file.name,
        "format": "pdf",
        "size_bytes": pdf_file.stat().st_size,
        "stored_at": "2026-02-24T15:54:25"
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

print(f"Created index with {len(documents)} documents")
print(f"Index file: {INDEX_FILE}")

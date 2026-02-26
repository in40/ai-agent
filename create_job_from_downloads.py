#!/usr/bin/env python3
"""
Scan downloads folder and create a Document Store job from existing files
"""
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
DOWNLOADS_DIR = "/root/qwen/ai_agent/downloads"
DOCUMENT_STORE_URL = "http://localhost:3070/mcp"
JOB_ID = f"job_downloads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def scan_downloads():
    """Scan downloads folder for PDF files"""
    pdf_files = []
    for file in Path(DOWNLOADS_DIR).glob("*.pdf"):
        pdf_files.append({
            'doc_id': f"doc_{len(pdf_files):03d}",
            'filename': file.name,  # Real filename like "guide.pdf"
            'path': str(file),
            'size': file.stat().st_size,
            'format': 'pdf'
        })
    return pdf_files

def create_job_in_document_store(files):
    """Create a job in Document Store with existing files"""
    print(f"Creating job {JOB_ID} with {len(files)} files...")
    
    for i, file_info in enumerate(files):
        try:
            # Read file content as binary
            with open(file_info['path'], 'rb') as f:
                content_bytes = f.read()

            # Encode binary content as base64 for safe JSON transport
            import base64
            content_b64 = base64.b64encode(content_bytes).decode('ascii')

            # Store via MCP
            payload = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": "store_document",
                    "arguments": {
                        "job_id": JOB_ID,
                        "doc_id": file_info['doc_id'],
                        "content": content_b64,  # Base64-encoded binary
                        "format": "pdf",
                        "metadata": {
                            "filename": file_info['filename'],  # Real filename
                            "original_path": file_info['path'],
                            "size_bytes": file_info['size'],
                            "format": "pdf",  # Explicit format
                            "imported_at": datetime.now().isoformat(),
                            "source": "downloads_folder_scan"
                        }
                    }
                }
            }
            
            response = requests.post(DOCUMENT_STORE_URL, json=payload, timeout=30)
            result = response.json()
            
            if i % 50 == 0:
                print(f"  Stored {i+1}/{len(files)} files...")
                
        except Exception as e:
            print(f"  Error storing {file_info['filename']}: {e}")
    
    print(f"\n✅ Job {JOB_ID} created with {len(files)} files")
    print(f"   Access via: Import from Store → {JOB_ID}")

if __name__ == '__main__':
    print("=== Scanning Downloads Folder ===")
    files = scan_downloads()
    print(f"Found {len(files)} PDF files in {DOWNLOADS_DIR}")
    
    if len(files) > 0:
        print("\n=== Creating Document Store Job ===")
        create_job_in_document_store(files)
    else:
        print("No PDF files found!")

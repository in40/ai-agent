#!/usr/bin/env python3
"""
Fix missing metadata for documents in Document Store.
Scans document files and creates metadata files with original filenames.
"""
import os
import json
from pathlib import Path
from datetime import datetime

DOCS_BASE = Path("/root/qwen/ai_agent/document-store-mcp-server/data/ingested")

def fix_missing_metadata():
    """Find documents without metadata and create it"""
    
    for job_dir in DOCS_BASE.iterdir():
        if not job_dir.is_dir():
            continue
            
        docs_dir = job_dir / "documents"
        if not docs_dir.exists():
            continue
        
        print(f"\n=== Processing {job_dir.name} ===")
        
        for file_path in docs_dir.iterdir():
            if file_path.suffix in ['.json', '.metadata']:
                continue  # Skip metadata files
            
            doc_id = file_path.stem
            metadata_path = docs_dir / f"{doc_id}.metadata.json"
            
            if metadata_path.exists():
                print(f"  ✓ {doc_id} - metadata exists")
                continue
            
            # Create metadata
            metadata = {
                "original_filename": file_path.name,
                "downloaded_at": datetime.now().isoformat(),
                "job_id": job_dir.name.replace("job_", ""),
                "content_type": f"application/{file_path.suffix[1:]}" if file_path.suffix else "text/plain"
            }
            
            # Try to extract original filename from doc_id if it contains URL-like structure
            if "_" in doc_id:
                parts = doc_id.split("_")
                if len(parts) >= 3:
                    # Assume format: domain_path_filename
                    potential_filename = parts[-1]
                    if "." in potential_filename:
                        metadata["original_filename"] = potential_filename
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  ✗ Created metadata for {doc_id}: {metadata['original_filename']}")

if __name__ == '__main__':
    fix_missing_metadata()
    print("\n=== Done ===")

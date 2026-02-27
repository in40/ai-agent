#!/usr/bin/env python3
"""
Backfill metadata for existing Document Store documents
Reads .source_metadata.json and creates individual .metadata.json files
"""
import os
import json
from pathlib import Path
from datetime import datetime

docstore_base = Path("/root/qwen/ai_agent/document-store-mcp-server/data/ingested")

print("=== Backfilling Document Store Metadata ===\n")

for job_dir in docstore_base.iterdir():
    if not job_dir.is_dir():
        continue
    
    docs_dir = job_dir / "documents"
    if not docs_dir.exists():
        continue
    
    # Read source metadata
    source_meta_path = docs_dir / ".source_metadata.json"
    if not source_meta_path.exists():
        print(f"⊘ Skipping {job_dir.name} - no .source_metadata.json")
        continue
    
    with open(source_meta_path, 'r') as f:
        source_meta = json.load(f)
    
    job_id = source_meta.get('job_id', job_dir.name)
    source_urls = source_meta.get('source_urls', [])
    downloaded_at = source_meta.get('downloaded_at', datetime.utcnow().isoformat())
    
    # Extract source domain from first URL
    source_domain = "unknown"
    if source_urls:
        from urllib.parse import urlparse
        parsed = urlparse(source_urls[0])
        source_domain = parsed.netloc.replace('.', '_')
    
    print(f"✓ Processing {job_dir.name}")
    print(f"  Job ID: {job_id}")
    print(f"  Source: {source_domain}")
    print(f"  Documents: {len(list(docs_dir.glob('*.pdf')))}")
    
    # Create metadata for each PDF
    for pdf_file in docs_dir.glob("*.pdf"):
        doc_id = pdf_file.stem
        metadata_path = docs_dir / f"{doc_id}.metadata.json"
        
        # Skip if metadata already exists
        if metadata_path.exists():
            continue
        
        # Try to match URL from source_urls
        original_url = ""
        for url in source_urls:
            if doc_id in url or os.path.basename(url).replace('.pdf', '') == doc_id:
                original_url = url
                break
        
        # Create metadata
        doc_metadata = {
            'original_filename': pdf_file.name,
            'original_url': original_url,
            'source_website': source_domain,
            'downloaded_at': downloaded_at,
            'job_id': job_id,
            'process_mode': 'download_only',
            'content_type': 'application/pdf'
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(doc_metadata, f, indent=2)
    
    print(f"  ✓ Created metadata files\n")

print("=== Metadata Backfill Complete ===")

#!/usr/bin/env python3
"""Test full extraction flow from document store"""
from backend.services.rag.document_store_client import document_store_client
from rag_component.document_loader import DocumentLoader
import tempfile
import base64
import os

job_id = "job_job_90825d5e7b99_rst_gov_ru:8443"
doc_id = "gost-34"

print(f"Getting document {doc_id} from {job_id}...")
content_result = document_store_client.get_document(job_id, doc_id, format='pdf')

if not content_result.get('success'):
    print(f"Failed: {content_result}")
else:
    doc_data = content_result.get('result', {})
    content = doc_data.get('content', {})
    
    if isinstance(content, dict) and 'content' in content:
        actual_content = content['content']
        print(f"Got base64 content, length: {len(actual_content)}")
        
        # Decode and save
        binary = base64.b64decode(actual_content)
        print(f"Decoded to {len(binary)} bytes")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(binary)
            tmp_path = tmp.name
        
        print(f"Saved to {tmp_path}")
        print("Extracting text (this may take 30-60 seconds)...")
        
        loader = DocumentLoader()
        docs = loader.load_document(tmp_path)
        
        if docs:
            print(f"\n✅ SUCCESS!")
            print(f"Method: {docs[0].metadata.get('extraction_method')}")
            print(f"Text length: {len(docs[0].page_content)}")
            print(f"\nFirst 300 chars:\n{docs[0].page_content[:300]}")
        else:
            print("❌ No docs extracted")
        
        os.unlink(tmp_path)
        print(f"\nCleaned up temp file")

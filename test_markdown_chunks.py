#!/usr/bin/env python3
"""Test script to verify .chunks.json file creation for markdown files"""

import os
import json
import tempfile
import requests

RAG_SERVICE_URL = "http://localhost:5003"

# Create a test markdown file
test_markdown = """# Test Document

## Section 1: Introduction

This is a test document with some content.

## Section 2: Details

More detailed content goes here.

## Section 3: Conclusion

Final thoughts and summary.
"""

# Create temp file
with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
    f.write(test_markdown)
    test_file_path = f.name

print(f"Created test file: {test_file_path}")

try:
    # Test 1: Call smart_ingest_files endpoint
    print("\n=== Test 1: Smart Ingest Files ===")

    with open(test_file_path, "rb") as f:
        files = {"files": ("test_document.md", f, "text/markdown")}
        data = {
            "chunking_strategy": "smart_chunking",
            "ingest_chunks": "false",
            "process_mode": "vector_db",
        }

        response = requests.post(
            f"{RAG_SERVICE_URL}/api/rag/smart_ingest_files",
            files=files,
            data=data,
            timeout=120,
        )

    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Response keys: {result.keys()}")

        # Check for job_id
        if "job_id" in result:
            job_id = result["job_id"]
            print(f"\nJob ID: {job_id}")

            # Wait for job to complete
            import time

            print("Waiting for job to complete...")
            time.sleep(5)

            # Check job status
            job_response = requests.get(f"{RAG_SERVICE_URL}/jobs/{job_id}", timeout=10)

            if job_response.status_code == 200:
                job_data = job_response.json()
                print(f"\n=== Job Status ===")
                print(f"Status: {job_data.get('status')}")
                print(f"Chunks generated: {job_data.get('chunks_generated')}")

                if "result" in job_data and job_data["result"]:
                    print("\n=== Job Result ===")
                    print(
                        f"  Documents processed: {job_data['result'].get('documents_processed', 0)}"
                    )
                    print(
                        f"  Total chunks: {job_data['result'].get('total_chunks', 0)}"
                    )

                    if "document_results" in job_data["result"]:
                        for doc_result in job_data["result"]["document_results"]:
                            print(f"\n  Document: {doc_result.get('filename')}")
                            print(f"  Status: {doc_result.get('status')}")
                            print(f"  Chunks: {doc_result.get('chunks')}")
                            if "chunks_file" in doc_result:
                                chunks_file = doc_result["chunks_file"]
                                print(f"  Chunks file: {chunks_file}")

                                if os.path.exists(chunks_file):
                                    with open(chunks_file, "r", encoding="utf-8") as cf:
                                        chunks_data = json.load(cf)
                                    print(
                                        f"  ✓ Chunks file exists with {len(chunks_data.get('chunks', []))} chunks"
                                    )
                                    print(f"    Doc ID: {chunks_data.get('doc_id')}")
                                    if chunks_data.get("chunks"):
                                        print(
                                            f"    First chunk preview: {chunks_data['chunks'][0].get('content', '')[:100]}..."
                                        )
                                else:
                                    print(f"  ✗ Chunks file NOT found: {chunks_file}")
            else:
                print(f"Failed to get job status: {job_response.status_code}")
                print(job_response.text[:500])
        else:
            print(f"✗ No job_id in response")
            print(f"Response: {result}")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"  Response: {response.text[:500]}")

finally:
    if os.path.exists(test_file_path):
        os.unlink(test_file_path)
        print(f"\nCleaned up test file")

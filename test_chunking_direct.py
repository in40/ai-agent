#!/usr/bin/env python3
"""Test .chunks.json file creation directly via smart_ingestion_enhanced module"""

import os
import json
import sys
import tempfile

# Add project root to path
sys.path.insert(0, "/root/qwen/ai_agent")

from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync

# Create a test markdown file
test_markdown = """# Test Document

## Section 1: Introduction

This is a test document with some content for smart chunking.

The document has multiple sections and should be split into meaningful chunks.

## Section 2: Details

More detailed content goes here with technical information.

## Section 3: Conclusion

Final thoughts and summary of the document content.
"""

# Create temp file
with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
    f.write(test_markdown)
    test_file_path = f.name

print(f"Created test file: {test_file_path}")
print(f"File size: {os.path.getsize(test_file_path)} bytes")

try:
    print("\n=== Calling chunk_document_with_llm_sync ===")

    # Call the chunking function directly
    success, chunks, error, cleaning_method = chunk_document_with_llm_sync(
        file_path=test_file_path, prompt="", filename="test_document.md", timeout=300
    )

    print(f"\n=== Results ===")
    print(f"Success: {success}")
    print(f"Error: {error}")
    print(f"Cleaning method: {cleaning_method}")
    print(f"Chunks count: {len(chunks) if chunks else 0}")

    if chunks:
        print(f"\n=== Sample Chunk ===")
        print(json.dumps(chunks[0], indent=2, ensure_ascii=False))

        # Save chunks to .chunks.json manually (simulating what the fix should do)
        doc_id = "test_doc_" + __import__("uuid").uuid4().hex[:8]
        base_name = "test_document"

        chunks_file = f"/tmp/{base_name}_{doc_id}.chunks.json"
        chunks_data_output = {
            "doc_id": doc_id,
            "filename": "test_document.md",
            "total_chunks": len(chunks),
            "chunking_strategy": "smart_llm",
            "chunks": [
                {
                    "chunk_id": c.get("chunk_id", f"{doc_id}_chunk_{i:04d}"),
                    "chunk_index": i,
                    "content": c.get("content", ""),
                    "section": c.get("section", ""),
                    "title": c.get("title", ""),
                    "token_count": c.get(
                        "token_count", len(c.get("content", "").split())
                    ),
                }
                for i, c in enumerate(chunks)
            ],
        }

        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data_output, f, indent=2, ensure_ascii=False)

        print(f"\n=== Saved .chunks.json to: {chunks_file} ===")

        # Verify the file
        if os.path.exists(chunks_file):
            with open(chunks_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            print(f"✓ File exists with {len(saved_data.get('chunks', []))} chunks")
            print(f"  Doc ID: {saved_data.get('doc_id')}")
            print(f"  Total chunks: {saved_data.get('total_chunks')}")
        else:
            print("✗ File was not created")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()

finally:
    if os.path.exists(test_file_path):
        os.unlink(test_file_path)
        print(f"\nCleaned up test file")

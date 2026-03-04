#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/qwen/ai_agent')
from models.response_generator import ResponseGenerator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL

print(f"Testing LLM: {RESPONSE_LLM_PROVIDER}/{RESPONSE_LLM_MODEL}")
rg = ResponseGenerator()
llm = rg._get_llm_instance()
print(f"LLM instance: {type(llm)}")

# Test with short text
test_text = "This is a test document for chunking. It contains multiple sentences. We want to see if the LLM can chunk it properly."
print(f"Test text length: {len(test_text)} chars")

try:
    from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm
    import tempfile
    import os
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_text)
        temp_path = f.name
    
    print(f"Calling LLM with temp file: {temp_path}")
    success, chunks, error = chunk_document_with_llm(
        file_path=temp_path,
        prompt="",
        filename="test.txt"
    )
    
    print(f"Success: {success}")
    print(f"Chunks: {len(chunks)}")
    if error:
        print(f"Error: {error}")
    
    # Cleanup
    os.unlink(temp_path)
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()

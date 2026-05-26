#!/usr/bin/env python3
"""
Test smart chunking on a large document from Document Store.
"""
import os
import sys
import json
import asyncio
import shutil
import tempfile

# Add project root to path
sys.path.insert(0, '/root/qwen/ai_agent')

# Set environment before any imports
os.environ.setdefault('CONFIG_FILE', '/root/qwen/ai_agent/config/config.json')

from pathlib import Path

# Import chunking function - use the service module path
# The smart_ingestion_enhanced.py uses: from config.settings import ...
# But when running directly, we need to handle the import differently

# First, let's manually import the chunking functions by reading the source
import importlib.util
import importlib.machinery

# Load config.settings directly
spec = importlib.util.spec_from_file_location("settings", "/root/qwen/ai_agent/config/settings.py")
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)

DEFAULT_SMART_CHUNKING_PROMPT = settings.DEFAULT_SMART_CHUNKING_PROMPT if hasattr(settings, 'DEFAULT_SMART_CHUNKING_PROMPT') else None

# We need to define the chunk_document_with_llm_sync function inline
# since importing the whole module has dependency issues

def load_smart_ingestion_module():
    """Load smart_ingestion_enhanced module without full imports."""
    # Read and exec the chunk_document_with_llm_sync function
    with open('/root/qwen/ai_agent/backend/services/rag/smart_ingestion_enhanced.py', 'r') as f:
        source = f.read()

    # Create a module and exec the relevant functions
    mod = importlib.util.module_from_spec(
        importlib.util.spec_from_loader("smart_ingestion", loader=None)
    )

    # We'll need to define dependencies first
    import logging
    logging.basicConfig(level=logging.INFO)

    # Mock the ResponseGenerator
    class MockLLM:
        def __init__(self):
            import asyncio
            self._async = True

        async def ainvoke(self, prompt):
            import asyncio
            from langchain_core.messages import AIMessage
            # For now, return a mock response
            await asyncio.sleep(0.1)
            return AIMessage(content='{"chunks": [], "total_chunks": 0}')

    class MockResponseGenerator:
        def _get_llm_instance(self, provider, model):
            return MockLLM()

    mod.ResponseGenerator = MockResponseGenerator
    mod.logger = logging.getLogger(__name__)

    # Execute the module with minimal dependencies
    exec(source, mod.__dict__)

    return mod

# Document Store paths
JOB_ID = "job_job_3ad1455bec52_rst_gov_ru:8443"
DOC_ID = "gost-34_bdb2abdc"
BASE_DIR = Path("/root/qwen/ai_agent/document-store-mcp-server/data/ingested")
DOCS_DIR = BASE_DIR / JOB_ID / "documents"

def main():
    # Get document from Document Store
    md_path = DOCS_DIR / f"{DOC_ID}.md"

    if not md_path.exists():
        print(f"ERROR: {md_path} not found")
        return

    # Read the document
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Document loaded: {len(content)} characters")
    print(f"First 500 chars:\n{content[:500]}...")

    # Create temp file for processing
    temp_fd, temp_path = tempfile.mkstemp(suffix='.md')
    os.close(temp_fd)

    try:
        # Write document to temp file
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Chunk with LLM - use a direct approach
        print(f"\n=== Starting chunking with LLM ===")

        # Load document content using DocumentLoader
        sys.path.insert(0, '/root/qwen/ai_agent/rag_component')
        from rag_component.document_loader import DocumentLoader

        document_loader = DocumentLoader()
        docs = document_loader.load_document(temp_path)
        print(f"Loaded {len(docs)} document parts")

        document_content = ""
        for doc in docs:
            document_content += doc.page_content + "\n"

        print(f"Total content: {len(document_content)} characters")

        # Use the existing LLM infrastructure
        sys.path.insert(0, '/root/qwen/ai_agent/backend')
        sys.path.insert(0, '/root/qwen/ai_agent/models')

        from models.response_generator import ResponseGenerator
        from rag_component.main import RAGOrchestrator

        print(f"Using LLM provider: {settings.RESPONSE_LLM_PROVIDER}, model: {settings.RESPONSE_LLM_MODEL}")

        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=settings.RESPONSE_LLM_PROVIDER,
            model=settings.RESPONSE_LLM_MODEL
        )

        # Use default prompt from the module
        from backend.services.rag import smart_ingestion_enhanced
        prompt = smart_ingestion_enhanced.DEFAULT_SMART_CHUNKING_PROMPT.format(input_text=document_content[:50000])

        print(f"Prompt length: {len(prompt)} chars")
        print(f"Calling LLM...")

        import asyncio
        response = asyncio.run(llm.ainvoke(prompt))
        response_content = response.content if hasattr(response, 'content') else str(response)

        print(f"LLM response length: {len(response_content)} chars")
        print(f"Response preview: {response_content[:500]}...")

        # Parse JSON response
        import re
        from backend.services.rag.json_utils import parse_json_robust

        cleaned_response = re.sub(r'\[THINK\][\s\S]*?\[/THINK\]', '', response_content)
        cleaned_response = cleaned_response.strip()

        # Remove markdown code blocks
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        print(f"Cleaned response length: {len(cleaned_response)} chars")

        # Extract JSON object
        json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
        if json_match:
            json_str = json_match.group(0)
            print(f"Found JSON object: {len(json_str)} chars")
            chunking_result = parse_json_robust(json_str, default_on_error={'chunks': []})

            if isinstance(chunking_result, dict):
                chunks = chunking_result.get('chunks', [])
                print(f"Extracted {len(chunks)} chunks")
            else:
                chunks = []
                print("Unexpected chunking result type")
        else:
            print("No JSON found in response")
            chunks = []
            return

        # Show chunk summary
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i+1}:")
            print(f"  - Section: {chunk.get('section', 'N/A')}")
            print(f"  - Title: {chunk.get('title', 'N/A')}")
            print(f"  - Content length: {len(chunk.get('content', ''))} chars")
            print(f"  - Content preview: {chunk.get('content', '')[:200]}...")

        if len(chunks) > 3:
            print(f"\n... and {len(chunks) - 3} more chunks")

        # Save chunks to file
        chunks_path = DOCS_DIR / f"{DOC_ID}.chunks.json"
        chunks_data = {
            "doc_id": DOC_ID,
            "filename": f"{DOC_ID}.md",
            "total_chunks": len(chunks),
            "chunking_strategy": "smart_chunking",
            "chunks": chunks
        }

        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)

        print(f"\n=== Saved chunks to {chunks_path} ===")
        print(f"File size: {chunks_path.stat().st_size} bytes")
        print(f"=== Chunking completed successfully ===")

    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except:
            pass

if __name__ == "__main__":
    main()

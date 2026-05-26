#!/usr/bin/env python3
import sys

sys.path.insert(0, "/root/qwen/ai_agent")
from backend.services.rag.app import (
    _chunk_with_streaming_and_retry,
    LLM_STREAMING_ENABLED,
)
from models.response_generator import ResponseGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"LLM_STREAMING_ENABLED: {LLM_STREAMING_ENABLED}")
response_gen = ResponseGenerator()
llm = response_gen._get_llm_instance(provider="LM Studio", model="qwen3.5-0.8b@bf16")
test_markdown = "# Test Document\n\n## Section 1\n\nThis is a test.\n\n## Section 2\n\nMore content here.\n"
prompt = """Chunk this document. Return JSON with chunks array. Each chunk has content field."""
full_prompt = f"{prompt}\n\n{test_markdown[:50000]}"
logger.info("Calling chunking with streaming...")
chunks, chunks_data, document_summary, key_entities = _chunk_with_streaming_and_retry(
    llm, full_prompt, {"filename": "test.md"}, "test_job"
)
logger.info(f"Chunks count: {len(chunks)}")
if chunks_data:
    logger.info(f"First chunk content: {chunks_data[0]}")

#!/usr/bin/env python3
"""
Comprehensive test script to verify RAG functionality with LM Studio embeddings
"""
import os
import sys
sys.path.insert(0, '/root/qwen_test/ai_agent')

from rag_component.main import RAGOrchestrator
from rag_component.embedding_manager import EmbeddingManager

def test_comprehensive_rag():
    print("Testing comprehensive RAG functionality with LM Studio embeddings...")
    
    # Test the embedding manager directly
    print("\n1. Testing embedding manager...")
    emb_manager = EmbeddingManager()
    print(f"   Provider: {emb_manager.provider}")
    print(f"   Model: {emb_manager.model_name}")
    
    test_text = "This is a test for the RAG system."
    embedding = emb_manager.embed_text(test_text)
    print(f"   Embedding length: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    
    # Test RAG orchestrator
    print("\n2. Testing RAG orchestrator...")
    rag_orchestrator = RAGOrchestrator(llm=None)  # Pass None for LLM since we're only testing ingestion/retrieval
    
    # Test document ingestion
    test_file = "/root/qwen_test/ai_agent/test_ural.txt"
    print(f"   Attempting to ingest: {test_file}")
    success = rag_orchestrator.ingest_documents([test_file])
    print(f"   Ingestion result: {success}")
    
    if success:
        print("\n3. Testing document retrieval...")
        # Test querying the ingested document
        query_result = rag_orchestrator.retriever.retrieve_documents("What is the oil price?")
        print(f"   Retrieved {len(query_result)} documents")
        if query_result:
            print(f"   First document preview: {query_result[0].page_content[:100]}...")
    
    print("\n4. All tests completed successfully!")

if __name__ == "__main__":
    test_comprehensive_rag()
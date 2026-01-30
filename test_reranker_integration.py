#!/usr/bin/env python3
"""
Test script to verify the reranker integration with the RAG component.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from rag_component import RAGOrchestrator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
from models.response_generator import ResponseGenerator

def test_reranker_integration():
    """Test the reranker integration with the RAG component."""
    print("Testing Reranker Integration...")
    
    # Initialize the response generator to get an LLM instance
    response_generator = ResponseGenerator()
    llm = response_generator._get_llm_instance(
        provider=RESPONSE_LLM_PROVIDER,
        model=RESPONSE_LLM_MODEL
    )
    
    # Initialize the RAG orchestrator with the LLM
    rag_orchestrator = RAGOrchestrator(llm=llm)
    
    # Test query
    test_query = "What is the capital of France?"
    
    print(f"Query: {test_query}")
    
    # Retrieve documents using the RAG orchestrator (this should now use reranking if enabled)
    retrieved_docs = rag_orchestrator.retrieve_documents(test_query, top_k=5)
    
    print(f"Retrieved {len(retrieved_docs)} documents:")
    for i, doc in enumerate(retrieved_docs):
        print(f"  Doc {i+1}: Score={doc.get('score', 'N/A')}, Source={doc.get('source', 'N/A')}")
        print(f"    Content preview: {doc.get('content', '')[:100]}...")
        print(f"    Reranked: {doc.get('reranked', False)}")
        print()
    
    print("Reranker integration test completed.")


if __name__ == "__main__":
    test_reranker_integration()
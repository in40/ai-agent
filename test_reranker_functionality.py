#!/usr/bin/env python3
"""
Test script to verify the reranker functionality with simulated documents.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from rag_component.reranker import Reranker
from rag_component.config import RERANKER_ENABLED


def test_reranker_functionality():
    """Test the reranker functionality with simulated documents."""
    print("Testing Reranker Functionality...")
    
    # Initialize the reranker
    reranker = Reranker()
    
    print(f"Reranker enabled: {RERANKER_ENABLED}")
    print(f"Model: {reranker.model}")
    print(f"Base URL: {reranker.base_url}")
    
    if not RERANKER_ENABLED:
        print("Reranker is disabled. Please set RERANKER_ENABLED=true in your environment.")
        return
    
    # Simulated documents
    query = "What is the capital of France?"
    documents = [
        {
            "content": "Paris is the capital and most populous city of France. It is located in the north-central part of the country.",
            "title": "France Capital",
            "source": "Geography Book",
            "metadata": {"author": "John Doe"},
            "score": 0.7
        },
        {
            "content": "London is the capital city of England and the United Kingdom. It is located on the River Thames in south-east England.",
            "title": "UK Capital",
            "source": "Geography Book",
            "metadata": {"author": "Jane Smith"},
            "score": 0.6
        },
        {
            "content": "Berlin is the capital and largest city of Germany. It is located in northeastern Germany.",
            "title": "Germany Capital",
            "source": "Geography Book",
            "metadata": {"author": "Hans Mueller"},
            "score": 0.5
        },
        {
            "content": "The weather today is sunny with a high of 25 degrees Celsius.",
            "title": "Weather Report",
            "source": "News Website",
            "metadata": {"author": "Weather Service"},
            "score": 0.3
        }
    ]
    
    print(f"\nOriginal documents (before reranking):")
    for i, doc in enumerate(documents):
        print(f"  Doc {i+1}: Score={doc.get('score', 'N/A')}, Content preview: {doc.get('content', '')[:50]}...")
    
    # Test reranking
    print(f"\nTesting reranking for query: '{query}'")
    reranked_docs = reranker.rerank_documents(query, documents, top_k=3)
    
    print(f"\nReranked documents (after reranking):")
    for i, doc in enumerate(reranked_docs):
        print(f"  Doc {i+1}: Score={doc.get('score', 'N/A')}, Reranked={doc.get('reranked', False)}, Content preview: {doc.get('content', '')[:50]}...")
    
    print("\nReranker functionality test completed.")


if __name__ == "__main__":
    test_reranker_functionality()
#!/usr/bin/env python3
"""
Test script to verify the updated reranker implementation using embeddings endpoint.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from rag_component.reranker import Reranker


def test_updated_reranker():
    """Test the updated reranker implementation."""
    print("Testing updated reranker implementation using embeddings endpoint...")
    
    # Initialize the reranker
    reranker = Reranker()
    
    print(f"Reranker enabled: {reranker.enabled}")
    print(f"Model: {reranker.model}")
    print(f"Base URL: {reranker.base_url}")
    
    if not reranker.enabled:
        print("Reranker is disabled. Please set RERANKER_ENABLED=true in your environment.")
        return False
    
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
        },
        {
            "content": "France is a country in Europe known for its art, cuisine, and culture.",
            "title": "About France",
            "source": "Travel Guide",
            "metadata": {"author": "Travel Expert"},
            "score": 0.4
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
        print(f"  Doc {i+1}: Score={doc.get('score', 'N/A'):.4f}, Reranked={doc.get('reranked', False)}, Content preview: {doc.get('content', '')[:50]}...")
    
    if len(reranked_docs) > 0:
        print(f"\n✓ Reranking test completed successfully!")
        print(f"  - Original documents: {len(documents)}")
        print(f"  - Returned documents: {len(reranked_docs)}")
        print(f"  - Top document: '{reranked_docs[0].get('content', '')[:60]}...'")
        return True
    else:
        print(f"\n✗ Reranking test failed - no documents returned")
        return False


if __name__ == "__main__":
    success = test_updated_reranker()
    if success:
        print("\n✓ Updated reranker implementation test completed successfully!")
    else:
        print("\n✗ Updated reranker implementation test failed.")
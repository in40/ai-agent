#!/usr/bin/env python3
"""
Test script to temporarily adjust similarity threshold and test Russian query
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_with_lower_threshold():
    """Test Russian query with a lower similarity threshold."""
    print("Testing Russian query with lower similarity threshold...")
    
    # Temporarily set the threshold to 0.6 to allow the documents to be returned
    os.environ['RAG_SIMILARITY_THRESHOLD'] = '0.6'
    
    try:
        # Import required modules after setting the environment variable
        from rag_component.main import RAGOrchestrator
        from rag_component.retriever import Retriever
        from rag_component.config import RAG_SIMILARITY_THRESHOLD
        
        print(f"Updated similarity threshold: {RAG_SIMILARITY_THRESHOLD}")
        
        # Initialize the RAG orchestrator without an LLM for testing retrieval only
        rag_orchestrator = RAGOrchestrator(llm=None)
        
        # Russian query from the user
        russian_query = "Для биномиального закона распределения 256 независимых данных"
        print(f"Testing query: {russian_query}")
        
        # Try to retrieve documents using get_relevant_documents method
        print("\nTrying with get_relevant_documents method (which applies threshold)...")
        relevant_docs = rag_orchestrator.retriever.get_relevant_documents(russian_query)
        
        print(f"Number of relevant documents: {len(relevant_docs)}")
        
        if relevant_docs:
            print("\nRelevant documents:")
            for i, doc in enumerate(relevant_docs):
                print(f"\nDocument {i+1}:")
                print(f"  Score: {doc['score']}")
                print(f"  Content preview: {doc['content'][:200]}...")
                print(f"  Source: {doc['source']}")
        else:
            print("\nStill no relevant documents found.")
            
        # Reset the threshold back to original value
        os.environ['RAG_SIMILARITY_THRESHOLD'] = '0.7'
        
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_lower_threshold()
    if success:
        print("\n✓ Test with lower threshold completed!")
    else:
        print("\n✗ Test with lower threshold failed.")
        sys.exit(1)
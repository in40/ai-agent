#!/usr/bin/env python3
"""
Debug script to test Russian query functionality in RAG
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_russian_query():
    """Test Russian query functionality."""
    print("Testing Russian query functionality...")
    
    try:
        # Import required modules
        from rag_component.main import RAGOrchestrator
        
        # Initialize the RAG orchestrator without an LLM for testing retrieval only
        rag_orchestrator = RAGOrchestrator(llm=None)
        
        # Russian query from the user
        russian_query = "Для биномиального закона распределения 256 независимых данных"
        print(f"Testing query: {russian_query}")
        
        # Try to retrieve documents
        print("\nAttempting to retrieve documents...")
        retrieved_docs = rag_orchestrator.retriever.retrieve_documents_with_scores(russian_query)
        
        print(f"Number of documents retrieved: {len(retrieved_docs)}")
        
        if retrieved_docs:
            print("\nRetrieved documents with scores:")
            for i, (doc, score) in enumerate(retrieved_docs):
                print(f"\nDocument {i+1}:")
                print(f"  Score: {score}")
                print(f"  Content preview: {doc.page_content[:200]}...")
                print(f"  Metadata: {doc.metadata}")
        else:
            print("\nNo documents retrieved.")
            
        # Also try with get_relevant_documents method
        print("\nTrying with get_relevant_documents method...")
        relevant_docs = rag_orchestrator.retriever.get_relevant_documents(russian_query)
        
        print(f"Number of relevant documents: {len(relevant_docs)}")
        
        if relevant_docs:
            print("\nRelevant documents:")
            for i, doc in enumerate(relevant_docs):
                print(f"\nDocument {i+1}:")
                print(f"  Score: {doc['score']}")
                print(f"  Content preview: {doc['content'][:200]}...")
                print(f"  Source: {doc['source']}")
                print(f"  Metadata: {doc['metadata']}")
        else:
            print("\nNo relevant documents found.")
            
        # Check if the vector store is empty
        print(f"\nVector store type: {rag_orchestrator.vector_store_manager.store_type}")
        print(f"Collection name: {rag_orchestrator.vector_store_manager.collection_name}")
        
        # Try a simple test query to see if anything is in the database
        test_query = "test"
        print(f"\nTesting with simple query: {test_query}")
        test_docs = rag_orchestrator.retriever.get_relevant_documents(test_query)
        print(f"Number of documents for 'test' query: {len(test_docs)}")
        
        return True
        
    except Exception as e:
        print(f"Error during Russian query test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_russian_query()
    if success:
        print("\n✓ Russian query test completed!")
    else:
        print("\n✗ Russian query test failed.")
        sys.exit(1)
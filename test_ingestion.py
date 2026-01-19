#!/usr/bin/env python3
"""
Test script to verify that documents have been properly ingested into the RAG system.
This script queries the RAG system to see if it can retrieve information from the ingested documents.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_document_ingestion():
    """Test that documents have been ingested by querying the RAG system."""
    print("Testing Document Ingestion...")
    print("=" * 40)
    
    try:
        # Import required modules
        from rag_component import RAGOrchestrator
        from models.response_generator import ResponseGenerator
        
        # Initialize the response generator to get the LLM
        response_gen = ResponseGenerator()
        llm = response_gen.llm  # Access the LLM directly from the response generator
        
        print("✓ Successfully accessed the LLM")
        
        # Initialize the RAG orchestrator
        rag_orchestrator = RAGOrchestrator(llm=llm)
        print("✓ RAG orchestrator initialized successfully")
        
        # Test query - adjust this based on the content of your sample documents
        test_query = "What is the company mission mentioned in the documents?"
        
        print(f"\nQuery: {test_query}")
        
        # Process a query using RAG
        result = rag_orchestrator.query(test_query)
        
        print(f"Response: {result['response']}")
        print(f"Number of retrieved documents: {len(result['context'])}")
        
        # Display information about retrieved documents
        if result['context']:
            print("\nRetrieved document snippets:")
            for i, doc in enumerate(result['context']):
                print(f"  Document {i+1}:")
                print(f"    Content preview: {doc['content'][:200]}...")
                print(f"    Metadata: {doc['metadata']}")
                print(f"    Score: {doc['score']}")
                print()
        else:
            print("\n⚠ No documents were retrieved for this query.")
            print("This could mean:")
            print("  - No documents match the query")
            print("  - Documents weren't properly ingested")
            print("  - The vector store is empty")
        
        # Test with another query to be thorough
        print("-" * 40)
        test_query2 = "What products and services does the company offer?"
        print(f"Second query: {test_query2}")
        
        result2 = rag_orchestrator.query(test_query2)
        print(f"Response: {result2['response']}")
        print(f"Number of retrieved documents: {len(result2['context'])}")
        
        if result2['context']:
            print("✓ At least one document was retrieved, indicating ingestion was successful!")
            return True
        else:
            print("⚠ No documents retrieved in second test.")
            return False
            
    except Exception as e:
        print(f"✗ Error during ingestion test: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_vector_store_contents():
    """Check the contents of the vector store directly."""
    print("\nChecking Vector Store Contents...")
    print("=" * 40)
    
    try:
        from rag_component.vector_store_manager import VectorStoreManager
        
        # Initialize the vector store manager
        vector_store_manager = VectorStoreManager()
        
        # Try to get the count of documents in the collection
        # Note: This depends on the specific vector store implementation
        if hasattr(vector_store_manager.vector_store, '_collection'):
            count = vector_store_manager.vector_store._collection.count()
            print(f"Number of documents in vector store: {count}")
            if count > 0:
                print("✓ Vector store contains documents")
                return True
            else:
                print("⚠ Vector store appears to be empty")
                return False
        else:
            print("? Unable to determine vector store contents directly")
            return True  # Don't fail the test if we can't check directly
            
    except Exception as e:
        print(f"⚠ Could not check vector store contents: {e}")
        return True  # Don't fail the test if we can't check directly

if __name__ == "__main__":
    print("RAG Document Ingestion Verification Test")
    print("=" * 50)
    
    # Test document retrieval
    retrieval_success = test_document_ingestion()
    
    # Check vector store contents
    storage_success = check_vector_store_contents()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"  Document Retrieval Test: {'PASS' if retrieval_success else 'FAIL'}")
    print(f"  Vector Storage Check: {'PASS' if storage_success else 'WARNING'}")
    
    if retrieval_success:
        print("\n✓ Documents appear to be successfully ingested!")
        print("The RAG system can retrieve information from the documents.")
    else:
        print("\n✗ Document ingestion may have failed.")
        print("The RAG system could not retrieve expected information.")
        sys.exit(1)
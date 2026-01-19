#!/usr/bin/env python3
"""
Simple test to verify that documents are ingested without requiring model downloads.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ingestion_verification():
    """Test that documents are ingested by checking the vector store directly."""
    print("Verifying document ingestion...")
    
    try:
        # Import the vector store manager directly
        from rag_component.vector_store_manager import VectorStoreManager
        
        # Initialize the vector store manager
        vector_store_manager = VectorStoreManager()
        
        print("✓ Vector store manager initialized")
        
        # Check if the vector store has documents
        # We'll use a direct approach to check the collection
        collection = vector_store_manager.vector_store._client.get_collection(name=vector_store_manager.collection_name)
        
        # Get the count of documents in the collection
        count = collection.count()
        print(f"✓ Vector store contains {count} documents")
        
        if count > 0:
            print("✓ Documents have been successfully ingested!")
            
            # Get a sample of documents to verify content
            results = collection.peek(limit=2)
            print(f"Sample documents: {len(results['ids'])} retrieved")
            
            for i, doc_id in enumerate(results['ids']):
                print(f"  Document {i+1}: ID={doc_id}")
                
            return True
        else:
            print("⚠ Vector store is empty - documents may not have been ingested")
            return False
            
    except Exception as e:
        print(f"✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ingestion_verification()
    if success:
        print("\n✓ Document ingestion verification completed successfully!")
    else:
        print("\n✗ Document ingestion verification failed.")
        sys.exit(1)
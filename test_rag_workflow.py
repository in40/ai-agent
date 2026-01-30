#!/usr/bin/env python3
"""
Test script to simulate the RAG workflow that might be causing the 500 error.
"""

import os

def test_vector_store_init():
    """Test the vector store initialization which might be causing the 500 error."""
    print("Testing vector store initialization...")

    # Set the environment to use Qdrant as the vector store type to trigger the test embedding
    os.environ['RAG_VECTOR_STORE_TYPE'] = 'qdrant'
    
    try:
        from rag_component.vector_store_manager import VectorStoreManager
        print("Attempting to initialize VectorStoreManager...")
        
        # This might cause the 500 error if there's an issue with embedding generation
        vs_manager = VectorStoreManager()
        
        print(f"Vector store type: {vs_manager.store_type}")
        print("✅ VectorStoreManager initialized successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during VectorStoreManager initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_embedding_query():
    """Test the embed_query method directly which is used in the vector store initialization."""
    print("\nTesting direct embed_query method...")
    
    try:
        from rag_component.embedding_manager import EmbeddingManager
        emb_manager = EmbeddingManager()
        
        # This is the exact call that happens in vector_store_manager.py line ~110
        print("Calling embed_query('test')...")
        test_embedding = emb_manager.embeddings.embed_query("test")
        embedding_size = len(test_embedding)
        
        print(f"✅ Test embedding successful, size: {embedding_size}")
        print(f"Sample values: {test_embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during embed_query test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity_search():
    """Test the similarity search functionality that might be used in 'Document Lookup'."""
    print("\nTesting similarity search functionality...")
    
    try:
        from rag_component.vector_store_manager import VectorStoreManager
        vs_manager = VectorStoreManager()
        
        # Try a similarity search
        results = vs_manager.similarity_search("test query", top_k=3)
        
        print(f"✅ Similarity search successful, found {len(results)} results")
        return True
        
    except Exception as e:
        print(f"❌ Error during similarity search: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = test_direct_embedding_query()
    success2 = test_vector_store_init()  # Only run this if the first test passes
    success3 = test_similarity_search() if success1 and success2 else False

    if success1 and success2 and success3:
        print("\n✅ All tests passed! The RAG system appears to be working correctly.")
    else:
        print("\n❌ Some tests failed. There may be issues with the RAG system.")
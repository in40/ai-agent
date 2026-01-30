#!/usr/bin/env python3
"""
Test script to verify that the embedding manager works with T5 encoder models.
"""

import os
from rag_component.embedding_manager import EmbeddingManager

def test_t5_embedding():
    """Test the embedding manager with a T5 encoder model."""
    print("Testing T5 encoder embedding model...")

    # Clear RAG-specific environment variables to prevent interference
    if 'RAG_EMBEDDING_PROVIDER' in os.environ:
        del os.environ['RAG_EMBEDDING_PROVIDER']
    if 'RAG_EMBEDDING_MODEL' in os.environ:
        del os.environ['RAG_EMBEDDING_MODEL']
    if 'RAG_EMBEDDING_HOSTNAME' in os.environ:
        del os.environ['RAG_EMBEDDING_HOSTNAME']
    if 'RAG_EMBEDDING_PORT' in os.environ:
        del os.environ['RAG_EMBEDDING_PORT']

    # Set environment variables to use the T5 encoder model
    os.environ['EMBEDDING_PROVIDER'] = 'huggingface'
    os.environ['EMBEDDING_MODEL'] = 'frida'  # This should trigger the T5 encoder path
    # Temporarily override hostname and port to avoid LM Studio path
    os.environ['EMBEDDING_HOSTNAME'] = 'localhost'
    os.environ['EMBEDDING_PORT'] = '8000'  # Use a different port to avoid LM Studio detection

    try:
        # Create an embedding manager instance
        emb_manager = EmbeddingManager()

        print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")

        # Test embedding a simple text
        test_text = "This is a test document for T5 encoder embedding."
        embedding = emb_manager.embed_text(test_text)

        print(f"T5 encoder embedding successful. Length: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")

        # Test embedding multiple texts
        test_texts = [
            "First test document for T5 encoder.",
            "Second test document for T5 encoder.",
            "Third test document for T5 encoder."
        ]

        embeddings = emb_manager.embed_texts(test_texts)
        print(f"Multiple T5 encoder embedding successful. Number of embeddings: {len(embeddings)}")

        for i, emb in enumerate(embeddings):
            print(f"  Text {i+1} embedding length: {len(emb)}")

        print("✅ T5 encoder embedding tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error during T5 encoder embedding: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regular_embedding():
    """Test the embedding manager with a regular model to ensure we didn't break anything."""
    print("\nTesting regular embedding model...")

    # Clear RAG-specific environment variables to prevent interference
    if 'RAG_EMBEDDING_PROVIDER' in os.environ:
        del os.environ['RAG_EMBEDDING_PROVIDER']
    if 'RAG_EMBEDDING_MODEL' in os.environ:
        del os.environ['RAG_EMBEDDING_MODEL']
    if 'RAG_EMBEDDING_HOSTNAME' in os.environ:
        del os.environ['RAG_EMBEDDING_HOSTNAME']
    if 'RAG_EMBEDDING_PORT' in os.environ:
        del os.environ['RAG_EMBEDDING_PORT']

    # Set environment variables to use a regular model
    os.environ['EMBEDDING_PROVIDER'] = 'huggingface'
    os.environ['EMBEDDING_MODEL'] = 'all-MiniLM-L6-v2'
    # Temporarily override hostname and port to avoid LM Studio path
    os.environ['EMBEDDING_HOSTNAME'] = 'localhost'
    os.environ['EMBEDDING_PORT'] = '8000'  # Use a different port to avoid LM Studio detection

    try:
        # Create an embedding manager instance
        emb_manager = EmbeddingManager()

        print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")

        # Test embedding a simple text
        test_text = "This is a test document for regular embedding."
        embedding = emb_manager.embed_text(test_text)

        print(f"Regular embedding successful. Length: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")

        print("✅ Regular embedding tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error during regular embedding: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_t5_embedding()
    success2 = test_regular_embedding()
    
    if success1 and success2:
        print("\n🎉 All embedding tests passed!")
    else:
        print("\n⚠️  Some tests failed.")
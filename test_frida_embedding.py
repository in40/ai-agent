#!/usr/bin/env python3
"""
Test script specifically for Frida T5 encoder model.
"""

import os
from rag_component.embedding_manager import EmbeddingManager

def test_frida_embedding():
    """Test the embedding manager with the Frida T5 encoder model."""
    print("Testing Frida T5 encoder embedding model...")

    # Clear all environment variables to ensure clean test
    env_vars_to_clear = [
        'EMBEDDING_PROVIDER', 'EMBEDDING_MODEL', 'EMBEDDING_HOSTNAME', 'EMBEDDING_PORT', 'EMBEDDING_API_PATH',
        'RAG_EMBEDDING_PROVIDER', 'RAG_EMBEDDING_MODEL', 'RAG_EMBEDDING_HOSTNAME', 'RAG_EMBEDDING_PORT'
    ]
    
    for var in env_vars_to_clear:
        if var in os.environ:
            del os.environ[var]

    # Set environment variables to use the Frida T5 encoder model
    os.environ['EMBEDDING_PROVIDER'] = 'huggingface'  # Explicitly set to huggingface
    os.environ['EMBEDDING_MODEL'] = 'frida'  # This should trigger the T5 encoder path
    
    # Don't set hostname/port to avoid LM Studio path

    try:
        # Create an embedding manager instance
        emb_manager = EmbeddingManager()

        print(f"Embedding manager provider: {emb_manager.provider}")
        print(f"Embedding manager model_name: {emb_manager.model_name}")
        print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")

        # Test embedding a simple text
        test_text = "This is a test document for Frida T5 encoder embedding."
        embedding = emb_manager.embed_text(test_text)

        print(f"Frida T5 encoder embedding successful. Length: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")

        # Test embedding multiple texts
        test_texts = [
            "First test document for Frida T5 encoder.",
            "Second test document for Frida T5 encoder.",
            "Third test document for Frida T5 encoder."
        ]

        embeddings = emb_manager.embed_texts(test_texts)
        print(f"Multiple Frida T5 encoder embedding successful. Number of embeddings: {len(embeddings)}")

        for i, emb in enumerate(embeddings):
            print(f"  Text {i+1} embedding length: {len(emb)}")

        print("✅ Frida T5 encoder embedding tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error during Frida T5 encoder embedding: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_frida_embedding()

    if success:
        print("\n🎉 Frida T5 encoder embedding test passed!")
    else:
        print("\n⚠️  Frida T5 encoder embedding test failed.")
#!/usr/bin/env python3
"""
Final test to verify that the system works with the original .env configuration
but prioritizes T5EncoderEmbeddings for 'frida' model.
"""

import os

def test_with_original_config():
    """Test with the original .env configuration but ensure 'frida' uses T5EncoderEmbeddings."""
    print("Testing with original .env configuration but 'frida' model...")

    # Use the original configuration from .env
    # EMBEDDING_PROVIDER="lm studio" and EMBEDDING_MODEL=frida
    # The system should now prioritize T5EncoderEmbeddings for 'frida' regardless of provider
    
    try:
        # Create an embedding manager instance
        from rag_component.embedding_manager import EmbeddingManager
        emb_manager = EmbeddingManager()

        print(f"Embedding manager provider: {emb_manager.provider}")
        print(f"Embedding manager model_name: {emb_manager.model_name}")
        print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")

        # Check if it's using T5EncoderEmbeddings despite the provider being "lm studio"
        is_t5_embeddings = type(emb_manager.embeddings).__name__ == 'T5EncoderEmbeddings'
        print(f"Using T5EncoderEmbeddings: {is_t5_embeddings}")
        
        if is_t5_embeddings:
            print("✅ Successfully using T5EncoderEmbeddings even with 'lm studio' provider!")
            
            # Test embedding a simple text
            test_text = "This is a test document for Frida T5 encoder embedding."
            embedding = emb_manager.embed_text(test_text)
            
            print(f"Frida T5 encoder embedding successful. Length: {len(embedding)}")
            print(f"First 10 values: {embedding[:10]}")
            
            return True
        else:
            print(f"❌ Expected T5EncoderEmbeddings, got {type(emb_manager.embeddings).__name__}")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_with_original_config()

    if success:
        print("\n🎉 Final test passed! The system now correctly uses T5EncoderEmbeddings for 'frida' model regardless of provider setting.")
    else:
        print("\n⚠️  Final test failed.")
#!/usr/bin/env python3
"""
Test script to force using HuggingFace provider for Frida T5 encoder model.
"""

import os

def test_frida_embedding_forced_hf():
    """Test the embedding manager with Frida T5 encoder model forced to use HuggingFace."""
    print("Testing Frida T5 encoder embedding model with forced HuggingFace provider...")

    # Temporarily override the environment variables
    original_env = {}
    env_vars_to_override = [
        'EMBEDDING_PROVIDER', 'RAG_EMBEDDING_PROVIDER'
    ]
    
    # Save original values
    for var in env_vars_to_override:
        original_env[var] = os.environ.get(var)
    
    # Set to use HuggingFace
    os.environ['EMBEDDING_PROVIDER'] = 'huggingface'
    os.environ['RAG_EMBEDDING_PROVIDER'] = 'huggingface'
    os.environ['EMBEDDING_MODEL'] = 'frida'
    os.environ['RAG_EMBEDDING_MODEL'] = 'frida'
    
    # Clear hostname and port to avoid LM Studio detection
    if 'EMBEDDING_HOSTNAME' in os.environ:
        del os.environ['EMBEDDING_HOSTNAME']
    if 'EMBEDDING_PORT' in os.environ:
        del os.environ['EMBEDDING_PORT']
    if 'RAG_EMBEDDING_HOSTNAME' in os.environ:
        del os.environ['RAG_EMBEDDING_HOSTNAME']
    if 'RAG_EMBEDDING_PORT' in os.environ:
        del os.environ['RAG_EMBEDDING_PORT']

    try:
        # Create an embedding manager instance
        from rag_component.embedding_manager import EmbeddingManager
        emb_manager = EmbeddingManager()

        print(f"Embedding manager provider: {emb_manager.provider}")
        print(f"Embedding manager model_name: {emb_manager.model_name}")
        print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")

        # Test embedding a simple text
        test_text = "This is a test document for Frida T5 encoder embedding."
        
        # Try to embed the text
        embedding = emb_manager.embed_text(test_text)

        print(f"Frida T5 encoder embedding successful. Length: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")

        print("✅ Frida T5 encoder embedding tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error during Frida T5 encoder embedding: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original environment variables
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]


def test_with_exception_handling():
    """Test with additional exception handling to see what specific error occurs."""
    print("\nTesting with more specific error handling...")

    # Set environment for T5 model with HuggingFace
    os.environ['EMBEDDING_PROVIDER'] = 'huggingface'
    os.environ['EMBEDDING_MODEL'] = 'frida'
    
    # Remove hostname/port to avoid LM Studio path
    for var in ['EMBEDDING_HOSTNAME', 'EMBEDDING_PORT']:
        if var in os.environ:
            del os.environ[var]

    try:
        from rag_component.embedding_manager import EmbeddingManager
        emb_manager = EmbeddingManager()
        
        print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
        
        # Try a simple operation to see if model loads properly
        if hasattr(emb_manager.embeddings, 'tokenizer'):
            print("Tokenizer loaded successfully")
        if hasattr(emb_manager.embeddings, 'model'):
            print("Model loaded successfully")
            if hasattr(emb_manager.embeddings.model, 'config'):
                print(f"Model config loaded, hidden size: {emb_manager.embeddings.model.config.hidden_size}")
        
        return True
    except Exception as e:
        print(f"Detailed error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = test_frida_embedding_forced_hf()
    success2 = test_with_exception_handling()

    if success1 and success2:
        print("\n🎉 Frida T5 encoder embedding tests passed!")
    else:
        print("\n⚠️  Some Frida T5 encoder embedding tests failed.")
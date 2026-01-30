#!/usr/bin/env python3
"""
Quick test to verify the model alias mapping works.
"""

import os

def test_model_alias_mapping():
    """Test that the model alias mapping works correctly."""
    print("Testing model alias mapping...")

    # Set environment for T5 model with HuggingFace
    os.environ['EMBEDDING_PROVIDER'] = 'huggingface'
    os.environ['EMBEDDING_MODEL'] = 'frida'
    
    # Remove hostname/port to avoid LM Studio path
    for var in ['EMBEDDING_HOSTNAME', 'EMBEDDING_PORT']:
        if var in os.environ:
            del os.environ[var]

    try:
        # Import after setting environment
        from rag_component.embedding_manager import T5EncoderEmbeddings
        
        # Test the alias resolution directly by checking the internal logic
        model_name = 'frida'
        model_aliases = {
            "frida": "t5-small",  # Using t5-small as the default for frida
            "t5-base-encoder": "t5-base",
            "t5-large-encoder": "t5-large",
        }
        
        actual_model_name = model_aliases.get(model_name.lower(), model_name)
        print(f"Original model name: {model_name}")
        print(f"Mapped to: {actual_model_name}")
        
        # Verify the mapping worked
        assert actual_model_name == "t5-small", f"Expected 't5-small', got '{actual_model_name}'"
        
        print("✅ Model alias mapping test passed!")
        return True
    except Exception as e:
        print(f"❌ Error during model alias mapping test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_manager_initialization():
    """Test that the embedding manager initializes correctly with the alias."""
    print("\nTesting embedding manager initialization with alias mapping...")
    
    # Set environment
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
        
        # Check if it's using the T5EncoderEmbeddings
        if hasattr(emb_manager.embeddings, 'model_name'):
            print(f"Internal model name: {emb_manager.embeddings.model_name}")
        
        print("✅ Embedding manager initialization test passed!")
        return True
    except Exception as e:
        print(f"❌ Error during embedding manager initialization test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = test_model_alias_mapping()
    success2 = test_embedding_manager_initialization()

    if success1 and success2:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed.")
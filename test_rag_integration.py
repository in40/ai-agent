#!/usr/bin/env python3
"""
Debug script to test the embedding functionality in the context of the RAG system.
"""

import os

def test_rag_integration():
    """Test the embedding functionality in the context of RAG operations."""
    print("Testing RAG integration with the updated embedding system...")

    # Use the original configuration from .env
    try:
        from rag_component.embedding_manager import EmbeddingManager
        emb_manager = EmbeddingManager()

        print(f"Embedding manager provider: {emb_manager.provider}")
        print(f"Embedding manager model_name: {emb_manager.model_name}")
        print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")

        # Test embedding various types of text that might be used in RAG
        test_cases = [
            "Simple test query",
            "What is the capital of France?",
            "How does machine learning work?",
            "Explain quantum computing in simple terms.",
            "",  # Empty string test
            "A" * 1000,  # Long text test
        ]

        for i, test_text in enumerate(test_cases):
            print(f"\nTest case {i+1}: {test_text[:50]}{'...' if len(test_text) > 50 else ''}")
            try:
                if test_text.strip():  # Only test non-empty strings
                    embedding = emb_manager.embed_text(test_text)
                    print(f"  Success: Generated embedding of length {len(embedding)}")
                else:
                    print("  Skipping empty string test")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()

        # Test multiple embeddings
        print(f"\nTesting multiple embeddings...")
        test_texts = [
            "First document",
            "Second document", 
            "Third document"
        ]
        try:
            embeddings = emb_manager.embed_texts(test_texts)
            print(f"Success: Generated {len(embeddings)} embeddings")
            for i, emb in enumerate(embeddings):
                print(f"  Embedding {i+1}: length {len(emb)}")
        except Exception as e:
            print(f"Error in multiple embeddings: {e}")
            import traceback
            traceback.print_exc()

        return True

    except Exception as e:
        print(f"❌ Error during RAG integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store_compatibility():
    """Test if the embeddings are compatible with vector store operations."""
    print("\nTesting vector store compatibility...")
    
    try:
        from rag_component.embedding_manager import EmbeddingManager
        emb_manager = EmbeddingManager()
        
        # Test a typical query that might come from document lookup
        query = "Find information about machine learning algorithms"
        embedding = emb_manager.embed_text(query)
        
        print(f"Generated embedding for query: {len(embedding)} dimensions")
        
        # Check if embedding values are reasonable (not NaN or infinite)
        import math
        invalid_values = [val for val in embedding if math.isnan(val) or math.isinf(val)]
        if invalid_values:
            print(f"❌ Found {len(invalid_values)} invalid values in embedding")
            return False
        else:
            print("✅ All embedding values are valid")
            
        # Test if embedding values are in reasonable range
        min_val = min(embedding)
        max_val = max(embedding)
        print(f"Embedding value range: [{min_val:.4f}, {max_val:.4f}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during vector store compatibility test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success1 = test_rag_integration()
    success2 = test_vector_store_compatibility()

    if success1 and success2:
        print("\n✅ All tests passed! The embedding system appears to be working correctly.")
    else:
        print("\n❌ Some tests failed. There may be issues with the embedding system.")
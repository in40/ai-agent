#!/usr/bin/env python3
"""
Test script to check if the embedding model works correctly
"""
import os
import sys
sys.path.insert(0, '/root/qwen_test/ai_agent')

from rag_component.embedding_manager import EmbeddingManager

def test_embedding():
    print("Testing embedding manager...")
    
    # Create an embedding manager instance
    emb_manager = EmbeddingManager()
    
    print(f"Provider: {emb_manager.provider}")
    print(f"Model: {emb_manager.model_name}")
    
    # Test embedding a simple text
    test_text = "This is a test document for embedding."
    
    try:
        print(f"Attempting to embed text: '{test_text}'")
        embedding = emb_manager.embed_text(test_text)
        print(f"Embedding successful. Length: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")
    except Exception as e:
        print(f"Error during embedding: {e}")
        import traceback
        traceback.print_exc()
        
    # Test embedding multiple texts
    test_texts = ["First document", "Second document", ""]
    print(f"\nAttempting to embed multiple texts: {test_texts}")
    try:
        embeddings = emb_manager.embed_texts(test_texts)
        print(f"Multiple embedding successful. Number of embeddings: {len(embeddings)}")
        for i, emb in enumerate(embeddings):
            print(f"  Text {i}: length {len(emb)}, first 5 values: {emb[:5]}")
    except Exception as e:
        print(f"Error during multiple embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding()
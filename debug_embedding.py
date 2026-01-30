#!/usr/bin/env python3
"""
Debug script to understand what's happening with the embedding manager.
"""

import os

def debug_embedding_manager():
    """Debug the embedding manager to see what's happening."""
    print("Debugging embedding manager...")
    
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
    
    print(f"EMBEDDING_PROVIDER: {os.getenv('EMBEDDING_PROVIDER')}")
    print(f"EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL')}")
    print(f"EMBEDDING_HOSTNAME: {os.getenv('EMBEDDING_HOSTNAME')}")
    print(f"EMBEDDING_PORT: {os.getenv('EMBEDDING_PORT')}")
    
    # Import after setting environment variables
    from rag_component.config import RAG_EMBEDDING_PROVIDER, RAG_EMBEDDING_MODEL
    print(f"RAG_EMBEDDING_PROVIDER (after clearing): {RAG_EMBEDDING_PROVIDER}")
    print(f"RAG_EMBEDDING_MODEL (after clearing): {RAG_EMBEDDING_MODEL}")
    
    from config.settings import EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_HOSTNAME, EMBEDDING_PORT
    print(f"Global EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")
    print(f"Global EMBEDDING_MODEL: {EMBEDDING_MODEL}")
    print(f"Global EMBEDDING_HOSTNAME: {EMBEDDING_HOSTNAME}")
    print(f"Global EMBEDDING_PORT: {EMBEDDING_PORT}")
    
    # Create an embedding manager instance
    from rag_component.embedding_manager import EmbeddingManager
    emb_manager = EmbeddingManager()
    
    print(f"Embedding manager provider: {emb_manager.provider}")
    print(f"Embedding manager model_name: {emb_manager.model_name}")
    print(f"Embedding manager hostname: {emb_manager.hostname}")
    print(f"Embedding manager port: {emb_manager.port}")
    print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")

if __name__ == "__main__":
    debug_embedding_manager()
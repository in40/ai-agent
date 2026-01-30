#!/usr/bin/env python3
"""
Debug script to understand how the embedding manager determines the provider.
"""

import os

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

print("Environment variables:")
print(f"EMBEDDING_PROVIDER: {os.environ.get('EMBEDDING_PROVIDER')}")
print(f"EMBEDDING_MODEL: {os.environ.get('EMBEDDING_MODEL')}")
print(f"EMBEDDING_HOSTNAME: {os.environ.get('EMBEDDING_HOSTNAME')}")
print(f"EMBEDDING_PORT: {os.environ.get('EMBEDDING_PORT')}")

# Import the settings to see the defaults
from config.settings import EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_HOSTNAME, EMBEDDING_PORT
print("\nConfig settings (with defaults):")
print(f"EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")
print(f"EMBEDDING_MODEL: {EMBEDDING_MODEL}")
print(f"EMBEDDING_HOSTNAME: {EMBEDDING_HOSTNAME}")
print(f"EMBEDDING_PORT: {EMBEDDING_PORT}")

# Import the rag config
from rag_component.config import RAG_EMBEDDING_PROVIDER, RAG_EMBEDDING_MODEL
print(f"\nRAG config:")
print(f"RAG_EMBEDDING_PROVIDER: {RAG_EMBEDDING_PROVIDER}")
print(f"RAG_EMBEDDING_MODEL: {RAG_EMBEDDING_MODEL}")

# Now create the embedding manager
from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()

print(f"\nEmbedding manager:")
print(f"Provider: {emb_manager.provider}")
print(f"Model name: {emb_manager.model_name}")
print(f"Hostname: {emb_manager.hostname}")
print(f"Port: {emb_manager.port}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
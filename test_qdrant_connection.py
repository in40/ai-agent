#!/usr/bin/env python3
"""
Test script to replicate the exact Qdrant connection from the RAG component
"""

import os
from dotenv import dotenv_values

# Load environment variables like the RAG MCP Server does
env_vars = dotenv_values()
os.environ.update(env_vars)

# Get the Qdrant config directly from environment like the updated vector_store_manager does
qdrant_url = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("RAG_QDRANT_API_KEY", "")

print(f"Qdrant URL: {qdrant_url}")
print(f"Qdrant API Key set: {'Yes' if qdrant_api_key else 'No'}")
print(f"Qdrant API Key length: {len(qdrant_api_key) if qdrant_api_key else 0}")

if not qdrant_api_key:
    print("ERROR: Qdrant API key is not set!")
    exit(1)

from qdrant_client import QdrantClient

print("\nCreating Qdrant client with HTTP (prefer_grpc=False)...")
try:
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        prefer_grpc=False  # Use HTTP instead of gRPC
    )
    
    print("✓ Qdrant client created successfully")
    
    # Test the connection by getting collections
    print("Testing connection by getting collections...")
    collections = client.get_collections()
    print(f"✓ Successfully retrieved collections: {collections}")
    
    print("\n✓ Test PASSED: Qdrant connection working!")
    
except Exception as e:
    print(f"✗ Test FAILED: {e}")
    import traceback
    traceback.print_exc()
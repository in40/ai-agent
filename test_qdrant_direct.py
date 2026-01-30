#!/usr/bin/env python3
"""
Direct test of Qdrant connection with explicit API key
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Get the API key directly from environment
api_key = os.getenv("RAG_QDRANT_API_KEY")
url = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")

print(f"API Key from environment: {api_key}")
print(f"URL from environment: {url}")

if not api_key:
    print("ERROR: API key not found in environment")
    exit(1)

from qdrant_client import QdrantClient

print("\nTrying to connect with explicit parameters...")

try:
    # Create client with explicit parameters
    client = QdrantClient(
        url=url,
        api_key=api_key,
        prefer_grpc=False
    )
    
    print("✓ Successfully created Qdrant client")
    
    # Test connection by getting collections
    collections = client.get_collections()
    print(f"✓ Successfully retrieved collections: {collections}")
    
    print("\n✓ Connection test PASSED!")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
    import traceback
    traceback.print_exc()
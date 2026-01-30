#!/usr/bin/env python3
"""
Debug script to test Qdrant connection
"""

from qdrant_client import QdrantClient

def test_qdrant_connection():
    print("Testing Qdrant connection...")
    
    # Test with API key and HTTP
    try:
        client = QdrantClient(
            url="http://localhost:6333",
            api_key="7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d",
            prefer_grpc=False
        )
        
        print("Connected to Qdrant successfully!")
        
        # Try to list collections
        collections = client.get_collections()
        print(f"Collections: {collections}")
        
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qdrant_connection()
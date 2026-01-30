#!/usr/bin/env python3
"""
Debug script to test Qdrant connection with environment variables
"""

import os
from dotenv import load_dotenv
from rag_component.config import RAG_QDRANT_API_KEY, RAG_QDRANT_URL

def test_qdrant_connection():
    print("Testing Qdrant connection with environment variables...")
    
    # Load environment variables
    load_dotenv()
    
    print(f"RAG_QDRANT_URL: {RAG_QDRANT_URL}")
    print(f"RAG_QDRANT_API_KEY: {'Set' if RAG_QDRANT_API_KEY else 'Not set'}")
    
    if not RAG_QDRANT_API_KEY:
        print("ERROR: RAG_QDRANT_API_KEY is not set!")
        return
    
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(
            url=RAG_QDRANT_URL,
            api_key=RAG_QDRANT_API_KEY,
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
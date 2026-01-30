#!/usr/bin/env python3
"""
Script to reset the Qdrant collection to fix the dimension mismatch.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path so we can import from rag_component
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def reset_qdrant_collection():
    """Reset the Qdrant collection to fix the dimension mismatch."""
    try:
        from qdrant_client import QdrantClient
        from rag_component.config import RAG_COLLECTION_NAME, RAG_QDRANT_URL, RAG_QDRANT_API_KEY
        
        # Get Qdrant config
        qdrant_url = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("RAG_QDRANT_API_KEY", "")
        collection_name = os.getenv("RAG_COLLECTION_NAME", "documents")
        
        print(f"Connecting to Qdrant at {qdrant_url}")
        print(f"Using collection: {collection_name}")
        
        # Initialize Qdrant client
        if qdrant_api_key:
            client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                prefer_grpc=False  # Use HTTP instead of gRPC to avoid auth issues
            )
        else:
            client = QdrantClient(
                url=qdrant_url,
                prefer_grpc=False  # Use HTTP instead of gRPC to avoid auth issues
            )
        
        # Delete the existing collection
        try:
            client.delete_collection(collection_name=collection_name)
            print(f"✓ Deleted existing collection: {collection_name}")
        except Exception as e:
            print(f"Note: Collection {collection_name} didn't exist or couldn't be deleted: {str(e)}")
        
        # Create a new collection with the correct embedding size
        from rag_component.embedding_manager import EmbeddingManager
        from qdrant_client.http.models import Distance, VectorParams
        
        embedding_manager = EmbeddingManager()
        test_embedding = embedding_manager.embeddings.embed_query("test")
        embedding_size = len(test_embedding)
        
        print(f"Creating new collection with embedding size: {embedding_size}")
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE),
        )
        
        print(f"✓ Created new collection '{collection_name}' with correct embedding size: {embedding_size}")
        return True
        
    except Exception as e:
        print(f"Error resetting Qdrant collection: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Resetting Qdrant collection to fix dimension mismatch...")
    success = reset_qdrant_collection()
    
    if success:
        print("\n✓ Qdrant collection reset successful! The dimension mismatch issue should be fixed.")
    else:
        print("\n✗ Qdrant collection reset failed.")
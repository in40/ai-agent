#!/usr/bin/env python3
"""
Script to clear the vector database by removing all documents.
"""
import os
import shutil
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Also add the current directory to the Python path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def clear_vector_db():
    """Clear all documents from the vector database."""
    print("Starting vector database clearing process...")

    try:
        # Import required modules
        from rag_component.vector_store_manager import VectorStoreManager
        from rag_component.config import RAG_VECTOR_STORE_TYPE, RAG_CHROMA_PERSIST_DIR, RAG_COLLECTION_NAME

        print("Initializing vector store manager...")
        # Initialize the vector store manager
        vector_store_manager = VectorStoreManager()

        print("Clearing the vector database...")

        if vector_store_manager.store_type.lower() == "chroma":
            # For Chroma, we need to delete the persistent directory to clear all data
            persist_dir = RAG_CHROMA_PERSIST_DIR
            collection_name = RAG_COLLECTION_NAME

            print(f"Deleting persistent directory: {persist_dir}")

            # Delete the entire persist directory to clear all data
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir)
                print(f"Persistent directory deleted: {persist_dir}")
            else:
                print(f"Persistent directory does not exist: {persist_dir}")

            # Re-initialize the vector store to create a fresh one
            vector_store_manager = VectorStoreManager()
        else:
            # For other vector stores, use the existing method
            vector_store_manager.delete_collection()

        print("✓ Vector database cleared successfully!")
        print(f"Vector store type: {vector_store_manager.store_type}")
        print(f"Collection name: {vector_store_manager.collection_name}")
        print(f"Persistent directory: {vector_store_manager.persist_dir}")

        return True

    except Exception as e:
        print(f"✗ Error during vector database clearing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = clear_vector_db()
    sys.exit(0 if success else 1)
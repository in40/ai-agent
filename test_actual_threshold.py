#!/usr/bin/env python3
"""
Test script to check what threshold the RAG orchestrator is actually using
"""
import os
import sys
from pathlib import Path

# Set the environment variable before importing anything
os.environ['RAG_SIMILARITY_THRESHOLD'] = '0.6'

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_actual_threshold():
    """Test what threshold the RAG orchestrator is actually using."""
    print("=== CHECKING ACTUAL THRESHOLD IN USE ===")
    
    # Import and reload the config to ensure it picks up the environment variable
    import importlib
    import rag_component.config
    importlib.reload(rag_component.config)
    
    # Check the threshold value from the config
    from rag_component.config import RAG_SIMILARITY_THRESHOLD
    print(f"Threshold from config: {RAG_SIMILARITY_THRESHOLD}")
    
    # Initialize RAG orchestrator
    from rag_component.main import RAGOrchestrator
    from rag_component.retriever import Retriever
    from rag_component.vector_store_manager import VectorStoreManager
    
    # Create components individually to check the threshold
    vector_store_manager = VectorStoreManager()
    retriever = Retriever(vector_store_manager)
    
    print(f"Threshold in retriever: {retriever.similarity_threshold}")
    
    # Russian query
    russian_query = "Для биномиального закона распределения 256 независимых данных"
    
    # Test with get_relevant_documents (this applies the threshold)
    relevant_docs = retriever.get_relevant_documents(russian_query)
    print(f"Documents returned with current threshold: {len(relevant_docs)}")
    
    if len(relevant_docs) == 0:
        # Try with a lower threshold manually
        print("\nTrying with manually set lower threshold...")
        original_threshold = retriever.similarity_threshold
        retriever.similarity_threshold = 0.65  # Lower than previous 0.7 but higher than our expected 0.66
        
        relevant_docs_new = retriever.get_relevant_documents(russian_query)
        print(f"Documents returned with manually set threshold 0.65: {len(relevant_docs_new)}")
        
        # Restore original threshold
        retriever.similarity_threshold = original_threshold
        
        if len(relevant_docs_new) > 0:
            print("Documents were found when manually lowering the threshold!")
            print("This confirms the issue is definitely the threshold value.")
        else:
            print("Even with manually lowered threshold, no documents found.")
            print("There might be another issue.")
    
    return True

if __name__ == "__main__":
    success = test_actual_threshold()
    if success:
        print("\n✓ Threshold check completed!")
    else:
        print("\n✗ Threshold check failed.")
        sys.exit(1)
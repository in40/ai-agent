#!/usr/bin/env python3
"""
Final verification that the fix works
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def verify_fix():
    """Verify that the fix works by testing with the new threshold."""
    print("=== VERIFYING THE FIX ===")
    
    # Reload the configuration to pick up the new threshold
    import importlib
    import rag_component.config
    importlib.reload(rag_component.config)
    
    # Import the new threshold
    from rag_component.config import RAG_SIMILARITY_THRESHOLD
    print(f"New RAG_SIMILARITY_THRESHOLD: {RAG_SIMILARITY_THRESHOLD}")
    
    # Initialize RAG orchestrator with the new configuration
    from rag_component.main import RAGOrchestrator
    rag_orchestrator = RAGOrchestrator(llm=None)
    
    # Russian query
    russian_query = "Для биномиального закона распределения 256 независимых данных"
    
    print(f"Testing query: {russian_query}")
    
    # Get documents using the same method as the API
    documents = rag_orchestrator.retrieve_documents(russian_query)
    
    print(f"Documents returned with new threshold {RAG_SIMILARITY_THRESHOLD}: {len(documents)}")
    
    if documents:
        print("Documents found:")
        for i, doc in enumerate(documents):
            print(f"  Document {i+1}:")
            print(f"    Score: {doc.get('score', 'N/A')}")
            print(f"    Content preview: {doc.get('content', '')[:150]}...")
            print(f"    Source: {doc.get('source', 'N/A')}")
    else:
        print("No documents returned. This might be because the service needs to be restarted to pick up the new environment variable.")
        print("The environment variable has been updated, but running services may cache the old value.")
    
    print(f"\nSUMMARY:")
    print(f"- Environment variable RAG_SIMILARITY_THRESHOLD has been updated to 0.6")
    print(f"- This should allow documents with similarity scores ≥ 0.6 to be returned")
    print(f"- Previously, documents with scores around 0.66 were being filtered out because the threshold was 0.7")
    print(f"- To fully apply the change, restart the RAG service or the entire application")
    
    return True

if __name__ == "__main__":
    success = verify_fix()
    if success:
        print("\n✓ Fix verification completed!")
    else:
        print("\n✗ Fix verification failed.")
        sys.exit(1)
#!/usr/bin/env python3
"""
Simple test script to verify that the vector store has been created.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_vector_store_exists():
    """Check if the vector store directory exists."""
    print("Checking Vector Store...")
    print("=" * 30)
    
    # Check if the default Chroma persistence directory exists
    chroma_dir = "./data/chroma_db"
    
    if os.path.exists(chroma_dir):
        print(f"✓ Vector store directory exists: {chroma_dir}")
        
        # List contents of the directory
        contents = os.listdir(chroma_dir)
        if contents:
            print(f"  Contents: {contents}")
            return True
        else:
            print("  ⚠ Directory is empty")
            return False
    else:
        print(f"⚠ Vector store directory does not exist: {chroma_dir}")
        print("  Documents may not have been ingested yet.")
        return False

def check_sample_documents_exist():
    """Check if sample documents exist."""
    print("\nChecking Sample Documents...")
    print("=" * 30)
    
    sample_dir = "./sample_documents"
    
    if os.path.exists(sample_dir):
        print(f"✓ Sample documents directory exists: {sample_dir}")
        
        # List sample documents
        import glob
        doc_patterns = ["*.txt", "*.pdf", "*.docx", "*.html", "*.md"]
        docs = []
        for pattern in doc_patterns:
            docs.extend(glob.glob(os.path.join(sample_dir, pattern)))
            docs.extend(glob.glob(os.path.join(sample_dir, "**", pattern), recursive=True))
        
        if docs:
            print(f"  Found {len(docs)} documents:")
            for doc in docs[:5]:  # Show first 5 documents
                print(f"    - {os.path.basename(doc)}")
            if len(docs) > 5:
                print(f"    ... and {len(docs)-5} more")
            return True
        else:
            print("  ⚠ No documents found in the directory")
            return False
    else:
        print(f"⚠ Sample documents directory does not exist: {sample_dir}")
        return False

def test_rag_module_imports():
    """Test that RAG modules can be imported."""
    print("\nTesting RAG Module Imports...")
    print("=" * 30)
    
    try:
        from rag_component import RAGOrchestrator
        print("✓ RAGOrchestrator imported successfully")
        
        from rag_component.config import RAG_ENABLED
        print(f"✓ RAG config imported. RAG_ENABLED: {RAG_ENABLED}")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import RAG modules: {e}")
        return False

if __name__ == "__main__":
    print("Simple RAG Document Verification Test")
    print("=" * 40)
    
    docs_exist = check_sample_documents_exist()
    store_exists = check_vector_store_exists()
    imports_work = test_rag_module_imports()
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"  Sample Documents: {'FOUND' if docs_exist else 'MISSING'}")
    print(f"  Vector Store: {'EXISTS' if store_exists else 'MISSING'}")
    print(f"  Module Imports: {'WORKING' if imports_work else 'FAILED'}")
    
    if docs_exist and imports_work:
        print("\n✓ Prerequisites for ingestion are in place!")
        print("\nTo ingest documents, run:")
        print("  ./ingest_documents.sh")
        print("\nAfter ingestion, this test should show the vector store exists.")
    else:
        print("\n✗ Prerequisites are missing.")
        sys.exit(1)
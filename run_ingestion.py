#!/usr/bin/env python3
"""
Direct script to ingest documents into the RAG system.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Also add the current directory to the Python path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def ingest_documents(doc_dir="./sample_documents"):
    """Ingest documents from the specified directory."""
    print("Starting document ingestion process...")
    
    try:
        # Import required modules
        from rag_component import RAGOrchestrator
        from models.response_generator import ResponseGenerator
        
        # Initialize the response generator to get the LLM
        response_gen = ResponseGenerator()
        llm = response_gen.llm  # Access the LLM directly from the response generator
        
        print("Initializing RAG orchestrator...")
        # Initialize the RAG orchestrator
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        print(f"Ingesting documents from: {doc_dir}")
        # Ingest documents from the specified directory
        success = rag_orchestrator.ingest_documents_from_directory(doc_dir)
        
        if success:
            print("✓ Documents ingested successfully!")
            return True
        else:
            print("✗ Failed to ingest documents")
            return False
            
    except Exception as e:
        print(f"✗ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Ingest documents into RAG system')
    parser.add_argument('doc_dir', nargs='?', default='./sample_documents', 
                        help='Directory containing documents to ingest (default: ./sample_documents)')
    args = parser.parse_args()
    
    success = ingest_documents(args.doc_dir)
    sys.exit(0 if success else 1)
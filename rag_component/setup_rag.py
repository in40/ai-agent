#!/usr/bin/env python3
"""
Script to initialize the RAG component and ingest sample documents.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_rag():
    """Initialize the RAG orchestrator and ingest sample documents."""
    print("Setting up RAG component...")

    # Import required modules
    from rag_component import RAGOrchestrator
    from models.response_generator import ResponseGenerator

    # Initialize the response generator to get the LLM
    response_gen = ResponseGenerator()
    llm = response_gen.llm  # Access the LLM directly from the response generator

    print("Initializing RAG orchestrator...")
    # Initialize the RAG orchestrator
    rag_orchestrator = RAGOrchestrator(llm=llm)

    print("Ingesting sample documents...")
    # Ingest documents from the sample directory
    success = rag_orchestrator.ingest_documents_from_directory("./sample_documents/")

    if success:
        print("✓ Documents ingested successfully!")
        return rag_orchestrator
    else:
        print("✗ Failed to ingest documents")
        return None

def test_query(rag_orchestrator, question):
    """Test a sample query against the ingested documents."""
    print(f"\nTesting query: '{question}'")
    
    # Ask a question about the documents
    result = rag_orchestrator.query(question)
    
    print("Response:", result['response'])
    print("Retrieved documents:", len(result['context']))
    
    return result

if __name__ == "__main__":
    print("RAG Setup and Test Script")
    print("=" * 40)
    
    # Set up RAG with sample documents
    rag_orch = setup_rag()
    
    if rag_orch:
        print("\nRAG component is ready for testing!")
        
        # Test a few sample queries
        test_queries = [
            "What is the company mission?",
            "What products and services does the company offer?",
            "How can I contact the company?",
            "What is AI according to the document?"
        ]
        
        for query in test_queries:
            test_query(rag_orch, query)
            print("-" * 40)
        
        print("\nSetup and basic testing complete!")
    else:
        print("Failed to set up RAG component.")
        sys.exit(1)
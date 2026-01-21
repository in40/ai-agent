#!/usr/bin/env python3
"""
Example script demonstrating the RAG (Retrieval-Augmented Generation) functionality
of the AI agent.
"""
import os
import asyncio
from pathlib import Path

def demonstrate_rag_functionality():
    """
    Demonstrates how to use the RAG component with the AI agent.
    """
    print("RAG Component Demonstration")
    print("=" * 40)
    
    print("\n1. Setting up RAG configuration...")
    print("   - RAG_ENABLED=true")
    print("   - RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2")
    print("   - RAG_VECTOR_STORE_TYPE=chroma")
    print("   - RAG_TOP_K_RESULTS=5")
    
    print("\n2. Document Ingestion Process:")
    print("   - Documents are loaded using DocumentLoader")
    print("   - Different file types are supported (PDF, DOCX, TXT, HTML, MD)")
    print("   - Text is split into chunks for processing")
    print("   - Chunks are converted to embeddings and stored in vector database")
    
    print("\n3. Query Processing Flow:")
    print("   - User query enters the LangGraph workflow")
    print("   - check_rag_applicability_node determines if RAG is appropriate")
    print("   - If RAG is selected, retrieve_documents_node fetches relevant docs")
    print("   - augment_context_node combines docs with user query")
    print("   - generate_rag_response_node creates the final response")
    
    print("\n4. Integration with Existing Workflow:")
    print("   - RAG seamlessly integrates with existing SQL workflow")
    print("   - Automatic fallback to SQL if RAG isn't appropriate")
    print("   - Preserves all existing functionality")
    
    print("\n5. Example Usage:")
    print("""
    # Initialize the RAG orchestrator with an LLM
    from rag_component import RAGOrchestrator
    from models.response_generator import ResponseGenerator
    
    # Get the response generator's LLM instance
    response_gen = ResponseGenerator()
    llm = response_gen._get_llm_instance(
        provider=os.getenv("RESPONSE_LLM_PROVIDER", "LM Studio"),
        model=os.getenv("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
    )
    
    # Initialize RAG orchestrator
    rag_orchestrator = RAGOrchestrator(llm=llm)
    
    # Ingest documents
    success = rag_orchestrator.ingest_documents([
        "path/to/document1.pdf",
        "path/to/document2.txt"
    ])
    
    if success:
        # Process a query using RAG
        result = rag_orchestrator.query("What does the document say about X?")
        print(result['response'])
    """)
    
    print("\n6. Key Benefits:")
    print("   - Enhanced responses using external knowledge sources")
    print("   - Support for various document formats")
    print("   - Configurable relevance thresholds")
    print("   - Seamless integration with existing SQL capabilities")
    print("   - Automatic fallback mechanisms")

def show_configuration_example():
    """
    Shows example configuration for RAG functionality.
    """
    print("\n" + "=" * 40)
    print("RAG Configuration Example")
    print("=" * 40)
    
    config_example = """
# RAG Configuration
RAG_ENABLED=true
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_VECTOR_STORE_TYPE=chroma
RAG_TOP_K_RESULTS=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=100
RAG_CHROMA_PERSIST_DIR=./data/chroma_db
RAG_COLLECTION_NAME=documents
RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx,.html,.md
    """.strip()
    
    print(config_example)

def show_architecture_overview():
    """
    Shows the architecture overview of the RAG component.
    """
    print("\n" + "=" * 40)
    print("RAG Architecture Overview")
    print("=" * 40)
    
    architecture = """
    User Request
         |
         v
    check_rag_applicability_node  -----> Traditional SQL Path
         |                                (if RAG not appropriate)
         | Use RAG?                       |
         v                                v
    retrieve_documents_node        get_schema_node -> ...
         |
         v
    augment_context_node
         |
         v
    generate_rag_response_node
         |
         v
    Return Response to User
    """.strip()
    
    print(architecture)

if __name__ == "__main__":
    demonstrate_rag_functionality()
    show_configuration_example()
    show_architecture_overview()
    
    print("\n" + "=" * 40)
    print("RAG Component Implementation Complete!")
    print("See docs/rag_component.md for detailed documentation.")
    print("=" * 40)
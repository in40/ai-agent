#!/usr/bin/env python3
"""
Test script to verify RAG component functionality.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_rag_imports():
    """Test that RAG components can be imported correctly."""
    print("Testing RAG component imports...")
    
    try:
        from rag_component import RAGOrchestrator
        print("✓ Successfully imported RAGOrchestrator")
        
        from rag_component.config import RAG_ENABLED
        print(f"✓ Successfully imported RAG config. RAG_ENABLED: {RAG_ENABLED}")
        
        from rag_component.document_loader import DocumentLoader
        print("✓ Successfully imported DocumentLoader")
        
        from rag_component.embedding_manager import EmbeddingManager
        print("✓ Successfully imported EmbeddingManager")
        
        from rag_component.vector_store_manager import VectorStoreManager
        print("✓ Successfully imported VectorStoreManager")
        
        from rag_component.retriever import Retriever
        print("✓ Successfully imported Retriever")
        
        from rag_component.rag_chain import RAGChain
        print("✓ Successfully imported RAGChain")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import RAG components: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error importing RAG components: {e}")
        return False

def test_rag_initialization():
    """Test that RAG components can be initialized correctly."""
    print("\nTesting RAG component initialization...")
    
    try:
        from rag_component import RAGOrchestrator
        
        # Initialize the orchestrator (without an LLM for this test)
        rag_orchestrator = RAGOrchestrator()
        print("✓ Successfully initialized RAGOrchestrator")
        
        # Test that all components were initialized
        assert hasattr(rag_orchestrator, 'document_loader'), "Missing document_loader"
        assert hasattr(rag_orchestrator, 'embedding_manager'), "Missing embedding_manager"
        assert hasattr(rag_orchestrator, 'vector_store_manager'), "Missing vector_store_manager"
        assert hasattr(rag_orchestrator, 'retriever'), "Missing retriever"
        assert hasattr(rag_orchestrator, 'rag_chain'), "Missing rag_chain"
        assert hasattr(rag_orchestrator, 'text_splitter'), "Missing text_splitter"
        
        print("✓ All RAG components properly initialized in orchestrator")
        
        return True
    except Exception as e:
        print(f"✗ Failed to initialize RAG components: {e}")
        return False

def test_embedding_manager():
    """Test the embedding manager functionality."""
    print("\nTesting embedding manager...")

    try:
        from rag_component.embedding_manager import EmbeddingManager

        embedding_manager = EmbeddingManager()
        print("✓ Successfully initialized EmbeddingManager")

        # Test that the embeddings property exists
        assert hasattr(embedding_manager, 'embeddings'), "Missing embeddings property"

        print("✓ Embedding manager has required properties")

        return True
    except Exception as e:
        print(f"✗ Failed to test embedding manager: {e}")
        return False

def test_vector_store_manager():
    """Test the vector store manager functionality."""
    print("\nTesting vector store manager...")

    try:
        from rag_component.vector_store_manager import VectorStoreManager

        vector_store_manager = VectorStoreManager()
        print("✓ Successfully initialized VectorStoreManager")

        # Test that required methods exist
        assert hasattr(vector_store_manager, 'similarity_search'), "Missing similarity_search method"
        assert hasattr(vector_store_manager, 'add_documents'), "Missing add_documents method"

        print("✓ Vector store manager has required methods")

        return True
    except Exception as e:
        print(f"✗ Failed to test vector store manager: {e}")
        return False

def test_state_update():
    """Test that the AgentState has been updated with RAG fields."""
    print("\nTesting AgentState RAG fields...")
    
    try:
        from langgraph_agent.langgraph_agent import AgentState
        
        # Check that RAG-specific fields are in the AgentState
        expected_fields = [
            'rag_documents',
            'rag_context', 
            'use_rag_flag',
            'rag_relevance_score',
            'rag_query',
            'rag_response'
        ]
        
        for field in expected_fields:
            assert field in AgentState.__annotations__, f"Missing field: {field}"
        
        print(f"✓ All {len(expected_fields)} RAG fields found in AgentState")
        
        return True
    except Exception as e:
        print(f"✗ Failed to verify AgentState RAG fields: {e}")
        return False

def main():
    """Run all tests."""
    print("Running RAG component tests...\n")
    
    tests = [
        test_rag_imports,
        test_rag_initialization,
        test_embedding_manager,
        test_vector_store_manager,
        test_state_update
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\n{'='*50}")
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! RAG component is properly integrated.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
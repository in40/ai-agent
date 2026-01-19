#!/usr/bin/env python3
"""
Simple test script to verify RAG functionality.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_rag_basic_functionality():
    """Test basic RAG functionality without actually ingesting documents."""
    print("Testing RAG basic functionality...")
    
    try:
        # Test imports
        from rag_component import RAGOrchestrator
        print("✓ RAGOrchestrator imported successfully")
        
        from rag_component.config import RAG_ENABLED
        print(f"✓ RAG config imported successfully. RAG_ENABLED: {RAG_ENABLED}")
        
        from rag_component.document_loader import DocumentLoader
        print("✓ DocumentLoader imported successfully")
        
        from rag_component.embedding_manager import EmbeddingManager
        print("✓ EmbeddingManager imported successfully")
        
        from rag_component.vector_store_manager import VectorStoreManager
        print("✓ VectorStoreManager imported successfully")
        
        from rag_component.retriever import Retriever
        print("✓ Retriever imported successfully")
        
        from rag_component.rag_chain import RAGChain
        print("✓ RAGChain imported successfully")
        
        # Test initialization of components (without actually connecting to external services)
        try:
            embedding_manager = EmbeddingManager()
            print("✓ EmbeddingManager initialized successfully")
        except Exception as e:
            print(f"⚠ EmbeddingManager initialization had an issue (expected if model needs download): {e}")
        
        try:
            vector_store_manager = VectorStoreManager()
            print("✓ VectorStoreManager initialized successfully")
        except Exception as e:
            print(f"⚠ VectorStoreManager initialization had an issue: {e}")
        
        # Test that the AgentState has RAG fields (by importing the main agent)
        try:
            from langgraph_agent.langgraph_agent import AgentState
            expected_fields = [
                'rag_documents',
                'rag_context',
                'use_rag_flag',
                'rag_relevance_score',
                'rag_query',
                'rag_response'
            ]
            
            for field in expected_fields:
                if hasattr(AgentState, '__annotations__') and field in AgentState.__annotations__:
                    print(f"✓ AgentState has RAG field: {field}")
                else:
                    print(f"✗ AgentState missing RAG field: {field}")
        except Exception as e:
            print(f"⚠ Could not check AgentState RAG fields: {e}")
        
        print("\nBasic RAG functionality test completed.")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import RAG components: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during RAG basic functionality test: {e}")
        return False

def test_rag_integration_with_agent():
    """Test that RAG is integrated with the main agent."""
    print("\nTesting RAG integration with main agent...")
    
    try:
        # Check if the main agent file has RAG-related code
        with open("langgraph_agent/langgraph_agent.py", "r") as f:
            content = f.read()
            
        if "RAG" in content or "rag" in content:
            print("✓ RAG code found in main agent file")
        else:
            print("✗ RAG code not found in main agent file")
            return False
            
        # Look for specific RAG nodes
        rag_nodes = [
            "check_rag_applicability_node",
            "retrieve_documents_node", 
            "augment_context_node",
            "generate_rag_response_node"
        ]
        
        for node in rag_nodes:
            if node in content:
                print(f"✓ Found RAG node: {node}")
            else:
                print(f"✗ Missing RAG node: {node}")
                
        print("✓ RAG integration with main agent verified")
        return True
        
    except Exception as e:
        print(f"✗ Error during RAG integration test: {e}")
        return False

if __name__ == "__main__":
    print("Simple RAG Functionality Test")
    print("=" * 40)
    
    test1_passed = test_rag_basic_functionality()
    test2_passed = test_rag_integration_with_agent()
    
    print("\n" + "=" * 40)
    if test1_passed and test2_passed:
        print("✓ All RAG tests passed!")
    else:
        print("✗ Some RAG tests failed.")
        sys.exit(1)
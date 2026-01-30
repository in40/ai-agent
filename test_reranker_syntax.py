#!/usr/bin/env python3
"""
Simple test to verify that the reranker integration is syntactically correct.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing imports...")
    
    try:
        from rag_component import RAGOrchestrator, Reranker
        print("✓ Successfully imported RAGOrchestrator and Reranker from rag_component")
    except ImportError as e:
        print(f"✗ Failed to import from rag_component: {e}")
        return False
    
    try:
        from rag_component.main import RAGOrchestrator
        print("✓ Successfully imported RAGOrchestrator from rag_component.main")
    except ImportError as e:
        print(f"✗ Failed to import RAGOrchestrator from rag_component.main: {e}")
        return False
    
    try:
        from rag_component.reranker import Reranker
        print("✓ Successfully imported Reranker from rag_component.reranker")
    except ImportError as e:
        print(f"✗ Failed to import Reranker from rag_component.reranker: {e}")
        return False
    
    try:
        from rag_component.config import RERANKER_ENABLED, RERANKER_MODEL
        print(f"✓ Successfully imported config: RERANKER_ENABLED={RERANKER_ENABLED}, RERANKER_MODEL={RERANKER_MODEL}")
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    return True


def test_rag_orchestrator_has_reranker():
    """Test that the RAG orchestrator has the reranker attribute."""
    print("\nTesting RAG Orchestrator structure...")
    
    try:
        from rag_component.main import RAGOrchestrator
        from rag_component.config import RERANKER_ENABLED
        
        # Create a basic instance (without LLM to avoid complexity)
        orchestrator = RAGOrchestrator()
        
        # Check if the reranker attribute exists
        if hasattr(orchestrator, 'reranker'):
            print(f"✓ RAGOrchestrator has 'reranker' attribute: {orchestrator.reranker is not None}")
            print(f"  RERANKER_ENABLED in config: {RERANKER_ENABLED}")
        else:
            print("✗ RAGOrchestrator does not have 'reranker' attribute")
            return False
            
    except Exception as e:
        print(f"✗ Error testing RAG Orchestrator structure: {e}")
        return False
    
    return True


def test_reranker_class():
    """Test the Reranker class structure."""
    print("\nTesting Reranker class...")
    
    try:
        from rag_component.reranker import Reranker
        
        # Create an instance
        reranker = Reranker()
        
        # Check if required methods exist
        if hasattr(reranker, 'rerank_documents'):
            print("✓ Reranker has 'rerank_documents' method")
        else:
            print("✗ Reranker does not have 'rerank_documents' method")
            return False
            
        # Check attributes
        print(f"  Enabled: {reranker.enabled}")
        print(f"  Model: {reranker.model}")
        print(f"  Base URL: {reranker.base_url}")
        
    except Exception as e:
        print(f"✗ Error testing Reranker class: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("Running syntax and integration tests for reranker...\n")
    
    success = True
    success &= test_imports()
    success &= test_rag_orchestrator_has_reranker()
    success &= test_reranker_class()
    
    print(f"\n{'='*50}")
    if success:
        print("✓ All tests passed! Reranker integration is syntactically correct.")
        print("\nNote: Functional testing requires LM Studio with the reranker model running.")
    else:
        print("✗ Some tests failed!")
    
    return success


if __name__ == "__main__":
    main()
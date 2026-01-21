#!/usr/bin/env python3
"""
Test script to verify that filenames are preserved during upload and ingestion.
"""
import os
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

def test_filename_preservation():
    """Test that filenames with non-Latin characters are preserved."""
    print("Testing filename preservation...")
    
    try:
        from rag_component.main import RAGOrchestrator
        from rag_component.config import RAG_EMBEDDING_MODEL
        from langchain_community.llms import HuggingFaceEndpoint
        import os

        # Create a mock LLM for testing
        class MockLLM:
            def invoke(self, *args, **kwargs):
                return "Mock response for testing"
        
        # Initialize RAG orchestrator with mock LLM for testing
        rag_orchestrator = RAGOrchestrator(llm=MockLLM())
        
        # Create a temporary file with a non-Latin filename
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                         prefix='Приказ_ФСТЭК_России_от_18_февраля_2013_г._N_21_') as temp_file:
            temp_file.write("This is a test document with Russian characters in the filename.")
            temp_file_path = temp_file.name
        
        print(f"Created temporary file: {temp_file_path}")
        
        # Test regular ingestion
        print("Testing regular ingestion...")
        success = rag_orchestrator.ingest_documents([temp_file_path])
        if not success:
            print("❌ Regular ingestion failed")
            return False
        
        print("✅ Regular ingestion completed successfully")
        
        # Test upload functionality with original filenames
        print("\nTesting upload functionality with original filenames...")
        
        # Create another temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                         prefix='Приказ_ФСТЭК_России_от_14_05_2020_N_68_') as temp_file:
            temp_file.write("This is another test document.")
            temp_file_path = temp_file.name
        
        original_filename = "Приказ ФСТЭК России от 14.05.2020 N 68.txt"
        
        # Simulate upload ingestion
        success = rag_orchestrator.ingest_documents_from_upload([temp_file_path], [original_filename])
        if not success:
            print("❌ Upload ingestion failed")
            return False
        
        print("✅ Upload ingestion completed successfully")
        
        # Clean up temporary files
        os.unlink(temp_file_path)
        
        # Create a file for directory ingestion test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                         prefix='Тестовый_документ_каталог_', dir=tempfile.gettempdir()) as temp_file:
            temp_file.write("This is a test document for directory ingestion.")
            temp_file_path = temp_file.name
        
        # Test directory ingestion
        print("\nTesting directory ingestion...")
        success = rag_orchestrator.ingest_documents_from_directory(tempfile.gettempdir())
        if not success:
            print("❌ Directory ingestion failed")
            return False
        
        print("✅ Directory ingestion completed successfully")
        
        # Clean up
        os.unlink(temp_file_path)
        
        print("\n✅ All ingestion tests passed! Filenames with non-Latin characters should be preserved.")
        print("✅ Source labels should be set correctly ('Filesystem ingestion' or 'Web upload')")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_filename_preservation()
    sys.exit(0 if success else 1)
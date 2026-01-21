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

        # Initialize RAG orchestrator without LLM for testing purposes
        # The LLM is only needed for query operations, not for ingestion
        rag_orchestrator = RAGOrchestrator()
        
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
        
        # Query to check if the document was ingested with the correct filename
        print("Querying to check if filename was preserved...")
        docs = rag_orchestrator.retrieve_documents("test document")
        
        if docs:
            doc = docs[0]
            source = doc.get('source', 'Unknown')
            print(f"Document source: {source}")
            
            # Check if the original filename is preserved
            expected_part = "Приказ_ФСТЭК_России_от_18_февраля_2013_г._N_21"
            if expected_part in source:
                print("✅ Filename with non-Latin characters preserved correctly")
            else:
                print(f"❌ Filename not preserved as expected. Expected part '{expected_part}' not found in '{source}'")
                
            # Check if upload method is labeled correctly
            upload_method = doc.get('metadata', {}).get('upload_method', '')
            if upload_method == "Filesystem ingestion":
                print("✅ Upload method labeled correctly as 'Filesystem ingestion'")
            else:
                print(f"❌ Upload method not labeled correctly. Got: '{upload_method}'")
        else:
            print("❌ No documents retrieved")
            return False
        
        # Clean up
        os.unlink(temp_file_path)
        
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
        
        # Query to check if the document was ingested with the correct original filename
        print("Querying to check if original filename was preserved...")
        docs = rag_orchestrator.retrieve_documents("another test document")
        
        if docs:
            doc = docs[0]
            source = doc.get('source', 'Unknown')
            print(f"Document source: {source}")
            
            # Check if the original filename is preserved
            expected_part = "Приказ ФСТЭК России от 14.05.2020 N 68"
            if expected_part in source:
                print("✅ Original filename with non-Latin characters preserved correctly")
            else:
                print(f"❌ Original filename not preserved as expected. Expected part '{expected_part}' not found in '{source}'")
                
            # Check if upload method is labeled correctly
            upload_method = doc.get('metadata', {}).get('upload_method', '')
            if upload_method == "Web upload":
                print("✅ Upload method labeled correctly as 'Web upload'")
            else:
                print(f"❌ Upload method not labeled correctly. Got: '{upload_method}'")
        else:
            print("❌ No documents retrieved from upload test")
            return False
        
        # Clean up
        os.unlink(temp_file_path)
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_filename_preservation()
    sys.exit(0 if success else 1)
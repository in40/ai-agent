#!/usr/bin/env python3
"""
Debug script to test the RAG ingestion functionality directly.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path so we can import from rag_component
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_direct_ingestion():
    """Test the RAG ingestion functionality directly."""
    try:
        # Import the RAG orchestrator
        from rag_component.main import RAGOrchestrator
        from models.response_generator import ResponseGenerator
        
        # Initialize the RAG orchestrator
        response_gen = ResponseGenerator()
        llm = response_gen.llm
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        print("✓ RAG orchestrator initialized successfully")
        
        # Create a temporary markdown file to test ingestion
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write("# Test Document\n\nThis is a test markdown file.\n\n## Section 2\n\nMore content here.")
            temp_file_path = temp_file.name
        
        print(f"✓ Created temporary test file: {temp_file_path}")
        
        # Try to load the document using the document loader directly
        from rag_component.document_loader import DocumentLoader
        loader = DocumentLoader()
        
        docs = loader.load_document(temp_file_path)
        print(f"✓ Successfully loaded document with {len(docs)} pages")
        
        # Try to ingest the document
        success = rag_orchestrator.ingest_documents([temp_file_path])
        
        if success:
            print("✓ Document ingestion successful!")
            result = True
        else:
            print("✗ Document ingestion failed!")
            result = False
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        return result
        
    except Exception as e:
        print(f"Error during direct ingestion test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing direct RAG ingestion functionality...")
    success = test_direct_ingestion()
    
    if success:
        print("\n✓ Direct ingestion test passed! The issue appears to be fixed.")
    else:
        print("\n✗ Direct ingestion test failed. The issue may still exist.")
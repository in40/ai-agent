#!/usr/bin/env python3
"""
Verification script to check if the uploaded PDF files were properly indexed in the vector store
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def verify_vector_store_contents():
    """Verify that the uploaded files are in the vector store"""
    print("Verifying vector store contents...")
    
    try:
        from rag_component.main import RAGOrchestrator
        from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
        from models.response_generator import ResponseGenerator
        
        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        # Try to retrieve documents to see if they were indexed
        print("Checking if documents are available in the vector store...")
        
        # Try a simple query to see if we get results from the uploaded documents
        test_query = "Apple Developer Program"
        print(f"Performing test query: '{test_query}'")
        
        documents = rag_orchestrator.retrieve_documents(test_query, top_k=10)
        
        print(f"Found {len(documents)} documents related to the query")
        
        # Print information about the retrieved documents
        for i, doc in enumerate(documents):
            print(f"\nDocument {i+1}:")
            print(f"  Source: {doc.get('metadata', {}).get('source', 'Unknown')}")
            print(f"  Title: {doc.get('metadata', {}).get('title', 'Unknown')}")
            print(f"  Upload Method: {doc.get('metadata', {}).get('upload_method', 'Unknown')}")
            print(f"  Content Preview: {doc.get('page_content', '')[:200]}...")
        
        # Also check for documents from the other uploaded files
        print("\nChecking for documents from ГОСТ Р 71207-2024.pdf...")
        gost_query = "стандарт"  # Russian word for "standard"
        gost_docs = rag_orchestrator.retrieve_documents(gost_query, top_k=5)
        print(f"Found {len(gost_docs)} documents related to ГОСТ Р 71207-2024.pdf")
        
        print("\nVerification complete!")
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_file_storage():
    """Check the file storage system"""
    print("\nChecking file storage system...")
    
    # Check how many files are stored in the uploaded files directory
    uploaded_files_dir = Path("./data/rag_uploaded_files")
    if uploaded_files_dir.exists():
        # Count the number of files
        file_count = sum(1 for _ in uploaded_files_dir.rglob("*") if _.is_file())
        print(f"Total files in rag_uploaded_files: {file_count}")
        
        # List the files
        for file_path in uploaded_files_dir.rglob("*"):
            if file_path.is_file():
                print(f"  - {file_path.relative_to(uploaded_files_dir)}")
    else:
        print("rag_uploaded_files directory does not exist")
    
    # Check how many markdown files are in the converted markdown directory
    converted_md_dir = Path("./data/rag_converted_markdown")
    if converted_md_dir.exists():
        md_files = list(converted_md_dir.rglob("*.md"))
        print(f"Total markdown files in rag_converted_markdown: {len(md_files)}")
        
        for md_file in md_files:
            print(f"  - {md_file.relative_to(converted_md_dir)}")
    else:
        print("rag_converted_markdown directory does not exist")

def main():
    print("RAG File Upload Verification Script")
    print("="*50)
    
    # Check file storage
    check_file_storage()
    
    # Verify vector store contents
    verify_vector_store_contents()
    
    print("\nVerification completed!")

if __name__ == "__main__":
    main()
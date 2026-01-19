#!/usr/bin/env python3
"""
Test to verify that documents can be ingested and queried.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ingestion_and_query():
    """Test document ingestion and querying."""
    print("Testing document ingestion and querying...")
    
    try:
        # Import required modules
        from rag_component import RAGOrchestrator
        from models.response_generator import ResponseGenerator
        
        # Initialize the response generator to get the LLM
        response_gen = ResponseGenerator()
        llm = response_gen.llm  # Access the LLM directly from the response generator
        
        # Initialize the RAG orchestrator
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        # First, let's try to ingest our sample document
        print("Attempting to ingest sample documents...")
        success = rag_orchestrator.ingest_documents_from_directory("./sample_documents/")
        
        if success:
            print("✓ Documents ingested successfully!")
        else:
            print("⚠ Document ingestion may have failed, but let's continue with the test")
        
        # Now try to query the system
        print("\nTesting query functionality...")
        test_query = "What is the company mission mentioned in the documents?"
        
        try:
            result = rag_orchestrator.query(test_query)
            print(f"Query: {test_query}")
            print(f"Response: {result['response']}")
            print(f"Number of retrieved documents: {len(result['context'])}")
            
            if result['context']:
                print("\nRetrieved document snippets:")
                for i, doc in enumerate(result['context'][:2]):  # Show first 2 documents
                    print(f"  Document {i+1}:")
                    print(f"    Content preview: {doc['content'][:200]}...")
                    print(f"    Score: {doc['score']}")
                    
                return True
            else:
                print("\n⚠ No documents were retrieved for this query.")
                print("This could mean:")
                print("  - No documents match the query")
                print("  - Documents weren't properly ingested")
                print("  - The vector store is empty")
                return False
                
        except Exception as e:
            print(f"✗ Error during querying: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ingestion_and_query()
    if success:
        print("\n✓ Ingestion and query test completed successfully!")
        print("Documents are properly ingested and can be retrieved.")
    else:
        print("\n✗ Ingestion and/or query test failed.")
        sys.exit(1)
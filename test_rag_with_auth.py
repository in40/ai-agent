#!/usr/bin/env python3
"""
Debug script to test RAG lookup functionality with proper authentication context
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_rag_lookup_with_auth_context():
    """Test RAG lookup with proper authentication context."""
    print("Testing RAG lookup with authentication context...")
    
    try:
        # Import required modules
        from backend.services.rag.app import rag_lookup
        from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
        from models.response_generator import ResponseGenerator
        from backend.security import Permission
        
        # Simulate the authentication context
        class MockCurrentUser:
            def __init__(self):
                self.id = "debug_user"
        
        current_user_id = MockCurrentUser()
        
        # Russian query from the user
        russian_query = "Для биномиального закона распределения 256 независимых данных"
        
        # Prepare the request data
        data = {
            'query': russian_query
        }
        
        print(f"Testing query: {russian_query}")
        
        # Call the rag_lookup function directly with mocked request context
        import flask
        from flask import Flask, request, g
        
        # Create a minimal Flask app for testing
        app = Flask(__name__)
        
        with app.test_request_context(json=data):
            # Set up the authentication context
            g.current_user = current_user_id
            
            # Call the function
            result, status_code = rag_lookup(current_user_id)
            
            print(f"Response status code: {status_code}")
            
            if status_code == 200:
                documents = result.get_json().get('documents', [])
                print(f"Number of documents returned: {len(documents)}")
                
                if documents:
                    print("\nReturned documents:")
                    for i, doc in enumerate(documents):
                        print(f"\nDocument {i+1}:")
                        print(f"  Score: {doc.get('score', 'N/A')}")
                        print(f"  Content preview: {doc.get('content', '')[:200]}...")
                        print(f"  Source: {doc.get('source', 'N/A')}")
                        print(f"  Metadata: {doc.get('metadata', {})}")
                else:
                    print("\nNo documents returned by the API.")
                    
                    # Let's also test the underlying functionality directly
                    print("\nTesting underlying functionality directly...")
                    from rag_component.main import RAGOrchestrator
                    
                    # Initialize RAG orchestrator with appropriate LLM
                    response_generator = ResponseGenerator()
                    llm = response_generator._get_llm_instance(
                        provider=RESPONSE_LLM_PROVIDER,
                        model=RESPONSE_LLM_MODEL
                    )

                    rag_orchestrator = RAGOrchestrator(llm=llm)

                    # Retrieve documents using the same method as the API
                    documents = rag_orchestrator.retrieve_documents(russian_query)
                    
                    print(f"Direct call - Number of documents returned: {len(documents)}")
                    
                    if documents:
                        print("\nDirect call - Returned documents:")
                        for i, doc in enumerate(documents):
                            print(f"\nDocument {i+1}:")
                            print(f"  Score: {doc.get('score', 'N/A')}")
                            print(f"  Content preview: {doc.get('content', '')[:200]}...")
                            print(f"  Source: {doc.get('source', 'N/A')}")
                            print(f"  Metadata: {doc.get('metadata', {})}")
                    else:
                        print("\nDirect call - No documents returned.")
            else:
                print(f"Error response: {result.get_json()}")
                
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_lookup_with_auth_context()
    if success:
        print("\n✓ RAG lookup test with authentication context completed!")
    else:
        print("\n✗ RAG lookup test with authentication context failed.")
        sys.exit(1)
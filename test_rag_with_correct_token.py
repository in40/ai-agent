#!/usr/bin/env python3
"""
Debug script to test RAG lookup functionality with a valid JWT token using the correct secret
"""
import os
import sys
from pathlib import Path
import jwt
from datetime import datetime, timedelta
from backend.security import UserRole, Permission

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_rag_lookup_with_correct_token():
    """Test RAG lookup with a valid JWT token using the correct secret."""
    print("Testing RAG lookup with a valid JWT token using the correct secret...")
    
    # Use the correct JWT secret
    jwt_secret = 'jwt-secret-string-change-this-too'
    
    # Create user info with appropriate permissions
    user_info = {
        'user_id': 'debug_user',
        'role': UserRole.ADMIN,
        'permissions': [
            Permission.READ_RAG,
            Permission.WRITE_RAG,
            Permission.READ_AGENT,
            Permission.WRITE_AGENT,
            Permission.MANAGE_USERS,
            Permission.READ_SYSTEM,
            Permission.WRITE_SYSTEM
        ]
    }
    
    # Create the payload
    payload = {
        'user_id': user_info['user_id'],
        'role': user_info['role'].value,
        'permissions': [perm.value for perm in user_info['permissions']],
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }

    # Generate a valid token using the correct secret
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    print(f"Generated token with correct secret: {token}")
    
    # Verify the token to make sure it's valid
    try:
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        print(f"Token verification successful: {decoded}")
    except Exception as e:
        print(f"Token verification failed: {e}")
        return False
    
    # Now test the API with the token
    import requests
    import json
    
    # The RAG service is running on port 5003
    base_url = "http://localhost:5003"
    
    # Russian query from the user
    russian_query = "Для биномиального закона распределения 256 независимых данных"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    payload = {
        'query': russian_query
    }
    
    try:
        print(f"Making POST request to {base_url}/lookup")
        print(f"Query: {russian_query}")
        
        response = requests.post(f"{base_url}/lookup", headers=headers, data=json.dumps(payload))
        
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            print(f"\nNumber of documents returned: {len(documents)}")
            
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
                
                # Let's also check if the issue is the similarity threshold by testing the retrieve endpoint
                print("\nTesting /retrieve endpoint which might have different behavior...")
                retrieve_response = requests.post(f"{base_url}/retrieve", headers=headers, data=json.dumps(payload))
                
                print(f"Retrieve endpoint response status code: {retrieve_response.status_code}")
                print(f"Retrieve endpoint response body: {retrieve_response.text}")
                
                if retrieve_response.status_code == 200:
                    retrieve_result = retrieve_response.json()
                    retrieve_docs = retrieve_result.get('documents', [])
                    print(f"\nNumber of documents from /retrieve: {len(retrieve_docs)}")
                    
                    if retrieve_docs:
                        print("\nDocuments from /retrieve:")
                        for i, doc in enumerate(retrieve_docs):
                            print(f"\nDocument {i+1}:")
                            print(f"  Score: {doc.get('score', 'N/A')}")
                            print(f"  Content preview: {doc.get('content', '')[:200]}...")
                            print(f"  Source: {doc.get('source', 'N/A')}")
                            print(f"  Metadata: {doc.get('metadata', {})}")
        else:
            print(f"Lookup endpoint failed with status {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"Error during API test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_lookup_with_correct_token()
    if success:
        print("\n✓ RAG lookup test with correct token completed!")
    else:
        print("\n✗ RAG lookup test with correct token failed.")
        sys.exit(1)
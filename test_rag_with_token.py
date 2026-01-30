#!/usr/bin/env python3
"""
Debug script to test RAG lookup functionality with a valid JWT token
"""
import os
import sys
from pathlib import Path
import jwt
from datetime import datetime, timedelta
from backend.security import UserRole, Permission, SecurityManager

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_rag_lookup_with_valid_token():
    """Test RAG lookup with a valid JWT token."""
    print("Testing RAG lookup with a valid JWT token...")
    
    # Create a security manager instance
    security_manager = SecurityManager()
    
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
    
    # Generate a valid token
    token = security_manager.generate_token(user_info, expiration_hours=24)
    print(f"Generated token: {token}")
    
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
                
        return True
        
    except Exception as e:
        print(f"Error during API test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_lookup_with_valid_token()
    if success:
        print("\n✓ RAG lookup test with valid token completed!")
    else:
        print("\n✗ RAG lookup test with valid token failed.")
        sys.exit(1)
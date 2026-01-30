#!/usr/bin/env python3
"""
Test script to verify that the imported processed documents are searchable
"""
import requests
import json
import os

# Configuration - use the same token as used during import
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:5000')
# Use a valid JWT token obtained from login
TEST_AUTH_TOKEN = os.getenv('TEST_AUTH_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdHVzZXIiLCJyb2xlIjoidXNlciIsInBlcm1pc3Npb25zIjpbInJlYWQ6YWdlbnQiLCJ3cml0ZTphZ2VudCIsInJlYWQ6cmFnIiwid3JpdGU6cmFnIl0sImV4cCI6MTc2OTc5Mjk0MiwiaWF0IjoxNzY5NzA2NTQyfQ.qT2-K-BK2b4WSkm7TLMpScxCEzq2pcI4M09mzky7R6k')

def test_search_functionality():
    """Test that the imported documents are searchable via the RAG service"""
    
    # Query that should match content from the GOST document
    search_query = {
        "query": "стойкость к атакам подбора",
        "top_k": 5
    }
    
    # Prepare the request
    url = f"{GATEWAY_URL}/api/rag/retrieve"
    
    # Headers
    headers = {
        'Authorization': f'Bearer {TEST_AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    print("Sending search request...")
    response = requests.post(url, json=search_query, headers=headers)
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print(f"Number of documents retrieved: {len(results.get('documents', []))}")
        
        # Print details of the first few results
        for i, doc in enumerate(results.get('documents', [])[:3]):
            print(f"\nDocument {i+1}:")
            print(f"  Content preview: {doc.get('page_content', '')[:200]}...")
            print(f"  Source: {doc.get('metadata', {}).get('source', 'Unknown')}")
            print(f"  Chunk ID: {doc.get('metadata', {}).get('chunk_id', 'Unknown')}")
            print(f"  Title: {doc.get('metadata', {}).get('title', 'Unknown')}")
    else:
        print(f"Response body: {response.text}")
    
    return response.status_code == 200

def check_specific_document():
    """Check if a specific document from the import is present"""
    
    # Query for a specific term that should be in the imported document
    search_query = {
        "query": "GOST_R_52633.3-2011",  # Document identifier from the JSON
        "top_k": 5
    }
    
    # Prepare the request
    url = f"{GATEWAY_URL}/api/rag/retrieve"
    
    # Headers
    headers = {
        'Authorization': f'Bearer {TEST_AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    print("\nChecking for specific document...")
    response = requests.post(url, json=search_query, headers=headers)
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print(f"Number of documents retrieved: {len(results.get('documents', []))}")
        
        # Print details of all results
        for i, doc in enumerate(results.get('documents', [])):
            print(f"\nDocument {i+1}:")
            print(f"  Source: {doc.get('metadata', {}).get('source', 'Unknown')}")
            print(f"  Chunk ID: {doc.get('metadata', {}).get('chunk_id', 'Unknown')}")
            print(f"  Title: {doc.get('metadata', {}).get('title', 'Unknown')}")
            print(f"  Upload method: {doc.get('metadata', {}).get('upload_method', 'Unknown')}")
            print(f"  Content preview: {doc.get('page_content', '')[:150]}...")
    else:
        print(f"Response body: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing search functionality for imported processed documents...\n")
    
    success1 = test_search_functionality()
    success2 = check_specific_document()
    
    if success1 and success2:
        print("\n✅ Search functionality is working - imported documents are accessible!")
    else:
        print("\n❌ Search functionality may have issues")
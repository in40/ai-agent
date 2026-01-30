#!/usr/bin/env python3
"""
Debug script to test RAG lookup functionality with the MCP server
"""
import os
import sys
import json
import requests
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_rag_mcp_lookup():
    """Test RAG lookup with the MCP server."""
    print("Testing RAG lookup with the MCP server...")
    
    # The RAG MCP server is running on port 8091
    base_url = "http://localhost:8091"
    
    # Russian query from the user
    russian_query = "Для биномиального закона распределения 256 независимых данных"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "action": "query_documents",
        "parameters": {
            "query": russian_query,
            "top_k": 5
        }
    }
    
    try:
        print(f"Making POST request to {base_url}/")
        print(f"Query: {russian_query}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{base_url}/", headers=headers, data=json.dumps(payload))
        
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nMCP Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('status') == 'success':
                documents = result.get('results', [])
                print(f"\nNumber of documents returned: {len(documents)}")
                
                if documents:
                    print("\nReturned documents:")
                    for i, doc in enumerate(documents):
                        print(f"\nDocument {i+1}:")
                        print(f"  Score: {doc.get('score', 'N/A')}")
                        print(f"  Content preview: {doc.get('content', '')[:200]}...")
                        print(f"  Metadata: {doc.get('metadata', {})}")
                else:
                    print("\nNo documents returned by the MCP server.")
            else:
                print(f"\nMCP server returned error: {result.get('error')}")
        else:
            print(f"MCP endpoint failed with status {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"Error during MCP test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_mcp_lookup()
    if success:
        print("\n✓ RAG MCP lookup test completed!")
    else:
        print("\n✗ RAG MCP lookup test failed.")
        sys.exit(1)
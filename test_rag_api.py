#!/usr/bin/env python3
"""
Test script to simulate API call to RAG service with Russian query
"""
import sys
import requests
import json
import os

def test_rag_lookup_api():
    """Test the RAG lookup API endpoint with Russian query."""
    print("Testing RAG lookup API with Russian query...")

    # The RAG service is running on port 5003
    base_url = "http://localhost:5003"

    # Russian query from the user
    russian_query = "Для биномиального закона распределения 256 независимых данных"

    headers = {
        'Content-Type': 'application/json'
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
            else:
                print("\nNo documents returned by the API.")

        return True

    except Exception as e:
        print(f"Error during API test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_lookup_api()
    if success:
        print("\n✓ RAG lookup API test completed!")
    else:
        print("\n✗ RAG lookup API test failed.")
        sys.exit(1)
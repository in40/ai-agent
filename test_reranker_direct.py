#!/usr/bin/env python3
"""
Test script to make a direct call to the reranker model.
"""
import sys
import os
import requests
import json

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from rag_component.config import RERANKER_MODEL, RERANKER_HOSTNAME, RERANKER_PORT, RERANKER_API_PATH, RERANKER_ENABLED

def test_reranker_direct():
    """Test direct call to the reranker model."""
    print("Testing direct call to reranker model...")
    
    if not RERANKER_ENABLED:
        print("Reranker is not enabled. Please set RERANKER_ENABLED=true in your environment.")
        return False
    
    print(f"Model: {RERANKER_MODEL}")
    print(f"Hostname: {RERANKER_HOSTNAME}")
    print(f"Port: {RERANKER_PORT}")
    print(f"API Path: {RERANKER_API_PATH}")
    
    # Construct the base URL
    base_url = f"http://{RERANKER_HOSTNAME}:{RERANKER_PORT}{RERANKER_API_PATH}"
    print(f"Base URL: {base_url}")
    
    # Test query and documents
    query = "What is the capital of France?"
    documents = [
        "Paris is the capital and most populous city of France. It is located in the north-central part of the country.",
        "London is the capital city of England and the United Kingdom. It is located on the River Thames in south-east England.",
        "Berlin is the capital and largest city of Germany. It is located in northeastern Germany.",
        "The weather today is sunny with a high of 25 degrees Celsius.",
        "France is a country in Europe known for its art, cuisine, and culture."
    ]
    
    # Try different possible endpoints
    endpoints_to_try = [
        f"{base_url}/rerank",
        f"{base_url}/v1/rerank",
        f"{base_url}/rankings",
        f"{base_url}/v1/rankings"
    ]
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": RERANKER_MODEL,
        "query": query,
        "documents": documents,
        "top_k": len(documents)
    }
    
    print(f"\nTesting payload: {json.dumps(payload, indent=2)}")
    
    for endpoint in endpoints_to_try:
        print(f"\nTrying endpoint: {endpoint}")
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success! Response: {json.dumps(result, indent=2)}")
                
                # Print the ranking results
                if "results" in result:
                    print("\nRanking Results:")
                    for i, item in enumerate(result["results"]):
                        doc_idx = item.get("index", -1)
                        relevance_score = item.get("relevance_score", 0.0)
                        if doc_idx < len(documents):
                            print(f"  {i+1}. Score: {relevance_score:.4f}, Document: {documents[doc_idx][:60]}...")
                
                return True
            else:
                print(f"Error response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"Connection error - server may not be running or accessible at {endpoint}")
        except requests.exceptions.Timeout:
            print(f"Timeout error - request took too long at {endpoint}")
        except requests.exceptions.RequestException as e:
            print(f"Request error at {endpoint}: {str(e)}")
        except Exception as e:
            print(f"Unexpected error at {endpoint}: {str(e)}")
    
    print("\nCould not reach the reranker model at any of the tested endpoints.")
    print("Make sure LM Studio is running with the reranker model loaded.")
    return False


if __name__ == "__main__":
    success = test_reranker_direct()
    if success:
        print("\n✓ Direct reranker call test completed successfully!")
    else:
        print("\n✗ Direct reranker call test failed or was unsuccessful.")
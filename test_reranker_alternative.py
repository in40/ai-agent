#!/usr/bin/env python3
"""
Test script to make a direct call to the reranker model using different approaches.
"""
import sys
import os
import requests
import json

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from rag_component.config import RERANKER_MODEL, RERANKER_HOSTNAME, RERANKER_PORT, RERANKER_API_PATH, RERANKER_ENABLED

def test_reranker_alternative_approaches():
    """Test different approaches to calling the reranker model."""
    print("Testing different approaches to call the reranker model...")
    
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
    
    # Approach 1: Try the standard embeddings endpoint (might work for some reranker models)
    print("\nApproach 1: Trying embeddings endpoint with query-document pairs")
    
    # For reranking, we need to make multiple calls - one for query and one for each document
    headers = {"Content-Type": "application/json"}
    
    try:
        # Get embedding for the query
        query_payload = {
            "input": query,
            "model": RERANKER_MODEL
        }
        
        query_response = requests.post(f"{base_url}/embeddings", json=query_payload, headers=headers, timeout=30)
        print(f"Query embedding request status: {query_response.status_code}")
        
        if query_response.status_code == 200:
            print("Query embedding successful!")
            query_embedding = query_response.json()["data"][0]["embedding"]
            print(f"Query embedding length: {len(query_embedding) if query_embedding else 'N/A'}")
        else:
            print(f"Query embedding failed: {query_response.text}")
            
        # Get embedding for the first document as a test
        if len(documents) > 0:
            doc_payload = {
                "input": documents[0],
                "model": RERANKER_MODEL
            }
            
            doc_response = requests.post(f"{base_url}/embeddings", json=doc_payload, headers=headers, timeout=30)
            print(f"Document embedding request status: {doc_response.status_code}")
            
            if doc_response.status_code == 200:
                print("Document embedding successful!")
                doc_embedding = doc_response.json()["data"][0]["embedding"]
                print(f"Document embedding length: {len(doc_embedding) if doc_embedding else 'N/A'}")
            else:
                print(f"Document embedding failed: {doc_response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request error during embeddings test: {str(e)}")
    
    # Approach 2: Try the chat completions endpoint (some models might work this way)
    print("\nApproach 2: Trying chat completions endpoint")
    
    try:
        chat_payload = {
            "model": RERANKER_MODEL,
            "messages": [
                {"role": "user", "content": f"Please rank the following documents by relevance to the query '{query}': {documents}"}
            ]
        }
        
        chat_response = requests.post(f"{base_url}/chat/completions", json=chat_payload, headers=headers, timeout=30)
        print(f"Chat completions request status: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            print("Chat completions successful!")
            result = chat_response.json()
            print(f"Response: {result['choices'][0]['message']['content'][:200]}...")
        else:
            print(f"Chat completions failed: {chat_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request error during chat completions test: {str(e)}")
    
    # Approach 3: Try the completions endpoint
    print("\nApproach 3: Trying completions endpoint")
    
    try:
        completion_payload = {
            "model": RERANKER_MODEL,
            "prompt": f"Rank these documents by relevance to the query '{query}': {documents}"
        }
        
        completion_response = requests.post(f"{base_url}/completions", json=completion_payload, headers=headers, timeout=30)
        print(f"Completions request status: {completion_response.status_code}")
        
        if completion_response.status_code == 200:
            print("Completions successful!")
            result = completion_response.json()
            if 'choices' in result and len(result['choices']) > 0:
                print(f"Response: {result['choices'][0]['text'][:200]}...")
        else:
            print(f"Completions failed: {completion_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request error during completions test: {str(e)}")
    
    # Approach 4: Try the specific rerank endpoint with different payload format
    print("\nApproach 4: Trying rerank endpoint with different payload format")
    
    try:
        # Some reranker implementations expect a different format
        rerank_payload = {
            "model": RERANKER_MODEL,
            "input": {
                "query": query,
                "texts": documents
            },
            "top_k": len(documents)
        }
        
        rerank_response = requests.post(f"{base_url}/rerank", json=rerank_payload, headers=headers, timeout=30)
        print(f"Rerank request status: {rerank_response.status_code}")
        
        if rerank_response.status_code == 200:
            print("Rerank successful!")
            result = rerank_response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Rerank failed: {rerank_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request error during rerank test: {str(e)}")
    
    return True


if __name__ == "__main__":
    success = test_reranker_alternative_approaches()
    if success:
        print("\n✓ Alternative approaches test completed!")
    else:
        print("\n✗ Alternative approaches test failed.")
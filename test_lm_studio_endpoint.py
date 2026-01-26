#!/usr/bin/env python3
"""
Test script to directly test the LM Studio embedding endpoint
"""
import requests
import json

def test_lm_studio_embedding():
    url = "http://asus-tus:1234/v1/embeddings"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Test payload for embedding
    payload = {
        "input": "This is a test document for embedding.",
        "model": "text-embedding-bge-m3"
    }
    
    print(f"Testing LM Studio embedding endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: LM Studio embedding endpoint is working correctly!")
        else:
            print("ERROR: LM Studio embedding endpoint returned an error.")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to LM Studio. Please check if LM Studio is running at http://asus-tus:1234")
    except Exception as e:
        print(f"ERROR: An exception occurred: {e}")

if __name__ == "__main__":
    test_lm_studio_embedding()
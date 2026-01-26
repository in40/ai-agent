#!/usr/bin/env python3
"""
Custom embedding wrapper for LM Studio that bypasses LangChain's OpenAIEmbeddings
"""
import os
import sys
sys.path.insert(0, '/root/qwen_test/ai_agent')

import requests
from typing import List
from langchain_core.embeddings import Embeddings


class LMStudioEmbeddings(Embeddings):
    """Custom embedding class for LM Studio."""
    
    def __init__(self, model: str, base_url: str, api_key: str = "dummy"):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        
        # Validate connection to LM Studio
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code != 200:
                print(f"Warning: Could not validate LM Studio connection. Status: {response.status_code}")
        except Exception as e:
            print(f"Warning: Could not connect to LM Studio at {self.base_url}. Error: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        # Filter out empty strings
        filtered_texts = [text for text in texts if text and text.strip()]
        
        if not filtered_texts:
            return []
        
        # Prepare the request
        payload = {
            "input": filtered_texts,
            "model": self.model
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the request to LM Studio
        response = requests.post(f"{self.base_url}/embeddings", json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"LM Studio embedding request failed with status {response.status_code}: {response.text}")
        
        result = response.json()
        
        # Extract embeddings from response
        embeddings = []
        for item in result.get("data", []):
            embeddings.append(item.get("embedding", []))
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        if not text or not text.strip():
            # Return a zero vector of appropriate dimension if text is empty
            return [0.0] * 10  # Adjust as needed
        
        # Prepare the request
        payload = {
            "input": [text],
            "model": self.model
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the request to LM Studio
        response = requests.post(f"{self.base_url}/embeddings", json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"LM Studio embedding request failed with status {response.status_code}: {response.text}")
        
        result = response.json()
        
        # Extract the first embedding from response
        if result.get("data") and len(result["data"]) > 0:
            return result["data"][0].get("embedding", [])
        else:
            raise Exception("No embeddings returned from LM Studio")


def test_custom_embeddings():
    print("Testing custom LM Studio embeddings...")
    
    # Create the custom embedding instance
    base_url = "http://asus-tus:1234/v1"
    model = "text-embedding-bge-m3"
    embeddings = LMStudioEmbeddings(model=model, base_url=base_url)
    
    # Test single embedding
    test_text = "This is a test document for embedding."
    print(f"Attempting to embed text: '{test_text}'")
    
    try:
        embedding = embeddings.embed_query(test_text)
        print(f"Single embedding successful. Length: {len(embedding)}")
        print(f"First 10 values: {embedding[:10]}")
    except Exception as e:
        print(f"Error during single embedding: {e}")
        import traceback
        traceback.print_exc()
    
    # Test multiple embeddings
    test_texts = ["First document", "Second document"]
    print(f"\nAttempting to embed multiple texts: {test_texts}")
    
    try:
        embeddings_list = embeddings.embed_documents(test_texts)
        print(f"Multiple embedding successful. Number of embeddings: {len(embeddings_list)}")
        for i, emb in enumerate(embeddings_list):
            print(f"  Text {i}: length {len(emb)}, first 5 values: {emb[:5]}")
    except Exception as e:
        print(f"Error during multiple embeddings: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_custom_embeddings()
#!/usr/bin/env python3
"""
Script to generate actual embeddings for all chunks and load into Qdrant.
Uses the reranker service at localhost:1234/v1/embeddings
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration
CHUNKS_DIR = "/root/qwen/ai_agent/rechunked_chunks"
QDRANT_URL = "http://localhost:6333"
QDRANT_KEY = "7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d"
COLLECTION_NAME = "documents"

# Embedding service
EMBEDDING_URL = "http://localhost:1234/v1/embeddings"
EMBEDDING_MODEL = "text-embedding-bge-reranker-v2-m3"

def get_embedding(text: str) -> list:
    """Get embedding for a single text using the reranker service."""
    try:
        payload = {
            "input": text,
            "model": EMBEDDING_MODEL
        }
        
        response = requests.post(EMBEDDING_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"    ⚠️ Embedding error: {response.status_code} - {response.text[:100]}")
            return None
        
        data = response.json()
        if "data" not in data or len(data["data"]) == 0:
            print(f"    ⚠️ No embedding data returned")
            return None
        
        return data["data"][0]["embedding"]
        
    except Exception as e:
        print(f"    ⚠️ Exception: {e}")
        return None

def clear_qdrant_collection():
    """Clear all points from the collection."""
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
    
    # Get all point IDs
    scroll_result = client.scroll(collection_name=COLLECTION_NAME, limit=10000, with_payload=False)
    point_ids = [point.id for point in scroll_result[0]]
    
    if point_ids:
        print(f"Deleting {len(point_ids)} existing points...")
        client.delete(collection_name=COLLECTION_NAME, points_selector=models.PointIdsList(points=point_ids))
        print(f"Deleted {len(point_ids)} points")
    else:
        print("Collection is empty")

def process_chunks_with_embeddings():
    """Process all chunk files, generate embeddings, and load to Qdrant."""
    print("=" * 60)
    print("GENERATING EMBEDDINGS AND LOADING TO QDRANT")
    print("=" * 60)
    
    # Clear existing data
    print("\n1. Clearing existing Qdrant data...")
    clear_qdrant_collection()
    
    # Get all chunk files
    print("\n2. Loading chunk files...")
    chunk_files = list(Path(CHUNKS_DIR).glob("*.chunks.json"))
    print(f"   Found {len(chunk_files)} chunk files")
    
    # Process each document
    print("\n3. Generating embeddings and uploading to Qdrant...")
    
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
    
    total_chunks = 0
    successful_chunks = 0
    failed_chunks = 0
    
    for i, chunk_file in enumerate(chunk_files, 1):
        doc_name = chunk_file.stem
        
        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        total_chunks += len(chunks)
        
        print(f"\n[{i}/{len(chunk_files)}] {doc_name} ({len(chunks)} chunks)")
        
        # Process chunks in batches of 10
        batch_size = 10
        for batch_start in range(0, len(chunks), batch_size):
            batch_end = min(batch_start + batch_size, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]
            
            print(f"   Processing chunks {batch_start}-{batch_end-1}...")
            
            # Generate embeddings for batch
            points = []
            for j, chunk_text in enumerate(batch_chunks):
                chunk_idx = batch_start + j
                
                # Get embedding
                embedding = get_embedding(chunk_text)
                
                if embedding is None:
                    failed_chunks += 1
                    print(f"      Chunk {chunk_idx}: FAILED")
                    continue
                
                successful_chunks += 1
                
                # Create point
                point_id = hashlib.md5(f"{doc_name}_{chunk_idx}".encode()).hexdigest()
                
                points.append(models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk_text,
                        "metadata": {
                            "source": doc_name,
                            "chunk_index": chunk_idx,
                            "total_chunks": len(chunks)
                        }
                    }
                ))
            
            # Upload batch to Qdrant
            if points:
                try:
                    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
                    print(f"      Uploaded {len(points)} chunks")
                except Exception as e:
                    print(f"      Upload error: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"Total chunks processed: {total_chunks}")
    print(f"Successful embeddings: {successful_chunks}")
    print(f"Failed embeddings: {failed_chunks}")
    
    # Get final count
    info = client.get_collection(COLLECTION_NAME)
    print(f"Final point count in Qdrant: {info.points_count}")

if __name__ == "__main__":
    process_chunks_with_embeddings()

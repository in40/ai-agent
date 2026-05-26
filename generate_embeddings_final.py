#!/usr/bin/env python3
"""
Script to generate actual embeddings for all chunks and load into Qdrant.
Uses the embedding service from .env configuration.
"""

import os
import json
import requests
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration from .env
EMBEDDING_URL = "http://asus-tus:1234/v1/embeddings"
EMBEDDING_MODEL = "bge-m3"

QDRANT_URL = "http://localhost:6333"
QDRANT_KEY = "7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d"
COLLECTION_NAME = "documents"

CHUNKS_DIR = "/root/qwen/ai_agent/rechunked_chunks"

def get_embedding(text: str) -> list:
    """Get embedding for a single text using the bge-m3 service."""
    try:
        payload = {
            "input": text,
            "model": EMBEDDING_MODEL
        }
        
        response = requests.post(EMBEDDING_URL, json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"    ⚠️ Embedding error: {response.status_code}")
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
    
    # Get all point IDs in batches
    all_point_ids = []
    offset = None
    while True:
        scroll_result = client.scroll(
            collection_name=COLLECTION_NAME, 
            limit=1000, 
            with_payload=False,
            offset=offset
        )
        if not scroll_result[0]:
            break
        all_point_ids.extend([point.id for point in scroll_result[0]])
        offset = scroll_result[1]
    
    if all_point_ids:
        print(f"Deleting {len(all_point_ids)} existing points...")
        client.delete(
            collection_name=COLLECTION_NAME, 
            points_selector=models.PointIdsList(points=all_point_ids)
        )
        print(f"✓ Deleted {len(all_point_ids)} points")
    else:
        print("✓ Collection is empty")

def process_chunks_with_embeddings():
    """Process all chunk files, generate embeddings, and load to Qdrant."""
    print("=" * 70)
    print("GENERATING EMBEDDINGS (bge-m3) AND LOADING TO QDRANT")
    print("=" * 70)
    print(f"Embedding service: {EMBEDDING_URL}")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Qdrant: {QDRANT_URL}/{COLLECTION_NAME}")
    
    # Clear existing data
    print("\n[1/4] Clearing existing Qdrant data...")
    clear_qdrant_collection()
    
    # Get all chunk files
    print("\n[2/4] Loading chunk files...")
    chunk_files = sorted(list(Path(CHUNKS_DIR).glob("*.chunks.json")))
    print(f"✓ Found {len(chunk_files)} chunk files")
    
    # Process each document
    print("\n[3/4] Generating embeddings and uploading to Qdrant...")
    
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
    
    total_chunks = 0
    successful_chunks = 0
    failed_chunks = 0
    batch_count = 0
    
    for i, chunk_file in enumerate(chunk_files, 1):
        doc_name = chunk_file.stem
        
        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        total_chunks += len(chunks)
        
        # Progress indicator every 10 documents
        if i % 10 == 0 or i == len(chunk_files):
            print(f"\n[{i}/{len(chunk_files)}] Processed {i} documents")
            print(f"  Chunks so far: {successful_chunks} successful, {failed_chunks} failed")
        
        # Process chunks in batches of 5 to avoid overwhelming the API
        batch_size = 5
        for batch_start in range(0, len(chunks), batch_size):
            batch_end = min(batch_start + batch_size, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]
            
            # Generate embeddings for batch
            points = []
            for j, chunk_text in enumerate(batch_chunks):
                chunk_idx = batch_start + j
                
                # Get embedding
                embedding = get_embedding(chunk_text)
                
                if embedding is None:
                    failed_chunks += 1
                    continue
                
                successful_chunks += 1
                
                # Create point
                point_id = hashlib.md5(f"{doc_name}_{chunk_idx}".encode()).hexdigest()
                
                points.append(models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk_text[:2000],  # Store truncated text in payload
                        "metadata": {
                            "source": doc_name,
                            "chunk_index": chunk_idx,
                            "total_chunks": len(chunks),
                            "full_text": chunk_text  # Store full text
                        }
                    }
                ))
            
            # Upload batch to Qdrant
            if points:
                try:
                    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
                    batch_count += 1
                    
                    # Progress every 50 batches
                    if batch_count % 50 == 0:
                        print(f"    Uploaded {batch_count} batches ({successful_chunks} chunks)")
                except Exception as e:
                    print(f"      Upload error: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Total chunks processed: {total_chunks}")
    print(f"Successful embeddings:  {successful_chunks}")
    print(f"Failed embeddings:      {failed_chunks}")
    print(f"Success rate:           {successful_chunks/total_chunks*100:.1f}%")
    
    # Get final count
    info = client.get_collection(COLLECTION_NAME)
    print(f"\nFinal point count in Qdrant: {info.points_count}")
    
    # Test a search query
    print("\n[4/4] Testing search...")
    test_query = "что такое защита информации"
    query_embedding = get_embedding(test_query)
    
    if query_embedding:
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=5
        )
        
        print(f"\nTest query: '{test_query}'")
        print("Top 5 results:")
        for i, hit in enumerate(search_result, 1):
            source = hit.payload.get('metadata', {}).get('source', 'Unknown')
            score = hit.score
            text_preview = hit.payload.get('metadata', {}).get('full_text', '')[:100]
            print(f"  {i}. [{source}] score: {score:.4f}")
            print(f"     {text_preview}...")

if __name__ == "__main__":
    process_chunks_with_embeddings()

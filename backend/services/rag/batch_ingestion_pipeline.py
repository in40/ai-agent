#!/usr/bin/env python3
"""
Batch Document Ingestion Pipeline
==================================

Integrates recursive chunking with embedding generation and Qdrant loading.
Uses configuration from .env file.

Usage:
    python3 batch_ingestion_pipeline.py [--source-dir DIR] [--mode MODE]

Modes:
    - full: Chunk + Embed + Load to Qdrant
    - chunk-only: Just create chunk files
    - embed-only: Generate embeddings for existing chunks
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.rag.recursive_chunking import RecursiveChunker

# Configuration from .env
EMBEDDING_URL = f"http://{os.getenv('EMBEDDING_HOSTNAME', 'asus-tus')}:{os.getenv('EMBEDDING_PORT', '1234')}{os.getenv('EMBEDDING_API_PATH', '/v1')}/embeddings"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")

QDRANT_URL = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")
QDRANT_KEY = os.getenv("RAG_QDRANT_API_KEY", "7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d")
COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "documents")

CHUNKS_OUTPUT_DIR = "/root/qwen/ai_agent/rechunked_chunks"


def load_existing_sources_qdrant() -> set:
    """Load list of already processed document sources from Qdrant."""
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
        scroll = client.scroll(collection_name=COLLECTION_NAME, limit=5000, with_payload=True)
        
        sources = set()
        for p in scroll[0]:
            src = p.payload.get('metadata', {}).get('source', '')
            if src:
                sources.add(src.split('.')[0])
        
        return sources
    except Exception as e:
        print(f"Warning: Could not check Qdrant: {e}")
        return set()


def chunk_documents(
    source_dir: str,
    output_dir: str = CHUNKS_OUTPUT_DIR,
    force: bool = False
) -> List[Dict[str, Any]]:
    """
    Chunk all documents in source directory.
    
    Args:
        source_dir: Directory containing .txt or .md files
        output_dir: Directory to save chunk JSON files
        force: Force re-chunking even if file exists
        
    Returns:
        List of chunking results
    """
    print(f"\n[CHUNKING] Processing documents from: {source_dir}")
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all document files
    doc_files = list(Path(source_dir).glob("*.txt")) + list(Path(source_dir).glob("*.md"))
    print(f"Found {len(doc_files)} document files")
    
    chunker = RecursiveChunker(
        target_chunk_size=2000,
        overlap_chars=200,
        min_chunk_size=500,
        max_chunk_size=8000
    )
    
    results = []
    
    for i, doc_file in enumerate(doc_files, 1):
        doc_name = doc_file.stem
        output_file = Path(output_dir) / f"{doc_name}.chunks.json"
        
        # Skip if already exists and not forcing
        if output_file.exists() and not force:
            print(f"  [{i}/{len(doc_files)}] Skipping {doc_name} (already chunked)")
            
            # Load existing result
            with open(output_file, 'r', encoding='utf-8') as f:
                results.append(json.load(f))
            continue
        
        print(f"  [{i}/{len(doc_files)}] Chunking: {doc_name}")
        
        try:
            result = chunker.chunk_document_file(str(doc_file), str(output_file))
            results.append(result)
            print(f"    → {result['total_chunks']} chunks")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    return results


def generate_embeddings_and_load(
    chunks_dir: str = CHUNKS_OUTPUT_DIR,
    batch_size: int = 10,
    skip_existing: bool = True
) -> Dict[str, int]:
    """
    Generate embeddings for all chunks and load to Qdrant.
    
    Args:
        chunks_dir: Directory containing chunk JSON files
        batch_size: Number of chunks to embed in each API call
        skip_existing: Skip documents already in Qdrant
        
    Returns:
        Statistics dictionary
    """
    print(f"\n[EMBEDDING] Generating bge-m3 embeddings and loading to Qdrant")
    print(f"  Embedding service: {EMBEDDING_URL}")
    print(f"  Model: {EMBEDDING_MODEL}")
    
    import requests
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)
    
    # Get existing sources if skipping
    existing_sources = set()
    if skip_existing:
        existing_sources = load_existing_sources_qdrant()
        print(f"  Existing documents in Qdrant: {len(existing_sources)}")
    
    # Find all chunk files
    chunk_files = sorted(list(Path(chunks_dir).glob("*.chunks.json")))
    print(f"  Chunk files to process: {len(chunk_files)}")
    
    stats = {
        "documents_processed": 0,
        "chunks_embedded": 0,
        "chunks_failed": 0,
        "qdrant_points": 0
    }
    
    for i, chunk_file in enumerate(chunk_files, 1):
        doc_name = chunk_file.stem.replace('.chunks', '')
        
        # Skip if already processed
        if skip_existing and doc_name in existing_sources:
            continue
        
        with open(chunk_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        
        # Process in batches
        for batch_start in range(0, len(chunks), batch_size):
            batch_chunks = chunks[batch_start:min(batch_start + batch_size, len(chunks))]
            
            texts = [c.get('content', '')[:2000] for c in batch_chunks]
            payload = {"input": texts, "model": EMBEDDING_MODEL}
            
            try:
                response = requests.post(EMBEDDING_URL, json=payload, timeout=180)
                
                if response.status_code == 200:
                    embeddings_data = response.json()["data"]
                    
                    points = []
                    for j, emb_data in enumerate(embeddings_data):
                        embedding = emb_data["embedding"]
                        chunk_idx = batch_start + j
                        point_id = hashlib.md5(f"{doc_name}_{chunk_idx}".encode()).hexdigest()
                        
                        points.append(models.PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                "metadata": {
                                    "source": doc_name,
                                    "chunk_index": chunk_idx,
                                    "full_text": chunks[chunk_idx].get('content', '')
                                }
                            }
                        ))
                    
                    if points:
                        client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
                        stats["chunks_embedded"] += len(points)
                
            except Exception as e:
                print(f"    ✗ Error embedding {doc_name}: {e}")
                stats["chunks_failed"] += len(batch_chunks)
        
        stats["documents_processed"] += 1
        
        if stats["documents_processed"] % 20 == 0:
            print(f"  Processed {stats['documents_processed']} documents, {stats['chunks_embedded']} chunks")
    
    # Final stats
    info = client.get_collection(COLLECTION_NAME)
    stats["qdrant_points"] = info.points_count
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Batch Document Ingestion Pipeline")
    parser.add_argument("--source-dir", default="/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents",
                       help="Source directory with .txt/.md files")
    parser.add_argument("--mode", choices=["full", "chunk-only", "embed-only"], default="full",
                       help="Processing mode")
    parser.add_argument("--force", action="store_true",
                       help="Force re-chunking even if files exist")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                       help="Skip documents already in Qdrant")
    
    args = parser.parse_args()
    
    print("="*70)
    print("BATCH DOCUMENT INGESTION PIPELINE")
    print("="*70)
    
    if args.mode in ["full", "chunk-only"]:
        results = chunk_documents(args.source_dir, force=args.force)
        print(f"\n✓ Chunking complete: {len(results)} documents processed")
    
    if args.mode == "full":
        stats = generate_embeddings_and_load(skip_existing=args.skip_existing)
        print(f"\n✓ Embedding complete:")
        print(f"  Documents: {stats['documents_processed']}")
        print(f"  Chunks: {stats['chunks_embedded']}")
        print(f"  Failed: {stats['chunks_failed']}")
        print(f"  Qdrant points: {stats['qdrant_points']}")
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()

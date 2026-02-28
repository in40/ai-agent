#!/usr/bin/env python3
"""Check Vector DB for chunks"""

from qdrant_client import QdrantClient

api_key = '7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d'
client = QdrantClient(host='localhost', port=6333, api_key=api_key)

print("=== Vector DB Check ===\n")

# Get collection info
collections = client.get_collections()
for col in collections.collections:
    info = client.get_collection(col.name)
    print(f"Collection: {col.name}")
    print(f"  Total points: {info.points_count}")
    
    # Search for recent documents (gost-r-50922-2006)
    print(f"\n  Searching for gost-r-50922-2006 chunks...")
    try:
        results = client.scroll(
            collection_name=col.name,
            scroll_filter={
                "must": [
                    {"key": "source", "like": "*gost-r-50922-2006*"}
                ]
            },
            limit=20
        )
        points = results[0]
        print(f"  Found {len(points)} chunks")
        for point in points[:5]:
            source = point.payload.get('source', 'N/A')
            chunk_id = point.payload.get('chunk_id', 'N/A')
            print(f"    - Chunk {chunk_id}: {source[:60]}")
    except Exception as e:
        print(f"  Search error: {e}")
    print()

print("=== Check Complete ===")

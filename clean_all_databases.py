#!/usr/bin/env python3
"""
Clean All Databases
Deletes all data from:
- Qdrant (vector database)
- Neo4j (graph database)
- Document Store (file storage)
"""
import os
import sys
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def clean_qdrant():
    """Clean Qdrant vector database"""
    print("=" * 60)
    print("Cleaning Qdrant Vector Database")
    print("=" * 60)

    try:
        import urllib.request
        import json

        # Get API key from environment or .env
        api_key = os.getenv('QDRANT_API_KEY', '7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d')
        qdrant_url = os.getenv('RAG_QDRANT_URL', 'http://localhost:6333')

        # List collections via REST API (more reliable than Python client)
        req = urllib.request.Request(f'{qdrant_url}/collections')
        req.add_header('api-key', api_key)
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            collections = data.get('result', {}).get('collections', [])
        
        print(f'Found {len(collections)} collections:')
        for col in collections:
            print(f'  - {col["name"]}')

        # Delete all collections
        print()
        print('Deleting all collections...')
        for col in collections:
            col_name = col['name']
            try:
                req = urllib.request.Request(f'{qdrant_url}/collections/{col_name}', method='DELETE')
                req.add_header('api-key', api_key)
                with urllib.request.urlopen(req) as resp:
                    print(f'  ✓ Deleted: {col_name}')
            except Exception as e:
                print(f'  ✗ Error deleting {col_name}: {e}')

        # Verify deletion
        req = urllib.request.Request(f'{qdrant_url}/collections')
        req.add_header('api-key', api_key)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            remaining = data.get('result', {}).get('collections', [])
        
        print()
        print(f'Remaining collections: {len(remaining)}')
        print()
        print('✓ Qdrant vector database cleaned!')
        return True

        # List all collections
        collections = client.get_collections()
        print(f'Found {len(collections.collections)} collections:')
        for col in collections.collections:
            print(f'  - {col.name}')

        # Delete all collections
        print()
        print('Deleting all collections...')
        for col in collections.collections:
            try:
                client.delete_collection(col.name)
                print(f'  ✓ Deleted: {col.name}')
            except Exception as e:
                print(f'  ✗ Error deleting {col.name}: {e}')

        # Verify deletion
        remaining = client.get_collections()
        print()
        print(f'Remaining collections: {len(remaining.collections)}')
        print()
        print('✓ Qdrant vector database cleaned!')
        return True

    except Exception as e:
        print(f'✗ Error cleaning Qdrant: {e}')
        import traceback
        traceback.print_exc()
        return False


def clean_neo4j():
    """Clean Neo4j graph database"""
    print()
    print("=" * 60)
    print("Cleaning Neo4j Graph Database")
    print("=" * 60)

    try:
        from neo4j import GraphDatabase

        # Neo4j connection details (via SSH tunnel on port 7687)
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'GraphRAG2024!')

        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            # Count existing nodes
            count = session.run('MATCH (n) RETURN count(n) as count').single()['count']
            print(f'Nodes before deletion: {count}')

            if count > 0:
                # Delete all nodes and relationships
                result = session.run('MATCH (n) DETACH DELETE n')
                stats = result.consume().counters
                print(f'Deleted {stats.nodes_deleted} nodes')
                print(f'Deleted {stats.relationships_deleted} relationships')
                print(f'Deleted {stats.labels_removed} labels')
            else:
                print('Database was already empty')

            # Verify deletion
            remaining = session.run('MATCH (n) RETURN count(n) as count').single()['count']
            print(f'Remaining nodes: {remaining}')

        driver.close()
        print()
        print('✓ Neo4j graph database cleaned!')
        return True

    except Exception as e:
        print(f'✗ Error cleaning Neo4j: {e}')
        import traceback
        traceback.print_exc()
        return False


def clean_document_store():
    """Clean document store (file storage)"""
    print()
    print("=" * 60)
    print("Cleaning Document Store")
    print("=" * 60)

    try:
        # Import document store config
        doc_store_config_path = project_root / "document-store-mcp-server" / "config.py"
        if doc_store_config_path.exists():
            sys.path.insert(0, str(doc_store_config_path.parent))
            import config as doc_config
            ingested_dir = doc_config.INGESTED_DIR
        else:
            # Fallback to default path
            ingested_dir = project_root / "document-store-mcp-server" / "data" / "ingested"

        print(f'Document store path: {ingested_dir}')

        if not ingested_dir.exists():
            print('Document store directory does not exist (already clean?)')
            print('✓ Document store cleaned!')
            return True

        # Count files before deletion
        file_count = sum(1 for _ in ingested_dir.rglob('*') if _.is_file())
        dir_count = sum(1 for _ in ingested_dir.rglob('*') if _.is_dir())
        print(f'Files before deletion: {file_count}')
        print(f'Subdirectories: {dir_count}')

        if file_count > 0 or dir_count > 0:
            # Delete entire ingested directory
            shutil.rmtree(ingested_dir)
            print(f'Deleted: {ingested_dir}')
            
            # Recreate empty directory
            ingested_dir.mkdir(parents=True, exist_ok=True)
            print('Created fresh empty directory')

        print()
        print('✓ Document store cleaned!')
        return True

    except Exception as e:
        print(f'✗ Error cleaning document store: {e}')
        import traceback
        traceback.print_exc()
        return False


def clean_chroma_fallback():
    """Clean ChromaDB (if still being used as fallback)"""
    print()
    print("=" * 60)
    print("Cleaning ChromaDB (Fallback)")
    print("=" * 60)

    try:
        from rag_component.config import RAG_CHROMA_PERSIST_DIR

        persist_dir = Path(RAG_CHROMA_PERSIST_DIR)
        print(f'ChromaDB path: {persist_dir}')

        if not persist_dir.exists():
            print('ChromaDB directory does not exist (already clean?)')
            print('✓ ChromaDB cleaned!')
            return True

        # Count files before deletion
        file_count = sum(1 for _ in persist_dir.rglob('*') if _.is_file())
        print(f'Files before deletion: {file_count}')

        if file_count > 0:
            shutil.rmtree(persist_dir)
            print(f'Deleted: {persist_dir}')
            
            # Recreate empty directory
            persist_dir.mkdir(parents=True, exist_ok=True)
            print('Created fresh empty directory')

        print('✓ ChromaDB cleaned!')
        return True

    except Exception as e:
        print(f'✗ Error cleaning ChromaDB: {e}')
        return False


def main():
    """Main function"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Complete Database Cleanup Utility                ║")
    print("║  This will DELETE ALL DATA from:                         ║")
    print("║    - Qdrant (Vector DB)                                  ║")
    print("║    - Neo4j (Graph DB)                                    ║")
    print("║    - Document Store (File Storage)                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Confirm deletion
    response = input("⚠️  Are you sure you want to delete ALL data? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cleanup cancelled.")
        sys.exit(0)

    print()

    # Clean databases
    qdrant_ok = clean_qdrant()
    neo4j_ok = clean_neo4j()
    doc_store_ok = clean_document_store()
    chroma_ok = clean_chroma_fallback()

    # Summary
    print()
    print("=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f'Qdrant (Vector):     {"✓ Cleaned" if qdrant_ok else "✗ Failed"}')
    print(f'Neo4j (Graph):       {"✓ Cleaned" if neo4j_ok else "✗ Failed"}')
    print(f'Document Store:      {"✓ Cleaned" if doc_store_ok else "✗ Failed"}')
    print(f'ChromaDB (Fallback): {"✓ Cleaned" if chroma_ok else "✗ Failed/Skipped"}')
    print("=" * 60)

    all_ok = qdrant_ok and neo4j_ok and doc_store_ok
    if all_ok:
        print()
        print("✓ All databases cleaned successfully!")
        sys.exit(0)
    else:
        print()
        print("✗ Some databases failed to clean")
        sys.exit(1)


if __name__ == "__main__":
    main()

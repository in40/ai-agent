#!/usr/bin/env python3
"""
Clean Vector and Graph Databases
Deletes all data from Qdrant (vector) and Neo4j (graph) databases
"""
import os
import sys

def clean_qdrant():
    """Clean Qdrant vector database"""
    print("=" * 60)
    print("Cleaning Qdrant Vector Database")
    print("=" * 60)
    
    try:
        from qdrant_client import QdrantClient
        
        # Get API key from environment or .env
        api_key = os.getenv('QDRANT_API_KEY', '7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d')
        
        # Connect to Qdrant
        client = QdrantClient(host='localhost', port=6333, api_key=api_key)
        
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
        return False


def clean_neo4j():
    """Clean Neo4j graph database"""
    print()
    print("=" * 60)
    print("Cleaning Neo4j Graph Database")
    print("=" * 60)
    
    try:
        from neo4j import GraphDatabase
        
        # Neo4j connection details
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7688')
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
        return False


def main():
    """Main function"""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Database Cleanup Utility                         ║")
    print("║  This will DELETE ALL DATA from vector and graph DBs    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # Confirm deletion
    response = input("Are you sure you want to delete ALL data? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cleanup cancelled.")
        sys.exit(0)
    
    print()
    
    # Clean databases
    qdrant_ok = clean_qdrant()
    neo4j_ok = clean_neo4j()
    
    # Summary
    print()
    print("=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f'Qdrant (Vector):  {"✓ Cleaned" if qdrant_ok else "✗ Failed"}')
    print(f'Neo4j (Graph):    {"✓ Cleaned" if neo4j_ok else "✗ Failed"}')
    print("=" * 60)
    
    if qdrant_ok and neo4j_ok:
        print()
        print("✓ All databases cleaned successfully!")
        sys.exit(0)
    else:
        print()
        print("✗ Some databases failed to clean")
        sys.exit(1)


if __name__ == "__main__":
    main()

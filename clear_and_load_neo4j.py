#!/usr/bin/env python3
"""
Clear Neo4j database and load deduplicated entities.
Uses SSH tunnel connection (localhost:7687).
"""

import json
from neo4j import GraphDatabase
from pathlib import Path
import argparse

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "GraphRAG2024!"


class Neo4jLoader:
    """Clear and load entities into Neo4j"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def clear_database(self, auto_confirm=False):
        """Clear all data from the database"""
        if not auto_confirm:
            response = input("⚠️  This will DELETE ALL data from Neo4j. Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return False
        
        print("\nClearing database...")
        
        with self.driver.session() as session:
            # Drop all relationships first
            print("  Deleting relationships...")
            result = session.run("MATCH ()-[r]->() DELETE r")
            rel_count = sum(1 for _ in result)
            
            # Then delete all nodes
            print("  Deleting nodes...")
            result = session.run("MATCH (n) DELETE n")
            node_count = sum(1 for _ in result)
            
            print(f"✓ Deleted {rel_count} relationships and {node_count} nodes")
            return True
    
    def create_constraints_and_indexes(self):
        """Create constraints and indexes for entities"""
        print("\nCreating constraints and indexes...")
        
        with self.driver.session() as session:
            # Create constraint on normalized_name (for deduplication)
            try:
                session.run("""
                    CREATE CONSTRAINT entity_normalized_name IF NOT EXISTS
                    FOR (e:Entity) REQUIRE e.normalized_name IS UNIQUE
                """)
                print("  ✓ Created constraint on normalized_name")
            except Exception as e:
                print(f"  ⚠ Constraint may already exist: {e}")
            
            # Create index on text for faster lookups
            try:
                session.run("""
                    CREATE INDEX entity_text IF NOT EXISTS
                    FOR (e:Entity) ON (e.text)
                """)
                print("  ✓ Created index on text")
            except Exception as e:
                print(f"  ⚠ Index may already exist: {e}")
            
            # Create index on type
            try:
                session.run("""
                    CREATE INDEX entity_type IF NOT EXISTS
                    FOR (e:Entity) ON (e.type)
                """)
                print("  ✓ Created index on type")
            except Exception as e:
                print(f"  ⚠ Index may already exist: {e}")
            
            # Create index on doc_name for relationships
            try:
                session.run("""
                    CREATE INDEX document_name IF NOT EXISTS
                    FOR (d:Document) ON (d.name)
                """)
                print("  ✓ Created index on document name")
            except Exception as e:
                print(f"  ⚠ Index may already exist: {e}")
    
    def load_entities(self, entities_file):
        """Load deduplicated entities from JSON file"""
        with open(entities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        print(f"\nLoading {len(entities)} entities...")
        
        batch_size = 50
        loaded_count = 0
        
        with self.driver.session() as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                
                # Load entities with MERGE on normalized_name
                session.run("""
                    UNWIND $batch AS entity
                    MERGE (e:Entity {normalized_name: toLower(entity.text)})
                    SET e.text = entity.text,
                        e.type = COALESCE(entity.type, 'UNKNOWN'),
                        e.confidence = COALESCE(entity.confidence, 0.5),
                        e.source = COALESCE(entity.source, 'pattern'),
                        e.aliases = COALESCE(entity.aliases, []),
                        e.doc_names = COALESCE(entity.doc_names, []),
                        e.merge_count = COALESCE(entity.merge_count, 1)
                """, batch=batch)
                
                loaded_count += len(batch)
                print(f"  Loaded {loaded_count}/{len(entities)} entities")
        
        print(f"✓ Loaded {loaded_count} entities")
        return loaded_count
    
    def load_documents(self, entities_file):
        """Extract and load unique documents from entities"""
        with open(entities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        
        # Extract unique documents
        docs = set()
        for entity in entities:
            doc_names = entity.get('doc_names', [])
            docs.update(doc_names)
        
        print(f"\nLoading {len(docs)} documents...")
        
        batch_size = 100
        loaded_count = 0
        
        with self.driver.session() as session:
            for i in range(0, len(docs), batch_size):
                batch = list(docs)[i:i + batch_size]
                
                session.run("""
                    UNWIND $batch AS doc_name
                    MERGE (d:Document {name: doc_name})
                    SET d.type = 'GOST'
                """, batch=batch)
                
                loaded_count += len(batch)
        
        print(f"✓ Loaded {loaded_count} documents")
        return loaded_count
    
    def create_entity_document_relationships(self, entities_file):
        """Create MENTIONS relationships between entities and documents"""
        with open(entities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        print(f"\nCreating entity-document relationships...")
        
        batch_size = 50
        rel_count = 0
        
        with self.driver.session() as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                
                # Create relationships
                result = session.run("""
                    UNWIND $batch AS entity
                    MATCH (e:Entity {normalized_name: toLower(entity.text)})
                    UNWIND entity.doc_names AS doc_name
                    MATCH (d:Document {name: doc_name})
                    MERGE (e)-[:MENTIONS]->(d)
                """, batch=batch)
                
                rel_count += sum(1 for _ in result)
        
        print(f"✓ Created {rel_count} MENTIONS relationships")
        return rel_count
    
    def verify_load(self):
        """Verify the loaded data"""
        print("\nVerifying loaded data...")
        
        with self.driver.session() as session:
            # Count entities
            result = session.run("MATCH (e:Entity) RETURN count(e) as count")
            entity_count = result.single()['count']
            
            # Count documents
            result = session.run("MATCH (d:Document) RETURN count(d) as count")
            doc_count = result.single()['count']
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            
            # Check for ФСТЭК entities
            result = session.run("""
                MATCH (e:Entity)
                WHERE toLower(e.text) CONTAINS 'фстэк'
                RETURN e.text as name, e.merge_count as merged
                ORDER BY e.text
            """)
            
            fstek_entities = [record['name'] for record in result]
            
            print(f"\n{'='*60}")
            print("LOADED DATA SUMMARY")
            print(f"{'='*60}")
            print(f"  Entities:     {entity_count}")
            print(f"  Documents:    {doc_count}")
            print(f"  Relationships: {rel_count}")
            print(f"\n  ФСТЭК entities loaded: {len(fstek_entities)}")
            for name in fstek_entities:
                print(f"    - {name}")
            
            return {
                'entities': entity_count,
                'documents': doc_count,
                'relationships': rel_count,
                'fstek_count': len(fstek_entities)
            }


def main():
    parser = argparse.ArgumentParser(description='Clear and load Neo4j with deduplicated entities')
    parser.add_argument('--input', default='/root/qwen/ai_agent/deduplicated_entities_strict/all_entities_strict.json',
                       help='Input deduplicated entities JSON file')
    parser.add_argument('--uri', default=NEO4J_URI, help='Neo4j URI')
    parser.add_argument('--user', default=NEO4J_USER, help='Neo4j username')
    parser.add_argument('--password', default=NEO4J_PASSWORD, help='Neo4j password')
    parser.add_argument('--no-clear', action='store_true', 
                       help='Skip database clearing (load only)')
    parser.add_argument('--yes', action='store_true',
                       help='Auto-confirm database clearing')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("CLEAR NEO4J AND LOAD DEDUPLICATED ENTITIES")
    print("=" * 80)
    
    loader = Neo4jLoader(args.uri, args.user, args.password)
    
    try:
        # Clear database if not skipped
        if not args.no_clear:
            loader.clear_database(auto_confirm=args.yes)
        
        # Create constraints and indexes
        loader.create_constraints_and_indexes()
        
        # Load documents first
        loader.load_documents(args.input)
        
        # Load entities
        loader.load_entities(args.input)
        
        # Create relationships
        loader.create_entity_document_relationships(args.input)
        
        # Verify
        stats = loader.verify_load()
        
    finally:
        loader.close()
    
    print("\n" + "=" * 80)
    print("LOAD COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

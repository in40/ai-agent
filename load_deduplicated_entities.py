#!/usr/bin/env python3
"""
Load deduplicated entities into Neo4j graph database.
Merges duplicate entities and preserves all relationships.
"""

import json
from neo4j import GraphDatabase
from pathlib import Path
import argparse

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


class DeduplicatedEntityLoader:
    """Load deduplicated entities into Neo4j"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_entity_constraints_and_indexes(self):
        """Create constraints and indexes for deduplicated entities"""
        with self.driver.session() as session:
            # Create constraint on normalized_name (for deduplication)
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) 
                REQUIRE e.normalized_name IS UNIQUE
            """)
            
            # Create index on text for faster lookups
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (e:Entity) 
                ON (e.text)
            """)
            
            # Create index on type
            session.run("""
                CREATE INDEX IF NOT EXISTS FOR (e:Entity) 
                ON (e.type)
            """)
    
    def load_deduplicated_entities(self, entities_file):
        """Load deduplicated entities from JSON file"""
        with open(entities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        print(f"\nLoading {len(entities)} deduplicated entities...")
        
        batch_size = 100
        loaded_count = 0
        
        with self.driver.session() as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]
                
                # Use unwind for batch processing
                session.run("""
                    UNWIND $batch AS entity
                    MERGE (e:Entity {normalized_name: toLower(entity.text)})
                    SET e.text = COALESCE(e.text, entity.text),
                        e.type = COALESCE(e.type, entity.type),
                        e.confidence = COALESCE(e.confidence, 0.5),
                        e.source = COALESCE(e.source, 'pattern'),
                        e.aliases = COALESCE(entity.aliases, []),
                        e.doc_names = COALESCE(entity.doc_names, []),
                        e.merge_count = COALESCE(entity.merge_count, 1)
                """, batch=batch)
                
                loaded_count += len(batch)
                print(f"  Processed {loaded_count}/{len(entities)} entities")
        
        print(f"✓ Loaded {loaded_count} deduplicated entities")
        return loaded_count
    
    def merge_entities_with_relationships(self, entities_file):
        """
        Merge duplicate entities while preserving ALL relationships.
        This is the key deduplication step.
        """
        with open(entities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        print(f"\nMerging entities with relationships...")
        
        with self.driver.session() as session:
            # For each deduplicated entity, merge all its aliases into the canonical form
            for entity in entities:
                if entity.get('aliases'):
                    canonical_name = entity['text']
                    aliases = entity['aliases']
                    
                    # Merge each alias into the canonical entity
                    for alias in aliases:
                        session.run("""
                            MATCH (alias_node:Entity {normalized_name: toLower($alias)})
                            MATCH (canonical:Entity {normalized_name: toLower($canonical)})
                            
                            // Move all relationships from alias to canonical
                            OPTIONAL MATCH (alias_node)-[r:MENTIONS]->(doc)
                            CREATE (canonical)-[new_mention:MENTIONS]->(doc)
                            SET new_mention = r
                            
                            OPTIONAL MATCH (dev)-[r:DEVELOPED_BY]->(alias_node)
                            CREATE (dev)-[new_dev:DEVELOPED_BY]->(canonical)
                            SET new_dev = r
                            
                            // Delete the alias node after merging relationships
                            DETACH DELETE alias_node
                        """, alias=alias, canonical=canonical_name)
                    
                    print(f"  Merged {len(aliases)} aliases into '{canonical_name}'")
        
        print("✓ Entity merging complete")
    
    def verify_deduplication(self):
        """Verify deduplication results"""
        with self.driver.session() as session:
            # Count entities by normalized name (should all be unique)
            result = session.run("""
                MATCH (e:Entity)
                RETURN count(DISTINCT e.normalized_name) as unique_entities,
                       count(e) as total_nodes
            """)
            record = result.single()
            
            print(f"\nDeduplication Verification:")
            print(f"  Unique normalized names: {record['unique_entities']}")
            print(f"  Total Entity nodes: {record['total_nodes']}")
            
            # Check for ФСТЭК specifically
            result = session.run("""
                MATCH (e:Entity)
                WHERE toLower(e.text) CONTAINS 'фстэк'
                RETURN e.text as name, e.merge_count as merged, size(e.aliases) as aliases
                ORDER BY e.text
            """)
            
            print(f"\nФСТЭК entities after merge:")
            for record in result:
                print(f"  • {record['name']} (merged: {record['merged']}, aliases: {record['aliases']})")


def main():
    parser = argparse.ArgumentParser(description='Load deduplicated entities into Neo4j')
    parser.add_argument('--input', default='/root/qwen/ai_agent/deduplicated_entities/all_entities_deduplicated.json',
                       help='Input deduplicated entities JSON file')
    parser.add_argument('--uri', default=NEO4J_URI, help='Neo4j URI')
    parser.add_argument('--user', default=NEO4J_USER, help='Neo4j username')
    parser.add_argument('--password', default=NEO4J_PASSWORD, help='Neo4j password')
    parser.add_argument('--skip-merge', action='store_true', 
                       help='Skip entity merging (load only)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LOAD DEDUPLICATED ENTITIES INTO NEO4J")
    print("=" * 80)
    
    loader = DeduplicatedEntityLoader(args.uri, args.user, args.password)
    
    try:
        # Create constraints and indexes
        print("\nCreating constraints and indexes...")
        loader.create_entity_constraints_and_indexes()
        print("✓ Constraints created")
        
        # Load deduplicated entities
        loader.load_deduplicated_entities(args.input)
        
        if not args.skip_merge:
            # Merge entities with relationships
            loader.merge_entities_with_relationships(args.input)
        
        # Verify results
        loader.verify_deduplication()
        
    finally:
        loader.close()
    
    print("\n" + "=" * 80)
    print("DEDUPLICATION LOADING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

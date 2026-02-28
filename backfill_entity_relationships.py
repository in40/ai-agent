#!/usr/bin/env python3
"""
Backfill MENTIONS relationships between Chunks and Entities.
Entities and Chunks exist but relationships were not created during ingestion.
This script creates MENTIONS relationships based on document co-occurrence.
"""
import sys
sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

from neo4j_integration import get_neo4j_connection

def backfill_mentions_relationships():
    """Create MENTIONS relationships between chunks and entities from same document"""
    
    neo4j = get_neo4j_connection()
    if not neo4j or not neo4j.connected:
        print("ERROR: Could not connect to Neo4j")
        return
    
    with neo4j.driver.session() as session:
        print("Starting backfill of MENTIONS relationships...")
        
        # Get all entities with their document info
        entities_result = session.run("""
            MATCH (e:Entity)
            RETURN e.name as name, e.type as type, e.updated_at as updated_at
            ORDER BY e.updated_at DESC
        """)
        
        entities = list(entities_result)
        print(f"Found {len(entities)} entities to process")
        
        relationships_created = 0
        
        for entity_record in entities:
            entity_name = entity_record['name']
            entity_type = entity_record['type']
            entity_updated = entity_record['updated_at']
            
            # Find chunks from the same time period (entity was extracted from these chunks)
            # We use updated_at timestamp to match chunks created around same time
            chunks_result = session.run("""
                MATCH (c:Chunk)
                WHERE c.chunk_id STARTS WITH 'docstore_job_'
                AND c.content CONTAINS $entity_name
                RETURN c.chunk_id as chunk_id, c.content as content
                LIMIT 10
            """, {'entity_name': entity_name})
            
            chunks = list(chunks_result)
            
            for chunk_record in chunks:
                chunk_id = chunk_record['chunk_id']
                
                # Create MENTIONS relationship
                session.run("""
                    MATCH (c:Chunk {chunk_id: $chunk_id})
                    MATCH (e:Entity {name: $entity_name, type: $entity_type})
                    MERGE (c)-[:MENTIONS]->(e)
                """, {
                    'chunk_id': chunk_id,
                    'entity_name': entity_name,
                    'entity_type': entity_type
                })
                
                relationships_created += 1
                
                if relationships_created % 100 == 0:
                    print(f"  Created {relationships_created} relationships...")
        
        print(f"\nCompleted! Created {relationships_created} MENTIONS relationships")
        
        # Verify
        result = session.run("MATCH ()-[r:MENTIONS]->() RETURN count(r) as count")
        count = result.single()['count']
        print(f"Total MENTIONS relationships in database: {count}")

if __name__ == '__main__':
    backfill_mentions_relationships()

#!/usr/bin/env python3
"""Check Neo4j graph for entities from recent ingestion"""

from neo4j import GraphDatabase

# Neo4j connection details
uri = "bolt://localhost:7687"
username = "neo4j"
password = "GraphRAG2024!"

driver = GraphDatabase.driver(uri, auth=(username, password))

print("=== Neo4j Graph Check ===\n")

with driver.session() as session:
    # Check total entities
    result = session.run("MATCH (e:Entity) RETURN count(e) as count")
    total_entities = result.single()["count"]
    print(f"Total Entities: {total_entities}")
    
    # Check entity types
    result = session.run("""
        MATCH (e:Entity) 
        RETURN e.type as type, count(e) as count 
        ORDER BY count DESC
    """)
    print("\nEntities by Type:")
    for record in result:
        print(f"  - {record['type']}: {record['count']}")
    
    # Check relationships
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    total_rels = result.single()["count"]
    print(f"\nTotal Relationships: {total_rels}")
    
    # Check recent entities (from gost-r-50922-2006)
    print("\nRecent Entities (from gost-r-50922-2006):")
    result = session.run("""
        MATCH (e:Entity) 
        WHERE e.source CONTAINS 'gost-r-50922-2006' OR e.document CONTAINS 'gost-r-50922-2006'
        RETURN e.name as name, e.type as type, e.source as source
        LIMIT 10
    """)
    for record in result:
        print(f"  - {record['name']} ({record['type']})")
    
    # Check Document chunks in graph
    print("\nDocument Chunks in Graph:")
    result = session.run("""
        MATCH (c:Chunk) 
        WHERE c.source CONTAINS 'gost-r-50922-2006'
        RETURN count(c) as count
    """)
    chunk_count = result.single()["count"]
    print(f"  Chunks stored: {chunk_count}")

driver.close()
print("\n=== Graph Check Complete ===")

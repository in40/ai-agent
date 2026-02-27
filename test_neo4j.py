#!/usr/bin/env python3
from neo4j import GraphDatabase

uri = 'bolt://localhost:7688'
user = 'neo4j'
password = 'GraphRAG2024!'

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run('MATCH (n) RETURN count(n) as count')
        count = result.single()['count']
        print(f'✓ Neo4j connection successful!')
        print(f'  Total nodes: {count}')
        
        labels = session.run('CALL db.labels()')
        print(f'  Node labels: {[r[0] for r in labels]}')
        
        rels = session.run('CALL db.relationshipTypes()')
        print(f'  Relationship types: {[r[0] for r in rels]}')
    driver.close()
except Exception as e:
    print(f'✗ Neo4j connection failed: {e}')

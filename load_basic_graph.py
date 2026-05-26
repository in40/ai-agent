#!/usr/bin/env python3
"""
Load GOST Entities and Formulas to Neo4j (Basic Loading - Approach A)

This script:
1. Creates Neo4j schema (constraints + indexes)
2. Loads all entities as nodes
3. Loads all formulas as nodes
4. Links to documents via metadata

Usage:
    python load_basic_graph.py [--neo4j-uri BOLT_URL] [--neo4j-user USER] [--neo4j-pass PASS]
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

def load_entities_and_formulas(entities_file: str, formulas_file: str) -> tuple:
    """Load entities and formulas from JSON files"""
    
    # Load entities
    with open(entities_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        entities = data.get('entities', [])
    
    # Load formulas
    with open(formulas_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        formulas = data.get('formulas', [])
    
    return entities, formulas


def create_schema(driver):
    """Create Neo4j schema (constraints and indexes)"""
    
    print("Creating Neo4j schema...")
    
    with driver.session() as session:
        # Create constraints for uniqueness
        print("  Creating constraints...")
        session.run("""
            CREATE CONSTRAINT entity_name IF NOT EXISTS 
            FOR (e:Entity) REQUIRE e.name IS UNIQUE
        """)
        
        session.run("""
            CREATE CONSTRAINT formula_expr IF NOT EXISTS 
            FOR (f:Formula) REQUIRE f.expression IS UNIQUE
        """)
        
        session.run("""
            CREATE CONSTRAINT doc_id IF NOT EXISTS 
            FOR (d:Document) REQUIRE d.doc_id IS UNIQUE
        """)
        
        # Create indexes for faster queries
        print("  Creating indexes...")
        session.run("""
            CREATE INDEX entity_type IF NOT EXISTS 
            FOR (e:Entity) ON (e.type)
        """)
        
        session.run("""
            CREATE INDEX formula_type IF NOT EXISTS 
            FOR (f:Formula) ON (f.type)
        """)
        
        session.run("""
            CREATE INDEX entity_source IF NOT EXISTS 
            FOR (e:Entity) ON (e.source)
        """)
        
        session.run("""
            CREATE INDEX formula_doc IF NOT EXISTS 
            FOR (f:Formula) ON (f.doc_name)
        """)
        
        print("  Schema created successfully!")


def load_entities(driver, entities: List[Dict[str, Any]], batch_size: int = 1000):
    """Load entities to Neo4j in batches"""
    
    print(f"\nLoading {len(entities)} entities...")
    
    # Group entities by source document for batching
    docs = set(ent.get('doc', ent.get('doc_name', 'unknown')) for ent in entities)
    print(f"  From {len(docs)} documents")
    
    with driver.session() as session:
        loaded = 0
        
        for i, entity in enumerate(entities):
            try:
                session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type,
                        e.source = COALESCE($source, 'unknown'),
                        e.doc_name = $doc_name,
                        e.confidence = COALESCE($confidence, 0.5),
                        e.created_at = datetime()
                """, {
                    'name': entity['text'],
                    'type': entity.get('type', 'UNKNOWN'),
                    'source': entity.get('source', 'pattern'),
                    'doc_name': entity.get('doc', entity.get('doc_name', '')),
                    'confidence': entity.get('confidence', 0.5)
                })
                
                loaded += 1
                
                if loaded % 100 == 0:
                    print(f"    Loaded {loaded} entities...")
                    
            except Exception as e:
                print(f"    Warning: Could not load entity '{entity.get('text', 'unknown')}': {e}")
        
        print(f"  Successfully loaded {loaded} entities")
        return loaded


def load_formulas(driver, formulas: List[Dict[str, Any]], batch_size: int = 1000):
    """Load formulas to Neo4j in batches"""
    
    print(f"\nLoading {len(formulas)} formulas...")
    
    # Group by document
    docs = set(f.get('doc_name', 'unknown') for f in formulas)
    print(f"  From {len(docs)} documents")
    
    with driver.session() as session:
        loaded = 0
        
        for i, formula in enumerate(formulas):
            try:
                session.run("""
                    MERGE (f:Formula {expression: $expression})
                    SET f.type = $type,
                        f.doc_name = $doc_name,
                        f.chunk_index = COALESCE($chunk_index, 0),
                        e.created_at = datetime()
                """, {
                    'expression': formula['text'],
                    'type': formula.get('type', 'UNKNOWN'),
                    'doc_name': formula.get('doc_name', ''),
                    'chunk_index': formula.get('chunk_index', 0)
                })
                
                loaded += 1
                
                if loaded % 500 == 0:
                    print(f"    Loaded {loaded} formulas...")
                    
            except Exception as e:
                print(f"    Warning: Could not load formula '{formula.get('text', 'unknown')}': {e}")
        
        print(f"  Successfully loaded {loaded} formulas")
        return loaded


def create_document_nodes(driver, entities: List[Dict], formulas: List[Dict]):
    """Create Document nodes from entity/formula metadata"""
    
    print("\nCreating document nodes...")
    
    # Extract unique documents
    doc_ids = set()
    for ent in entities:
        doc_id = ent.get('doc', ent.get('doc_name', ''))
        if doc_id:
            doc_ids.add(doc_id)
    
    for formula in formulas:
        doc_id = formula.get('doc_name', '')
        if doc_id:
            doc_ids.add(doc_id)
    
    print(f"  Found {len(doc_ids)} unique documents")
    
    with driver.session() as session:
        loaded = 0
        
        for doc_id in doc_ids:
            try:
                session.run("""
                    MERGE (d:Document {doc_id: $doc_id})
                    SET d.filename = $filename,
                        d.created_at = datetime()
                """, {
                    'doc_id': doc_id,
                    'filename': doc_id + '.pdf'  # Default filename
                })
                loaded += 1
            except Exception as e:
                print(f"    Warning: Could not create document '{doc_id}': {e}")
        
        print(f"  Created {loaded} document nodes")


def load_entities_with_links(driver, entities: List[Dict], formulas: List[Dict]):
    """Load entities and create links to documents"""
    
    print("\nLoading entities with document links...")
    
    with driver.session() as session:
        loaded = 0
        
        for entity in entities:
            try:
                # Create entity node
                session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type,
                        e.source = COALESCE($source, 'unknown'),
                        e.confidence = COALESCE($confidence, 0.5)
                """, {
                    'name': entity['text'],
                    'type': entity.get('type', 'UNKNOWN'),
                    'source': entity.get('source', 'pattern'),
                    'confidence': entity.get('confidence', 0.5)
                })
                
                # Link to document if available
                doc_name = entity.get('doc', entity.get('doc_name', ''))
                if doc_name:
                    session.run("""
                        MATCH (e:Entity {name: $entity_name})
                        MATCH (d:Document {doc_id: $doc_id})
                        MERGE (e)-[:APPEARS_IN]->(d)
                    """, {
                        'entity_name': entity['text'],
                        'doc_id': doc_name
                    })
                
                loaded += 1
                
                if loaded % 100 == 0:
                    print(f"    Loaded {loaded} entities...")
                    
            except Exception as e:
                print(f"    Warning: Entity '{entity.get('text', 'unknown')}': {e}")
        
        print(f"  Successfully loaded {loaded} entities with links")


def load_formulas_with_links(driver, formulas: List[Dict]):
    """Load formulas and create links to documents"""
    
    print("\nLoading formulas with document links...")
    
    with driver.session() as session:
        loaded = 0
        
        for formula in formulas:
            try:
                # Create formula node
                session.run("""
                    MERGE (f:Formula {expression: $expression})
                    SET f.type = $type,
                        f.chunk_index = COALESCE($chunk_index, 0)
                """, {
                    'expression': formula['text'],
                    'type': formula.get('type', 'UNKNOWN'),
                    'chunk_index': formula.get('chunk_index', 0)
                })
                
                # Link to document if available
                doc_name = formula.get('doc_name', '')
                if doc_name:
                    session.run("""
                        MATCH (f:Formula {expression: $formula_expr})
                        MATCH (d:Document {doc_id: $doc_id})
                        MERGE (f)-[:APPEARS_IN]->(d)
                    """, {
                        'formula_expr': formula['text'],
                        'doc_id': doc_name
                    })
                
                loaded += 1
                
                if loaded % 500 == 0:
                    print(f"    Loaded {loaded} formulas...")
                    
            except Exception as e:
                print(f"    Warning: Formula '{formula.get('text', 'unknown')}': {e}")
        
        print(f"  Successfully loaded {loaded} formulas with links")


def get_graph_stats(driver):
    """Get basic graph statistics"""
    
    print("\nGraph Statistics:")
    
    with driver.session() as session:
        # Count nodes by label
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)
        
        for record in result:
            print(f"  {record['label']}: {record['count']}")
        
        # Count relationships
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)
        
        print("\n  Relationships:")
        for record in result:
            print(f"    {record['rel_type']}: {record['count']}")


def main():
    parser = argparse.ArgumentParser(description='Load GOST entities and formulas to Neo4j')
    parser.add_argument('--neo4j-uri', default=NEO4J_URI, help='Neo4j URI (default: bolt://localhost:7687)')
    parser.add_argument('--neo4j-user', default=NEO4J_USER, help='Neo4j username (default: neo4j)')
    parser.add_argument('--neo4j-pass', default=NEO4J_PASS, help='Neo4j password (default: password)')
    parser.add_argument('--entities', default='/root/qwen/ai_agent/extraction_results_final/all_entities.json',
                       help='Entities JSON file')
    parser.add_argument('--formulas', default='/root/qwen/ai_agent/extraction_results_with_formulas/all_formulas.json',
                       help='Formulas JSON file')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("GOST GRAPH LOADING - BASIC (Approach A)")
    print("=" * 80)
    
    # Load data from files
    print("\nLoading data from files...")
    entities, formulas = load_entities_and_formulas(args.entities, args.formulas)
    print(f"  Entities: {len(entities)}")
    print(f"  Formulas: {len(formulas)}")
    
    # Connect to Neo4j
    print(f"\nConnecting to Neo4j at {args.neo4j_uri}...")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_pass))
        driver.verify_connectivity()
        print("  Connected successfully!")
    except Exception as e:
        print(f"  ERROR: Could not connect to Neo4j: {e}")
        print("\nMake sure Neo4j is running:")
        print("  docker start neo4j  # if using Docker")
        print("  # or check service status")
        sys.exit(1)
    
    try:
        # Create schema
        create_schema(driver)
        
        # Create document nodes first
        create_document_nodes(driver, entities, formulas)
        
        # Load entities with links
        load_entities_with_links(driver, entities)
        
        # Load formulas with links
        load_formulas_with_links(driver, formulas)
        
        # Show statistics
        get_graph_stats(driver)
        
        print("\n" + "=" * 80)
        print("LOADING COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Test queries in Neo4j Browser")
        print("2. Add relationships (see load_relationships.py)")
        print("3. Validate graph quality manually")
        
    except Exception as e:
        print(f"\nERROR during loading: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()


if __name__ == "__main__":
    main()

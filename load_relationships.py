#!/usr/bin/env python3
"""
Load Inferred Relationships to Neo4j (Approach B)

This script:
1. Reads entities and formulas from Neo4j
2. Infers relationships based on co-occurrence patterns
3. Loads relationships to Neo4j with confidence scores

Usage:
    python load_relationships.py [--neo4j-uri BOLT_URL] [--neo4j-user USER] [--neo4j-pass PASS]
"""

import sys
import json
import argparse
from neo4j import GraphDatabase
from collections import defaultdict

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"


def get_entities_by_doc(driver):
    """Get all entities grouped by document"""
    
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Entity)-[:APPEARS_IN]->(d:Document)
            RETURN d.doc_id as doc_id, collect(e.name) as entities
        """)
        
        docs = {}
        for record in result:
            docs[record['doc_id']] = record['entities']
        
        return docs


def get_formulas_by_doc(driver):
    """Get all formulas grouped by document"""
    
    with driver.session() as session:
        result = session.run("""
            MATCH (f:Formula)-[:APPEARS_IN]->(d:Document)
            RETURN d.doc_id as doc_id, collect(f.expression) as formulas
        """)
        
        docs = {}
        for record in result:
            docs[record['doc_id']] = record['formulas']
        
        return docs


def infer_entity_relationships(entities_by_doc):
    """
    Infer relationships between entities based on co-occurrence
    
    Rules:
    - Same chunk → MENTIONS relationship
    - Standard + Organization in same doc → DEVELOPED_BY
    - Standard + Standard in same doc → REFERENCES
    """
    
    relationships = []
    
    for doc_id, entities in entities_by_doc.items():
        # Rule 1: All entities in same document mention each other
        for i, ent1 in enumerate(entities):
            for ent2 in entities[i+1:]:
                if ent1 != ent2:
                    relationships.append({
                        'source': ent1,
                        'target': ent2,
                        'type': 'MENTIONS',
                        'confidence': 0.6,
                        'evidence': f'same_document:{doc_id}'
                    })
    
    return relationships


def infer_formula_relationships(driver):
    """
    Infer relationships between formulas
    
    Rules:
    - Formula uses crypto function → USES_FUNCTION
    - Similar formula patterns → RELATED_TO
    """
    
    relationships = []
    
    with driver.session() as session:
        # Get all crypto functions
        crypto_funcs_result = session.run("""
            MATCH (f:Formula {type: 'CRYPTO_FUNCTION'})
            RETURN f.expression as func
        """)
        
        crypto_functions = [r['func'] for r in crypto_funcs_result]
        
        # Get all variable assignments
        vars_result = session.run("""
            MATCH (f:Formula {type: 'VARIABLE_ASSIGNMENT'})
            RETURN f.expression as var, f.doc_name as doc
        """)
        
        variables = [(r['var'], r['doc']) for r in vars_result]
        
        # Rule: Variable uses crypto function if function name in variable expression
        for var_expr, doc in variables:
            for func in crypto_functions:
                if func in var_expr:
                    relationships.append({
                        'source': var_expr,
                        'target': func,
                        'type': 'USES_FUNCTION',
                        'confidence': 0.9,
                        'evidence': f'text_contains:{doc}'
                    })
    
    return relationships


def infer_standard_relationships(driver):
    """
    Infer relationships between standards and organizations
    
    Rules:
    - Standard + Organization in same doc → DEVELOPED_BY
    - Standard references another standard → REFERENCES
    """
    
    relationships = []
    
    with driver.session() as session:
        # Get documents with both standards and organizations
        result = session.run("""
            MATCH (d:Document)
            OPTIONAL MATCH (d)<-[:APPEARS_IN]-(e1:Entity {type: 'STANDARD'})
            OPTIONAL MATCH (d)<-[:APPEARS_IN]-(e2:Entity {type: 'ORGANIZATION'})
            WHERE e1 IS NOT NULL AND e2 IS NOT NULL
            RETURN d.doc_id as doc_id, e1.name as standard, e2.name as org
        """)
        
        for record in result:
            relationships.append({
                'source': record['standard'],
                'target': record['org'],
                'type': 'DEVELOPED_BY',
                'confidence': 0.8,
                'evidence': f'same_document:{record["doc_id"]}'
            })
    
    return relationships


def load_relationships(driver, relationships, batch_size=500):
    """Load relationships to Neo4j"""
    
    print(f"\nLoading {len(relationships)} relationships...")
    
    with driver.session() as session:
        loaded = 0
        errors = 0
        
        for i, rel in enumerate(relationships):
            try:
                session.run("""
                    MATCH (source {name: $source_name})
                    MATCH (target {name: $target_name})
                    WHERE source IS NOT NULL AND target IS NOT NULL
                    MERGE (source)-[r:MENTIONS]->(target)
                    SET r.confidence = $confidence,
                        r.evidence = $evidence,
                        r.created_at = datetime()
                """, {
                    'source_name': rel['source'],
                    'target_name': rel['target'],
                    'confidence': rel.get('confidence', 0.5),
                    'evidence': rel.get('evidence', '')
                })
                
                loaded += 1
                
                if loaded % 500 == 0:
                    print(f"    Loaded {loaded} relationships...")
                    
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(f"    Warning: Could not create relationship {rel['source']}→{rel['target']}: {e}")
        
        print(f"  Successfully loaded {loaded} relationships")
        if errors > 0:
            print(f"  Skipped {errors} relationships (missing nodes)")


def load_relationships_generic(driver, relationships):
    """Load relationships with dynamic relationship types"""
    
    print(f"\nLoading {len(relationships)} relationships...")
    
    with driver.session() as session:
        loaded = 0
        
        for i, rel in enumerate(relationships):
            try:
                # Use MERGE with relationship type
                rel_type = rel['type'].replace(' ', '_').upper()
                
                session.run(f"""
                    MATCH (source {{name: $source_name}})
                    MATCH (target {{name: $target_name}})
                    WHERE source IS NOT NULL AND target IS NOT NULL
                    MERGE (source)-[r:{rel_type}]->(target)
                    SET r.confidence = $confidence,
                        r.evidence = $evidence,
                        r.created_at = datetime()
                """, {
                    'source_name': rel['source'],
                    'target_name': rel['target'],
                    'confidence': rel.get('confidence', 0.5),
                    'evidence': rel.get('evidence', '')
                })
                
                loaded += 1
                
                if loaded % 500 == 0:
                    print(f"    Loaded {loaded} relationships...")
                    
            except Exception as e:
                if i < 10:
                    print(f"    Warning: Could not create {rel['type']} {rel['source']}→{rel['target']}: {e}")
        
        print(f"  Successfully loaded {loaded} relationships")


def get_graph_stats(driver):
    """Get graph statistics"""
    
    print("\nGraph Statistics:")
    
    with driver.session() as session:
        # Node counts
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)
        
        print("  Nodes:")
        for record in result:
            print(f"    {record['label']}: {record['count']}")
        
        # Relationship counts
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)
        
        print("  Relationships:")
        for record in result:
            print(f"    {record['rel_type']}: {record['count']}")


def main():
    parser = argparse.ArgumentParser(description='Load inferred relationships to Neo4j')
    parser.add_argument('--neo4j-uri', default=NEO4J_URI)
    parser.add_argument('--neo4j-user', default=NEO4J_USER)
    parser.add_argument('--neo4j-pass', default=NEO4J_PASS)
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("GOST GRAPH LOADING - RELATIONSHIPS (Approach B)")
    print("=" * 80)
    
    # Connect to Neo4j
    print(f"\nConnecting to Neo4j at {args.neo4j_uri}...")
    try:
        driver = GraphDatabase.driver(args.neo4j_uri, auth=(args.neo4j_user, args.neo4j_pass))
        driver.verify_connectivity()
        print("  Connected successfully!")
    except Exception as e:
        print(f"  ERROR: Could not connect to Neo4j: {e}")
        sys.exit(1)
    
    try:
        # Get existing data
        print("\nAnalyzing existing graph...")
        entities_by_doc = get_entities_by_doc(driver)
        print(f"  Found {len(entities_by_doc)} documents with entities")
        
        # Infer relationships
        print("\nInferring relationships...")
        
        # Entity co-occurrence relationships
        entity_rels = infer_entity_relationships(entities_by_doc)
        print(f"  Entity MENTIONS: {len(entity_rels)}")
        
        # Standard-Organization relationships
        standard_rels = infer_standard_relationships(driver)
        print(f"  Standard DEVELOPED_BY: {len(standard_rels)}")
        
        # Formula relationships
        formula_rels = infer_formula_relationships(driver)
        print(f"  Formula USES_FUNCTION: {len(formula_rels)}")
        
        total_rels = len(entity_rels) + len(standard_rels) + len(formula_rels)
        print(f"\n  Total relationships to load: {total_rels}")
        
        # Load relationships
        all_rels = entity_rels + standard_rels + formula_rels
        load_relationships_generic(driver, all_rels)
        
        # Show statistics
        get_graph_stats(driver)
        
        print("\n" + "=" * 80)
        print("RELATIONSHIP LOADING COMPLETE!")
        print("=" * 80)
        
        print("\nSample queries to try:")
        print("""
          // Find entities mentioned together
          MATCH (e1:Entity)-[:MENTIONS]-(e2:Entity)
          RETURN e1.name, e2.name LIMIT 20;
          
          // Find standards and their developers
          MATCH (s:Entity {type:'STANDARD'})-[:DEVELOPED_BY]->(o:Entity {type:'ORGANIZATION'})
          RETURN s.name, o.name LIMIT 20;
          
          // Find most connected entities
          MATCH (e:Entity)-[]-(related)
          RETURN e.name, COUNT(related) as connections
          ORDER BY connections DESC LIMIT 10;
        """)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GOST Knowledge Graph - Verification Script

Verifies that Neo4j database is properly configured with:
- All entities loaded
- All relationships created
- No orphaned entities
- Correct entity types
"""

from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "GraphRAG2024!"


def verify_database():
    """Verify Neo4j database state"""
    
    print("=" * 80)
    print("GOST KNOWLEDGE GRAPH - VERIFICATION")
    print("=" * 80 + "\n")
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Basic counts
            print("📊 BASIC STATISTICS")
            print("-" * 80)
            
            result = session.run("MATCH (e:Entity) RETURN count(e) as total")
            entity_count = result.single()['total']
            print(f"  Entities: {entity_count}")
            
            result = session.run("MATCH (d:Document) RETURN count(d) as total")
            doc_count = result.single()['total']
            print(f"  Documents: {doc_count}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
            rel_count = result.single()['total']
            print(f"  Relationships: {rel_count}")
            
            # Relationship breakdown
            print("\n📊 RELATIONSHIP BREAKDOWN")
            print("-" * 80)
            
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            
            for r in result:
                print(f"  {r['rel_type']}: {r['count']}")
            
            # Entity type distribution
            print("\n📊 ENTITY TYPE DISTRIBUTION")
            print("-" * 80)
            
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.type as type, count(e) as count
                ORDER BY count DESC
            """)
            
            for r in result:
                print(f"  {r['type']:25s} {r['count']:5d}")
            
            # Check for orphaned entities
            print("\n📊 ORPHANED ENTITY CHECK")
            print("-" * 80)
            
            result = session.run("""
                MATCH (e:Entity)
                WHERE NOT (e)-[]-()
                RETURN count(e) as orphaned
            """)
            
            orphaned = result.single()['orphaned']
            
            if orphaned == 0:
                print("  ✓ No orphaned entities found")
            else:
                print(f"  ⚠ {orphaned} orphaned entities found:")
                
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE NOT (e)-[]-()
                    RETURN e.name as name, e.type as type
                    LIMIT 10
                """)
                
                for r in result:
                    print(f"    - {r['name']} [{r['type']}]")
            
            # Check key organizations
            print("\n📊 KEY ORGANIZATIONS")
            print("-" * 80)
            
            key_orgs = [
                'ФСТЭК России',
                'Российский институт стандартизации',
                'Технический комитет по стандартизации ТК 362',
                'Стандартинформ'
            ]
            
            for org_name in key_orgs:
                result = session.run("""
                    MATCH (e:Entity {name: $name})-[r]-(target)
                    RETURN count(target) as connections
                """, name=org_name)
                
                record = result.single()
                if record and record['connections'] > 0:
                    print(f"  ✓ {org_name}: {record['connections']} connections")
                else:
                    print(f"  ✗ {org_name}: NO CONNECTIONS")
            
            # Test graph visualization query
            print("\n📊 GRAPH VISUALIZATION TEST")
            print("-" * 80)
            
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.name as name, e.type as type, COALESCE(e.relevance, 0) as relevance
                ORDER BY relevance DESC
                LIMIT 5
            """)
            
            print("  Top 5 entities by relevance:")
            for r in result:
                print(f"    - {r['name'][:50]}... [{r['type']}] (relevance: {r['relevance']})")
            
            # Summary
            print("\n" + "=" * 80)
            print("VERIFICATION SUMMARY")
            print("=" * 80)
            
            checks = [
                ("Entity count > 400", entity_count > 400),
                ("Document count > 100", doc_count > 100),
                ("Relationships > 4000", rel_count > 4000),
                ("No orphaned entities", orphaned == 0),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"  {status}: {check_name}")
                if not passed:
                    all_passed = False
            
            print("\n" + "=" * 80)
            if all_passed:
                print("✅ ALL CHECKS PASSED - Database is ready!")
            else:
                print("⚠️  SOME CHECKS FAILED - Review above for details")
            print("=" * 80)
            
            return all_passed
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    finally:
        driver.close()


if __name__ == "__main__":
    verify_database()

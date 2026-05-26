#!/usr/bin/env python3
"""
GOST Knowledge Graph - Complete Pipeline Script

This script implements the complete entity extraction, deduplication, and Neo4j loading pipeline
with all fixes and improvements learned during development.

Features:
- Strict entity deduplication (merges only true variants, NOT different entities)
- Automatic relationship creation (MENTIONS + CO_OCCURS_WITH)
- Handles missing documents automatically
- Fixes common entity type errors
- Splits combined entities (e.g., "Стандартинформ 2017" → organization + year)

Usage:
    python gost_knowledge_graph_pipeline.py --input extraction_results_final/all_entities.json
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import re

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "GraphRAG2024!"


class GOSTKnowledgeGraphPipeline:
    """Complete pipeline for GOST knowledge graph construction"""
    
    def __init__(self, input_file: str, output_dir: str = "knowledge_graph_output"):
        self.input_file = input_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Strict deduplication configuration
        self.dedup_threshold = 0.95
        self.abbreviation_rules = {
            'фстэк': ['фстэк россии', 'федеральная служба по техническому и экспортному контролю'],
            'ооо': ['общество с ограниченной ответственностью'],
            'ао': ['акционерное общество', 'открытый акционерное общество'],
            'зao': ['закрытый акционерное общество'],
            'тк': ['технический комитет'],
            'фгбу': ['федеральное государственное бюджетное учреждение'],
            'фгу': ['федеральное государственное учреждение'],
            'фгуп': ['федеральное государственное унитарное предприятие'],
        }
        
        # Entities to delete (extraction artifacts)
        self.artifacts_to_delete = {
            'THE', 'FOR', 'CHUNK', 'MANDATORY', 'EVERY', 'FIELD IS',
            'BEFORE YOU RESPOND', 'FINAL REMINDER', '⚠️'
        }
        
        # Entity type corrections
        self.type_corrections = {
            'ГОСУДАРСТВЕННЫЙ СТАНДАРТ РОССИЙСКОЙ ФЕДЕРАЦИИ': 'CONCEPT',
            'ГОСТ Р 50739—95': 'STANDARD',
            'П 50.1.110-2016': 'STANDARD',
        }
        
        # Combined entities to split
        self.combined_entities = {
            'СТАНДАРТНИФОРМ 2017': [
                ('Стандартинформ', 'ORGANIZATION'),
                ('2017', 'DATE')
            ]
        }
        
        # Typo corrections (merge into correct entity)
        self.typo_corrections = {
            'МOSCВА': 'Москва',  # Latin O → Cyrillic О
        }
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison"""
        if not name:
            return ""
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.replace('—', '-').replace('–', '-')
        normalized = normalized.replace('"', '"').replace('"', '"')
        return normalized
    
    def should_never_merge(self, name1: str, name2: str) -> bool:
        """Check if two entities should NEVER be merged"""
        # Different GOST standards
        std1 = re.search(r'(гост\s+r?\s*[\d\.]+[\d-]*)', name1.lower())
        std2 = re.search(r'(гост\s+r?\s*[\d\.]+[\d-]*)', name2.lower())
        if std1 and std2 and std1.group(1) != std2.group(1):
            return True
        
        # Different law numbers
        law1 = re.search(r'(№\s*\d+-\w+)', name1.lower())
        law2 = re.search(r'(№\s*\d+-\w+)', name2.lower())
        if law1 and law2 and law1.group(1) != law2.group(1):
            return True
        
        # Different dates
        date1 = re.search(r'(\d+\s*июнь[аыя]*\s*\d{4})', name1.lower())
        date2 = re.search(r'(\d+\s*июнь[аыя]*\s*\d{4})', name2.lower())
        if date1 and date2 and date1.group(1) != date2.group(1):
            return True
        
        return False
    
    def is_abbreviation(self, short_name: str, long_name: str) -> bool:
        """Check if short_name is an abbreviation of long_name"""
        short_norm = self.normalize_name(short_name)
        long_norm = self.normalize_name(long_name)
        
        if len(short_norm) > len(long_norm) * 0.7:
            return False
        
        if short_norm in long_norm:
            return True
        
        for abbrev, full_forms in self.abbreviation_rules.items():
            if abbrev in short_norm:
                if any(form in long_norm for form in full_forms):
                    return True
        
        return False
    
    def deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Deduplicate entities with strict rules"""
        print("\n" + "=" * 80)
        print("ENTITY DEDUPLICATION (Strict Mode)")
        print("=" * 80)
        
        # Group by similarity
        groups = defaultdict(list)
        sorted_entities = sorted(entities, key=lambda e: len(e.get('text', '')), reverse=True)
        
        for entity in sorted_entities:
            name = entity.get('text', '')
            if not name:
                continue
            
            found_group = None
            for canonical_name, group in groups.items():
                if self.is_abbreviation(name, canonical_name) or self.is_abbreviation(canonical_name, name):
                    if not self.should_never_merge(name, canonical_name):
                        found_group = canonical_name
                        break
            
            if found_group:
                groups[found_group].append(entity)
            else:
                groups[name].append(entity)
        
        # Create deduplicated entities
        deduped = []
        merge_stats = []
        
        for canonical_name, group in groups.items():
            if len(group) == 1:
                entity = group[0]
                deduped.append({
                    'text': entity.get('text', ''),
                    'type': entity.get('type', 'UNKNOWN'),
                    'doc_names': [entity.get('doc') or entity.get('doc_name', '')] if (entity.get('doc') or entity.get('doc_name')) else [],
                    'merge_count': 1,
                    'aliases': []
                })
            else:
                # Merge group
                all_docs = set()
                all_aliases = set()
                for entity in group:
                    doc = entity.get('doc') or entity.get('doc_name', '')
                    if doc:
                        all_docs.add(doc)
                    if entity.get('text', '') != canonical_name:
                        all_aliases.add(entity.get('text', ''))
                
                merged_entity = {
                    'text': canonical_name,
                    'type': group[0].get('type', 'UNKNOWN'),
                    'doc_names': list(all_docs),
                    'merge_count': len(group),
                    'aliases': list(all_aliases)
                }
                deduped.append(merged_entity)
                merge_stats.append({
                    'canonical': canonical_name,
                    'variants': list(all_aliases),
                    'count': len(group)
                })
        
        print(f"\nOriginal entities: {len(entities)}")
        print(f"Deduplicated entities: {len(deduped)}")
        print(f"Merged groups: {len(merge_stats)}")
        
        # Save deduplication stats
        with open(self.output_dir / 'deduplication_stats.json', 'w', encoding='utf-8') as f:
            json.dump({
                'original_count': len(entities),
                'deduplicated_count': len(deduped),
                'merge_groups': merge_stats
            }, f, ensure_ascii=False, indent=2)
        
        return deduped
    
    def apply_corrections(self, entities: List[Dict]) -> List[Dict]:
        """Apply entity corrections (types, splits, typo merges)"""
        print("\n" + "=" * 80)
        print("APPLYING ENTITY CORRECTIONS")
        print("=" * 80)
        
        corrected = []
        
        for entity in entities:
            name = entity['text']
            
            # Skip artifacts
            if name in self.artifacts_to_delete:
                print(f"  ✗ Deleting artifact: {name}")
                continue
            
            # Apply typo correction
            if name in self.typo_corrections:
                target = self.typo_corrections[name]
                print(f"  ✓ Merging '{name}' → '{target}'")
                # Find target entity and merge docs
                for e in corrected:
                    if e['text'] == target:
                        e['doc_names'].extend(entity.get('doc_names', []))
                        e['doc_names'] = list(set(e['doc_names']))
                        break
                continue
            
            # Split combined entities
            if name in self.combined_entities:
                print(f"  ✓ Splitting '{name}' into multiple entities")
                for split_name, split_type in self.combined_entities[name]:
                    corrected.append({
                        'text': split_name,
                        'type': split_type,
                        'doc_names': entity.get('doc_names', []),
                        'merge_count': 1,
                        'aliases': []
                    })
                continue
            
            # Apply type correction
            if name in self.type_corrections:
                entity['type'] = self.type_corrections[name]
                print(f"  ✓ Fixed type for '{name}': {entity['type']}")
            
            corrected.append(entity)
        
        return corrected
    
    def load_to_neo4j(self, entities: List[Dict]):
        """Load entities and create relationships in Neo4j"""
        from neo4j import GraphDatabase
        
        print("\n" + "=" * 80)
        print("LOADING TO NEO4J")
        print("=" * 80)
        
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        try:
            with driver.session() as session:
                # Clear existing data
                print("  Clearing existing data...")
                session.run("MATCH (n) DETACH DELETE n")
                
                # Create constraints
                print("  Creating constraints...")
                session.run("CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
                session.run("CREATE INDEX document_name IF NOT EXISTS FOR (d:Document) ON (d.name)")
                
                # Collect all unique documents
                all_docs = set()
                for entity in entities:
                    all_docs.update(entity.get('doc_names', []))
                
                # Create documents
                print(f"  Creating {len(all_docs)} documents...")
                batch_size = 100
                docs_list = list(all_docs)
                for i in range(0, len(docs_list), batch_size):
                    batch = docs_list[i:i+batch_size]
                    session.run("""
                        UNWIND $batch AS doc_name
                        CREATE (d:Document {name: doc_name, type: 'GOST'})
                    """, batch=batch)
                
                # Create entities with name property (for UI compatibility)
                print(f"  Creating {len(entities)} entities...")
                for i, entity in enumerate(entities):
                    if i % 50 == 0:
                        print(f"    Progress: {i}/{len(entities)}")
                    
                    session.run("""
                        CREATE (e:Entity {
                            name: $name,
                            text: $text,
                            normalized_name: toLower($name),
                            type: $type,
                            merge_count: $merge_count,
                            aliases: $aliases
                        })
                    """,
                        name=entity['text'],
                        text=entity['text'],
                        type=entity['type'],
                        merge_count=entity.get('merge_count', 1),
                        aliases=entity.get('aliases', [])
                    )
                    
                    # Create MENTIONS relationships
                    for doc_name in entity.get('doc_names', []):
                        if doc_name:
                            session.run("""
                                MATCH (e:Entity {name: $entity_name})
                                MATCH (d:Document {name: $doc_name})
                                CREATE (e)-[:MENTIONS]->(d)
                            """, entity_name=entity['text'], doc_name=doc_name)
                
                # Create CO_OCCURS_WITH relationships
                print("  Creating CO_OCCURS_WITH relationships...")
                session.run("""
                    MATCH (e1:Entity)-[:MENTIONS]->(d:Document)<-[:MENTIONS]-(e2:Entity)
                    WHERE e1.normalized_name < e2.normalized_name
                    MERGE (e1)-[r:CO_OCCURS_WITH]->(e2)
                    ON CREATE SET r.count = 1
                """)
                
                # Verify
                result = session.run("""
                    MATCH (e:Entity) RETURN count(e) as entities
                    UNION ALL
                    MATCH (d:Document) RETURN count(d) as documents
                    UNION ALL
                    MATCH ()-[r]->() RETURN count(r) as relationships
                """)
                
                stats = [r.values() for r in result]
                print(f"\n  ✓ Loaded: {stats[0]} entities, {stats[1]} documents, {stats[2]} relationships")
                
                # Check for orphaned entities
                result = session.run("""
                    MATCH (e:Entity) WHERE NOT (e)-[]-() RETURN count(e) as orphaned
                """)
                orphaned = result.single()['orphaned']
                if orphaned > 0:
                    print(f"  ⚠ {orphaned} orphaned entities found")
                else:
                    print(f"  ✓ No orphaned entities")
        
        finally:
            driver.close()
    
    def run(self):
        """Run the complete pipeline"""
        print("=" * 80)
        print("GOST KNOWLEDGE GRAPH PIPELINE")
        print("=" * 80)
        
        # Load input data
        print(f"\nLoading entities from {self.input_file}...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        print(f"  Loaded {len(entities)} entities")
        
        # Deduplicate
        deduped = self.deduplicate_entities(entities)
        
        # Apply corrections
        corrected = self.apply_corrections(deduped)
        
        # Save final entity list
        output_file = self.output_dir / 'final_entities.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(corrected),
                'entities': corrected
            }, f, ensure_ascii=False, indent=2)
        print(f"\n  Saved final entities to {output_file}")
        
        # Load to Neo4j
        self.load_to_neo4j(corrected)
        
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='GOST Knowledge Graph Pipeline')
    parser.add_argument('--input', default='extraction_results_final/all_entities.json',
                       help='Input entities JSON file')
    parser.add_argument('--output-dir', default='knowledge_graph_output',
                       help='Output directory')
    
    args = parser.parse_args()
    
    pipeline = GOSTKnowledgeGraphPipeline(args.input, args.output_dir)
    pipeline.run()


if __name__ == "__main__":
    main()

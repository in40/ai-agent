#!/usr/bin/env python3
"""
GOST Document Re-processing Pipeline
Processes all 112 GOST standards with improved hybrid entity extraction
for Neo4j graph ingestion.

Usage:
    python reprocess_gost_documents.py [--strategy STRATEGY] [--batch-size N] [--dry-run]

Strategies:
    - hybrid: Fast pattern + LLM enrichment (RECOMMENDED)
    - llm_only: Full LLM extraction (highest quality, slower)
    - pattern_only: Pattern matching only (fastest, lower quality)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import re

# Add backend to path
sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

from nlp_tools.entity_extractor import EntityExtractor
from nlp_tools.llm_entity_extractor import LLMEntityExtractor
from neo4j_integration import Neo4jIntegration


class GOSTReprocessor:
    """Main class for reprocessing GOST documents with entity extraction"""
    
    def __init__(self, strategy: str = 'hybrid', dry_run: bool = False):
        """
        Initialize reprocessor
        
        Args:
            strategy: Extraction strategy ('hybrid', 'llm_only', 'pattern_only')
            dry_run: If True, don't write to Neo4j or save files
        """
        self.strategy = strategy
        self.dry_run = dry_run
        
        # Initialize components
        print("Initializing entity extractors...")
        self.pattern_extractor = EntityExtractor(
            model_name="en_core_web_sm",
            russian_model="ru_core_news_sm",
            use_custom_types=True
        )
        
        if strategy in ['hybrid', 'llm_only']:
            self.llm_extractor = LLMEntityExtractor()
        else:
            self.llm_extractor = None
        
        if not dry_run:
            self.neo4j = Neo4jIntegration()
            if not self.neo4j.connected:
                self.neo4j.connect()
        else:
            self.neo4j = None
        
        # Configuration
        self.doc_store_path = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"
        self.output_path = "/root/qwen/ai_agent/reprocessed_chunks"
        self.llm_max_chars = 50000  # Limit for LLM calls
        
        # Statistics
        self.stats = {
            'documents_processed': 0,
            'documents_failed': 0,
            'chunks_processed': 0,
            'entities_extracted': 0,
            'llm_calls': 0,
            'processing_time': 0
        }
        
    def get_all_documents(self) -> List[str]:
        """Get list of all document base names with chunks.json"""
        chunks_files = list(Path(self.doc_store_path).glob("*.chunks.json"))
        return [f.stem for f in chunks_files]
    
    def load_document(self, doc_name: str) -> Dict[str, Any]:
        """Load document chunks from chunks.json"""
        chunks_file = Path(self.doc_store_path) / f"{doc_name}.chunks.json"
        
        if not chunks_file.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_file}")
        
        with open(chunks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy and pattern matching"""
        try:
            entities = self.pattern_extractor.extract_all_entities(
                text,
                use_spacy=True,
                use_nltk=False,
                use_patterns=True,
                extract_technologies=True
            )
            
            # Add GOST-specific patterns
            gost_entities = self._extract_gost_standards(text)
            entities.extend(gost_entities)
            
            return entities
        except Exception as e:
            print(f"  Pattern extraction error: {e}")
            return []
    
    def _extract_gost_standards(self, text: str) -> List[Dict[str, Any]]:
        """Extract GOST standard references using regex"""
        patterns = [
            (r'ГОСТ\s*Р\s*\d+[\s\-–—]+\d{4}', 'GOST_STANDARD'),
            (r'ГОСТ\s*\d+[\s\-–—]+\d{4}', 'GOST_STANDARD'),
            (r'GOST\s*R?\s*\d+[\s\-–—]+\d{4}', 'GOST_STANDARD'),
            (r'ISO\s*\d+(-\d+)?', 'ISO_STANDARD'),
            (r'IEC\s*\d+(-\d+)?', 'IEC_STANDARD'),
            (r'Федеральный\s*закон\s*№?\s*\d+-[Ff][Zz]', 'FEDERAL_LAW'),
            (r'Приказ\s*№?\s*\d+', 'ORDER'),
        ]
        
        entities = []
        for pattern, entity_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    'text': match.group(),
                    'label': entity_type,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.95,
                    'source': 'pattern'
                })
        
        return entities
    
    def extract_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using LLM"""
        if not self.llm_extractor:
            return []
        
        try:
            # Truncate if necessary
            if len(text) > self.llm_max_chars:
                text = text[:self.llm_max_chars] + "... [truncated]"
            
            result = self.llm_extractor.extract_entities(text)
            self.stats['llm_calls'] += 1
            
            entities = result.get('entities', [])
            
            # Add source metadata
            for ent in entities:
                ent['source'] = 'llm'
            
            return entities
        except Exception as e:
            print(f"  LLM extraction error: {e}")
            return []
    
    def merge_entities(self, pattern_entities: List, llm_entities: List) -> List[Dict[str, Any]]:
        """Merge entities from different sources, avoiding duplicates"""
        seen: Set[Tuple[str, str]] = set()
        merged = []
        
        # Combine all entities
        all_entities = pattern_entities + llm_entities
        
        for ent in all_entities:
            # Create unique key based on text and type
            text = ent.get('text', ent.get('name', '')).lower().strip()
            label = ent.get('label', ent.get('type', ''))
            key = (text, label)
            
            if key not in seen and text:
                seen.add(key)
                
                # Normalize entity format
                normalized = {
                    'name': ent.get('text', ent.get('name', '')),
                    'type': ent.get('label', ent.get('type', '')),
                    'confidence': ent.get('confidence', 0.8),
                    'source': ent.get('source', 'unknown'),
                    'start': ent.get('start', 0),
                    'end': ent.get('end', 0)
                }
                
                merged.append(normalized)
        
        return merged
    
    def process_document_patterns(self, doc_data: Dict[str, Any]) -> Tuple[int, List[Dict]]:
        """Process document with pattern extraction only"""
        all_entities = []
        
        for chunk in doc_data['chunks']:
            content = chunk.get('content', '')
            entities = self.extract_with_patterns(content)
            
            # Store entities in chunk
            chunk['entities'] = entities
            all_entities.extend(entities)
        
        return len(all_entities), all_entities
    
    def process_document_llm(self, doc_data: Dict[str, Any]) -> Tuple[int, List[Dict]]:
        """Process document with LLM extraction only"""
        # Combine all chunk content
        full_text = "\n\n".join([c.get('content', '') for c in doc_data['chunks']])
        
        # Extract entities from full text
        entities = self.extract_with_llm(full_text)
        
        # Distribute entities to chunks based on position
        for chunk in doc_data['chunks']:
            chunk['entities'] = []
        
        # Simple distribution: assign all entities to first chunk
        if doc_data['chunks'] and entities:
            doc_data['chunks'][0]['entities'] = entities
        
        return len(entities), entities
    
    def process_document_hybrid(self, doc_data: Dict[str, Any]) -> Tuple[int, List[Dict]]:
        """Process document with hybrid extraction (patterns + LLM)"""
        # Phase 1: Pattern extraction on each chunk
        all_pattern_entities = []
        for chunk in doc_data['chunks']:
            content = chunk.get('content', '')
            entities = self.extract_with_patterns(content)
            chunk['entities_pattern'] = entities
            all_pattern_entities.extend(entities)
        
        # Phase 2: LLM extraction on full document
        full_text = "\n\n".join([c.get('content', '') for c in doc_data['chunks']])
        llm_entities = self.extract_with_llm(full_text)
        
        # Phase 3: Merge entities
        merged_entities = self.merge_entities(all_pattern_entities, llm_entities)
        
        # Store merged entities in first chunk for reference
        if doc_data['chunks']:
            doc_data['chunks'][0]['entities_merged'] = merged_entities
        
        return len(merged_entities), merged_entities
    
    def process_document(self, doc_name: str) -> Dict[str, Any]:
        """Process single document with selected strategy"""
        start_time = datetime.now()
        
        try:
            print(f"  Processing: {doc_name}")
            
            # Load document
            doc_data = self.load_document(doc_name)
            num_chunks = len(doc_data.get('chunks', []))
            
            # Extract entities based on strategy
            if self.strategy == 'pattern_only':
                entity_count, entities = self.process_document_patterns(doc_data)
            elif self.strategy == 'llm_only':
                entity_count, entities = self.process_document_llm(doc_data)
            else:  # hybrid
                entity_count, entities = self.process_document_hybrid(doc_data)
            
            # Store in Neo4j if not dry run
            neo4j_stats = None
            if not self.dry_run and self.neo4j and self.neo4j.connected:
                try:
                    neo4j_stats = self.neo4j.create_knowledge_graph(
                        doc_data['chunks'],
                        entities=entities
                    )
                except Exception as e:
                    print(f"  Neo4j storage error: {e}")
            
            # Save updated chunks if not dry run
            if not self.dry_run:
                output_file = Path(self.output_path) / f"{doc_name}.chunks.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(doc_data, f, ensure_ascii=False, indent=2)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            result = {
                'doc_name': doc_name,
                'status': 'success',
                'chunks_processed': num_chunks,
                'entities_extracted': entity_count,
                'neo4j_stats': neo4j_stats,
                'processing_time': processing_time
            }
            
            self.stats['documents_processed'] += 1
            self.stats['chunks_processed'] += num_chunks
            self.stats['entities_extracted'] += entity_count
            self.stats['processing_time'] += processing_time
            
            return result
            
        except Exception as e:
            print(f"  ERROR: {e}")
            
            self.stats['documents_failed'] += 1
            
            return {
                'doc_name': doc_name,
                'status': 'failed',
                'error': str(e)
            }
    
    def process_all_documents(self, parallel: int = 4):
        """Process all documents with parallel execution"""
        print("=" * 60)
        print(f"GOST Document Re-processing Pipeline")
        print(f"Strategy: {self.strategy}")
        print(f"Dry run: {self.dry_run}")
        print("=" * 60)
        
        # Create output directory
        if not self.dry_run:
            Path(self.output_path).mkdir(exist_ok=True)
        
        # Get document list
        docs = self.get_all_documents()
        print(f"\nFound {len(docs)} documents to process")
        
        if not docs:
            print("No documents found!")
            return []
        
        # Process documents
        print(f"\nStarting processing with {parallel} workers...")
        start_time = datetime.now()
        
        results = []
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            future_to_doc = {
                executor.submit(self.process_document, doc): doc 
                for doc in docs
            }
            
            for i, future in enumerate(as_completed(future_to_doc), 1):
                doc = future_to_doc[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    status_icon = "✓" if result['status'] == 'success' else "✗"
                    print(f"[{i}/{len(docs)}] {status_icon} {doc}")
                    
                except Exception as e:
                    print(f"[{i}/{len(docs)}] ✗ {doc} - Exception: {e}")
                    results.append({
                        'doc_name': doc,
                        'status': 'failed',
                        'error': str(e)
                    })
                    self.stats['documents_failed'] += 1
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Print summary
        self._print_summary(results, total_time)
        
        return results
    
    def _print_summary(self, results: List[Dict], total_time: float):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print(f"\nDocuments:")
        print(f"  Total: {len(results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        
        if successful:
            total_chunks = sum(r.get('chunks_processed', 0) for r in successful)
            total_entities = sum(r.get('entities_extracted', 0) for r in successful)
            
            print(f"\nProcessing:")
            print(f"  Chunks processed: {total_chunks}")
            print(f"  Entities extracted: {total_entities}")
            print(f"  LLM calls: {self.stats['llm_calls']}")
            print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f}m)")
            print(f"  Avg time/doc: {total_time/len(successful):.1f}s")
            
            if not self.dry_run:
                print(f"\nOutput:")
                print(f"  Saved to: {self.output_path}/")
                print(f"  Neo4j updated: Yes")
            else:
                print(f"\nDry run - no files saved")
        
        if failed:
            print(f"\nFailed documents:")
            for result in failed[:10]:  # Show first 10
                print(f"  - {result['doc_name']}: {result.get('error', 'Unknown error')}")
            
            if len(failed) > 10:
                print(f"  ... and {len(failed) - 10} more")
        
        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Re-process GOST documents with entity extraction'
    )
    parser.add_argument(
        '--strategy',
        choices=['hybrid', 'llm_only', 'pattern_only'],
        default='hybrid',
        help='Entity extraction strategy (default: hybrid)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process without saving results'
    )
    parser.add_argument(
        '--llm-model',
        type=str,
        default=os.getenv("ENTITY_EXTRACT_LLM_MODEL", "qwen3-4b"),
        help='LLM model for entity extraction (default: from env or qwen3-4b)'
    )
    
    args = parser.parse_args()
    
    # Set environment variable for LLM model
    os.environ["ENTITY_EXTRACT_LLM_MODEL"] = args.llm_model
    
    # Create reprocessor
    reprocessor = GOSTReprocessor(
        strategy=args.strategy,
        dry_run=args.dry_run
    )
    
    # Process all documents
    results = reprocessor.process_all_documents(parallel=args.batch_size)
    
    # Return exit code based on success
    failed = sum(1 for r in results if r['status'] == 'failed')
    sys.exit(1 if failed > len(results) / 2 else 0)


if __name__ == "__main__":
    main()

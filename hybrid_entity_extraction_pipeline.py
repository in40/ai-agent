#!/usr/bin/env python3
"""
GOST Document Hybrid Entity Extraction Pipeline

Process all 112 GOST documents with:
1. Pattern/spaCy extraction (fast, comprehensive)
2. LLM validation (quality filter)
3. Chunked LLM extraction (deep analysis)
4. Smart merge with deduplication

Results stored to files for analysis (NOT loaded into Neo4j yet)

Usage:
    python hybrid_entity_extraction_pipeline.py [--validate-with-llm] [--chunked-extraction] [--output-dir OUTPUT_DIR]
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Set, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

# Configuration
DOC_STORE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"
OUTPUT_DIR = "/root/qwen/ai_agent/extraction_results"
LM_STUDIO_URL = "http://fedora:8081/v1"
LM_MODEL = "Qwen3.5-2B-UD-Q4_K_XL.gguf"

# Processing flags
DO_PATTERN_EXTRACTION = True
DO_LLM_VALIDATION = True
DO_CHUNKED_LLM_EXTRACTION = True


class HybridEntityExtractor:
    """Hybrid entity extraction with pattern + LLM validation"""
    
    def __init__(self):
        # Import spaCy extractor
        from nlp_tools.entity_extractor import EntityExtractor
        self.pattern_extractor = EntityExtractor(
            model_name="en_core_web_sm",
            russian_model="ru_core_news_sm",
            use_custom_types=True
        )
        
        # Statistics
        self.stats = {
            'documents_processed': 0,
            'chunks_processed': 0,
            'pattern_entities_extracted': 0,
            'llm_validated_entities': 0,
            'chunked_llm_entities': 0,
            'final_unique_entities': 0,
            'duplicates_removed': 0,
            'processing_time': 0
        }
    
    def get_all_documents(self) -> List[str]:
        """Get list of all document base names with chunks.json"""
        chunks_files = list(Path(DOC_STORE_PATH).glob("*.chunks.json"))
        # Remove .chunks suffix from stem (files are named like: doc.chunks.json)
        return [f.stem.replace('.chunks', '') for f in chunks_files]
    
    def load_document(self, doc_name: str) -> Dict[str, Any]:
        """Load document chunks from chunks.json"""
        # Files are named like: doc_name.chunks.json
        chunks_file = Path(DOC_STORE_PATH) / f"{doc_name}.chunks.json"
        
        if not chunks_file.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_file}")
        
        with open(chunks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def pattern_extraction(self, doc_data: Dict[str, Any]) -> Tuple[int, List[Dict]]:
        """Extract entities using pattern/spaCy method"""
        all_entities = []
        
        for chunk in doc_data['chunks']:
            content = chunk.get('content', '')
            
            # Extract with patterns
            entities = self.pattern_extractor.extract_all_entities(
                content,
                use_spacy=True,
                use_patterns=True,
                extract_technologies=True
            )
            
            # Add chunk metadata
            for ent in entities:
                ent['source'] = 'pattern'
                ent['chunk_id'] = chunk.get('chunk_id', 0)
            
            all_entities.extend(entities)
        
        return len(all_entities), all_entities
    
    def llm_validate_entities(self, candidate_entities: List[Dict], doc_text: str) -> List[Dict]:
        """Validate pattern-extracted entities with LLM"""
        if not candidate_entities:
            return []
        
        # Sample entities to validate (max 50 to avoid token limits)
        sample_entities = candidate_entities[:50]
        
        prompt = f"""Verify these candidate entities from Russian technical text.
Return JSON ONLY: {{"verified": [{{"text": "...", "valid": true/false, "reason": "..."}}]}}

Candidate entities (from pattern extraction):
{json.dumps(sample_entities, ensure_ascii=False, indent=2)}

Text context (first 3000 chars):
{doc_text[:3000]}"""

        try:
            response = requests.post(
                f"{LM_STUDIO_URL}/chat/completions",
                json={
                    "model": LM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1500
                },
                timeout=120
            )
            
            result = response.json()
            llm_output = result["choices"][0]["message"]["content"]
            
            # Parse JSON
            import re
            json_match = re.search(r'\{[\s\S]*"verified"[\s\S]*\}', llm_output)
            if json_match:
                data = json.loads(json_match.group(0))
                verified_list = data.get("verified", [])
                
                # Create set of valid entity texts
                valid_texts = set(
                    v['text'] for v in verified_list 
                    if v.get('valid', False)
                )
                
                # Filter original entities
                validated_entities = [
                    ent for ent in sample_entities 
                    if ent.get('text') in valid_texts
                ]
                
                # Add validation metadata
                for ent in validated_entities:
                    ent['llm_validated'] = True
                
                return validated_entities
            else:
                print(f"  Could not parse LLM validation response")
                return candidate_entities[:10]  # Fallback: keep some entities
                
        except Exception as e:
            print(f"  LLM validation error: {e}")
            return candidate_entities[:10]  # Fallback
    
    def chunked_llm_extraction(self, doc_data: Dict[str, Any]) -> Tuple[int, List[Dict]]:
        """Extract entities from each chunk using LLM"""
        all_entities = []
        
        for chunk in doc_data['chunks']:
            content = chunk.get('content', '')
            chunk_id = chunk.get('chunk_id', 0)
            
            # Skip very short chunks
            if len(content) < 100:
                continue
            
            # Extract entities from this chunk
            prompt = f"""Extract entities from this Russian technical text. Return JSON ONLY:
{{"entities": [{{"text": "...", "type": "STANDARD|ORGANIZATION|LOCATION|DATE|CONCEPT|TECHNICAL_TERM"}}]}}

Text: {content[:2000]}"""
            
            try:
                response = requests.post(
                    f"{LM_STUDIO_URL}/chat/completions",
                    json={
                        "model": LM_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 800
                    },
                    timeout=90
                )
                
                result = response.json()
                llm_output = result["choices"][0]["message"]["content"]
                
                # Parse JSON
                import re
                json_match = re.search(r'\{[\s\S]*"entities"[\s\S]*\}', llm_output)
                if json_match:
                    data = json.loads(json_match.group(0))
                    entities = data.get("entities", [])
                    
                    # Add chunk metadata
                    for ent in entities:
                        ent['source'] = 'llm_chunked'
                        ent['chunk_id'] = chunk_id
                    
                    all_entities.extend(entities)
                    
            except Exception as e:
                print(f"    Chunk {chunk_id} extraction error: {e}")
                continue
        
        return len(all_entities), all_entities
    
    def smart_merge(self, pattern_entities: List[Dict], 
                   validated_entities: List[Dict],
                   chunked_llm_entities: List[Dict]) -> Tuple[int, List[Dict]]:
        """Smart merge with deduplication and priority rules"""
        
        # Combine all entities
        all_entities = pattern_entities + validated_entities + chunked_llm_entities
        
        # Deduplication with priority
        # Priority: LLM > Validated > Pattern
        seen = {}  # key = (normalized_text, type)
        
        for ent in all_entities:
            text = normalize_entity_text(ent.get('text', ''))
            etype = ent.get('type', ent.get('label', 'UNKNOWN'))
            key = (text, etype)
            
            if key not in seen:
                # First occurrence - store it
                seen[key] = {
                    'entity': ent,
                    'source_priority': get_source_priority(ent.get('source', 'pattern'))
                }
            else:
                # Already exists - check if new one has higher priority
                existing_priority = seen[key]['source_priority']
                new_priority = get_source_priority(ent.get('source', 'pattern'))
                
                if new_priority > existing_priority:
                    seen[key] = {
                        'entity': ent,
                        'source_priority': new_priority
                    }
        
        # Extract merged entities
        merged_entities = [item['entity'] for item in seen.values()]
        
        return len(merged_entities), merged_entities
    
    def process_document(self, doc_name: str) -> Dict[str, Any]:
        """Process single document with hybrid extraction"""
        import time
        start_time = time.time()
        
        print(f"  Processing: {doc_name}")
        
        try:
            # Load document
            doc_data = self.load_document(doc_name)
            num_chunks = len(doc_data.get('chunks', []))
            
            # Combine all chunk text for validation context
            full_text = "\n\n".join([c.get('content', '') for c in doc_data['chunks']])
            
            # STEP 1: Pattern extraction
            pattern_count, pattern_entities = self.pattern_extraction(doc_data)
            print(f"    Pattern extraction: {pattern_count} entities")
            
            # STEP 2: LLM validation (optional)
            validated_entities = []
            if DO_LLM_VALIDATION and pattern_entities:
                print(f"    Validating with LLM...")
                validated_entities = self.llm_validate_entities(pattern_entities, full_text)
                print(f"    Validated: {len(validated_entities)} entities")
            
            # STEP 3: Chunked LLM extraction (optional)
            chunked_count, chunked_entities = 0, []
            if DO_CHUNKED_LLM_EXTRACTION:
                print(f"    Chunked LLM extraction...")
                chunked_count, chunked_entities = self.chunked_llm_extraction(doc_data)
                print(f"    Chunked LLM: {chunked_count} entities")
            
            # STEP 4: Smart merge
            merged_count, merged_entities = self.smart_merge(
                pattern_entities, 
                validated_entities, 
                chunked_entities
            )
            print(f"    Merged (unique): {merged_count} entities")
            
            processing_time = time.time() - start_time
            
            # Prepare result
            result = {
                'doc_name': doc_name,
                'status': 'success',
                'chunks_processed': num_chunks,
                'pattern_entities': pattern_count,
                'validated_entities': len(validated_entities),
                'chunked_llm_entities': chunked_count,
                'final_unique_entities': merged_count,
                'entities': merged_entities,
                'processing_time': processing_time
            }
            
            # Update statistics
            self.stats['documents_processed'] += 1
            self.stats['chunks_processed'] += num_chunks
            self.stats['pattern_entities_extracted'] += pattern_count
            self.stats['llm_validated_entities'] += len(validated_entities)
            self.stats['chunked_llm_entities'] += chunked_count
            self.stats['final_unique_entities'] += merged_count
            self.stats['processing_time'] += processing_time
            
            return result
            
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'doc_name': doc_name,
                'status': 'failed',
                'error': str(e)
            }
    
    def process_all_documents(self, parallel: int = 1):
        """Process all documents"""
        print("=" * 80)
        print("HYBRID ENTITY EXTRACTION PIPELINE")
        print(f"Pattern extraction: {DO_PATTERN_EXTRACTION}")
        print(f"LLM validation: {DO_LLM_VALIDATION}")
        print(f"Chunked LLM extraction: {DO_CHUNKED_LLM_EXTRACTION}")
        print("=" * 80)
        
        # Create output directory
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        
        # Get document list
        docs = self.get_all_documents()
        print(f"\nFound {len(docs)} documents to process")
        
        if not docs:
            print("No documents found!")
            return []
        
        # Process documents (sequential for now to control LLM rate)
        print(f"\nStarting processing...")
        import time
        start_time = time.time()
        
        results = []
        for i, doc_name in enumerate(docs, 1):
            print(f"\n[{i}/{len(docs)}]")
            result = self.process_document(doc_name)
            results.append(result)
            
            # Save individual result
            if result['status'] == 'success':
                output_file = Path(OUTPUT_DIR) / f"{doc_name}_entities.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'doc_name': doc_name,
                        'entities': result.get('entities', []),
                        'statistics': {
                            'pattern_count': result.get('pattern_entities', 0),
                            'validated_count': result.get('validated_entities', 0),
                            'chunked_llm_count': result.get('chunked_llm_entities', 0),
                            'final_unique': result.get('final_unique_entities', 0)
                        }
                    }, f, ensure_ascii=False, indent=2)
        
        total_time = time.time() - start_time
        
        # Print summary
        self._print_summary(results, total_time)
        
        # Save combined results
        self._save_combined_results(results)
        
        return results
    
    def _print_summary(self, results: List[Dict], total_time: float):
        """Print processing summary"""
        print("\n" + "=" * 80)
        print("PROCESSING SUMMARY")
        print("=" * 80)
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        print(f"\nDocuments:")
        print(f"  Total: {len(results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        
        if successful:
            total_pattern = sum(r.get('pattern_entities', 0) for r in successful)
            total_validated = sum(r.get('validated_entities', 0) for r in successful)
            total_chunked = sum(r.get('chunked_llm_entities', 0) for r in successful)
            total_unique = sum(r.get('final_unique_entities', 0) for r in successful)
            
            print(f"\nExtraction Statistics:")
            print(f"  Pattern entities: {total_pattern}")
            print(f"  LLM-validated: {total_validated}")
            print(f"  Chunked LLM: {total_chunked}")
            print(f"  Final unique (merged): {total_unique}")
            
            if total_pattern > 0:
                print(f"\nValidation Rate:")
                print(f"  Pattern → Validated: {(total_validated/total_pattern)*100:.1f}%")
                print(f"  Total duplicates removed: {total_pattern + total_chunked - total_unique}")
            
            print(f"\nPerformance:")
            print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f}m)")
            print(f"  Avg time/doc: {total_time/len(successful):.1f}s")
        
        if failed:
            print(f"\nFailed documents:")
            for result in failed[:5]:
                print(f"  - {result['doc_name']}: {result.get('error', 'Unknown')}")
        
        print(f"\nOutput saved to: {OUTPUT_DIR}/")
        print("=" * 80)
    
    def _save_combined_results(self, results: List[Dict]):
        """Save combined results for analysis"""
        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'pattern_extraction': DO_PATTERN_EXTRACTION,
                'llm_validation': DO_LLM_VALIDATION,
                'chunked_llm_extraction': DO_CHUNKED_LLM_EXTRACTION
            },
            'statistics': self.stats,
            'documents': [
                {
                    'doc_name': r['doc_name'],
                    'status': r['status'],
                    'pattern_entities': r.get('pattern_entities', 0),
                    'validated_entities': r.get('validated_entities', 0),
                    'chunked_llm_entities': r.get('chunked_llm_entities', 0),
                    'final_unique': r.get('final_unique_entities', 0)
                }
                for r in results
            ]
        }
        
        summary_file = Path(OUTPUT_DIR) / "extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Save all entities combined
        all_entities = []
        for r in results:
            if r['status'] == 'success':
                for ent in r.get('entities', []):
                    ent['doc_name'] = r['doc_name']
                all_entities.extend(r.get('entities', []))
        
        entities_file = Path(OUTPUT_DIR) / "all_entities.json"
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_entities': len(all_entities),
                'entities': all_entities
            }, f, ensure_ascii=False, indent=2)


def normalize_entity_text(text: str) -> str:
    """Normalize entity text for deduplication"""
    if not text:
        return ""
    # Lowercase and strip
    normalized = text.lower().strip()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def get_source_priority(source: str) -> int:
    """Get priority for entity source (higher = better)"""
    priorities = {
        'llm_chunked': 3,      # Highest - deep LLM analysis
        'llm_validated': 2,    # Medium - LLM validated patterns
        'pattern': 1           # Lowest - raw pattern extraction
    }
    return priorities.get(source, 0)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Hybrid entity extraction pipeline for GOST documents'
    )
    parser.add_argument(
        '--no-llm-validation',
        action='store_true',
        help='Skip LLM validation step'
    )
    parser.add_argument(
        '--no-chunked-extraction',
        action='store_true',
        help='Skip chunked LLM extraction step'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for results'
    )
    
    args = parser.parse_args()
    
    # Update flags
    global DO_LLM_VALIDATION, DO_CHUNKED_LLM_EXTRACTION, OUTPUT_DIR
    DO_LLM_VALIDATION = not args.no_llm_validation
    DO_CHUNKED_LLM_EXTRACTION = not args.no_chunked_extraction
    if args.output_dir:
        OUTPUT_DIR = args.output_dir
    
    # Create extractor
    extractor = HybridEntityExtractor()
    
    # Process all documents
    results = extractor.process_all_documents()
    
    # Return exit code
    failed = sum(1 for r in results if r['status'] == 'failed')
    sys.exit(1 if failed > len(results) / 2 else 0)


if __name__ == "__main__":
    main()

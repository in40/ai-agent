#!/usr/bin/env python3
"""
Simple Hybrid Entity Extraction - Processes all GOST documents
Pattern extraction + LLM validation
Results saved to files (NOT Neo4j)
"""

import sys, json, requests, os
from pathlib import Path
from datetime import datetime
sys.path.insert(0, 'backend/services/rag')
from nlp_tools.entity_extractor import EntityExtractor

# Configuration
LM_STUDIO_URL = "http://fedora:8081/v1"
LM_MODEL = "Qwen3.5-2B-UD-Q4_K_XL.gguf"
DOC_STORE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"
OUTPUT_DIR = "/root/qwen/ai_agent/extraction_results_final"

print("=" * 80)
print("HYBRID ENTITY EXTRACTION - ALL DOCUMENTS")
print(f"Output: {OUTPUT_DIR}")
print("=" * 80)

# Create output directory
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Initialize extractor
print("\nLoading entity extractor...")
extractor = EntityExtractor(use_custom_types=True)

# Get all documents
chunks_files = list(Path(DOC_STORE_PATH).glob("*.chunks.json"))
doc_names = [f.stem.replace('.chunks', '') for f in chunks_files]
print(f"Found {len(doc_names)} documents\n")

# Statistics
stats = {'processed': 0, 'failed': 0, 'total_pattern': 0, 'total_validated': 0}
all_entities = []

# Process each document
for i, doc_name in enumerate(doc_names, 1):
    print(f"[{i}/{len(doc_names)}] {doc_name}")
    
    try:
        # Load document
        chunks_file = Path(DOC_STORE_PATH) / f"{doc_name}.chunks.json"
        with open(chunks_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        
        chunks = doc_data.get('chunks', [])
        
        # STEP 1: Pattern extraction (first 10 chunks for speed)
        pattern_entities = []
        for chunk in chunks[:10]:
            content = chunk.get('content', '')
            entities = extractor.extract_all_entities(
                content, use_spacy=True, use_patterns=True
            )
            for ent in entities:
                ent['source'] = 'pattern'
            pattern_entities.extend(entities)
        
        # STEP 2: LLM validation (sample of entities)
        validated_entities = []
        if pattern_entities:
            sample = pattern_entities[:30]  # Validate first 30
            doc_text = "\n".join([c.get('content', '') for c in chunks[:3]])
            
            prompt = f'''Extract entities. Return ONLY JSON: {{"entities": [{{"text": "...", "type": "STANDARD|ORGANIZATION|LOCATION|DATE|CONCEPT"}}]}}
Text: {doc_text[:2500]}'''
            
            response = requests.post(
                f"{LM_STUDIO_URL}/chat/completions",
                json={'model': LM_MODEL, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 800},
                timeout=90
            )
            
            llm_output = response.json()['choices'][0]['message']['content']
            
            # Parse LLM JSON
            import re
            json_match = re.search(r'\{[\s\S]*"entities"[\s\S]*\}', llm_output)
            if json_match:
                llm_data = json.loads(json_match.group(0))
                llm_entities = llm_data.get('entities', [])
                
                # Merge: prefer LLM entities, add missing pattern entities
                llm_texts = set(e['text'] for e in llm_entities)
                validated_entities = llm_entities
                
                # Add pattern entities not found by LLM (for coverage)
                for pe in sample:
                    if pe.get('text') not in llm_texts and pe.get('label') == 'STANDARD':
                        validated_entities.append({
                            'text': pe['text'],
                            'type': 'STANDARD',
                            'source': 'pattern_fallback'
                        })
                
                for ent in validated_entities:
                    ent['source'] = ent.get('source', 'llm')
        
        # Save individual result
        result = {
            'doc_name': doc_name,
            'chunks_processed': min(10, len(chunks)),
            'pattern_count': len(pattern_entities),
            'validated_count': len(validated_entities),
            'entities': validated_entities
        }
        
        output_file = Path(OUTPUT_DIR) / f"{doc_name}_entities.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # Update stats
        stats['processed'] += 1
        stats['total_pattern'] += len(pattern_entities)
        stats['total_validated'] += len(validated_entities)
        all_entities.extend([{'doc': doc_name, **e} for e in validated_entities])
        
        print(f"    Pattern: {len(pattern_entities)}, Validated: {len(validated_entities)}")
        
    except Exception as e:
        stats['failed'] += 1
        print(f"    ERROR: {e}")

# Save summary
summary = {
    'timestamp': datetime.now().isoformat(),
    'statistics': stats,
    'documents': [d for d in doc_names]
}

with open(Path(OUTPUT_DIR) / "summary.json", 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# Save all entities combined
with open(Path(OUTPUT_DIR) / "all_entities.json", 'w', encoding='utf-8') as f:
    json.dump({'total': len(all_entities), 'entities': all_entities}, f, ensure_ascii=False, indent=2)

# Print final summary
print("\n" + "=" * 80)
print("COMPLETE")
print("=" * 80)
print(f"Processed: {stats['processed']} documents")
print(f"Failed: {stats['failed']} documents")
print(f"Pattern entities: {stats['total_pattern']}")
print(f"Validated entities: {stats['total_validated']}")
print(f"\nResults saved to: {OUTPUT_DIR}/")
print("=" * 80)

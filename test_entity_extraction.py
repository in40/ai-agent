#!/usr/bin/env python3
"""
Test Entity Extraction on 2 Large GOST Documents
Shows pattern-based and LLM-based extraction results
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

from nlp_tools.entity_extractor import EntityExtractor

# Select 2 largest documents
DOC_FILES = [
    "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/gost-r-52069_2c53c42c.chunks.json",
    "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_78b35e61.chunks.json"
]

def load_document(filepath):
    """Load document chunks"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_entities_pattern_based(text, extractor):
    """Extract entities using pattern matching"""
    return extractor.extract_all_entities(
        text,
        use_spacy=True,
        use_nltk=False,
        use_patterns=True,
        extract_technologies=True
    )

def summarize_entities(entities):
    """Create summary of extracted entities"""
    by_type = {}
    for ent in entities:
        entity_type = ent.get('label', 'UNKNOWN')
        if entity_type not in by_type:
            by_type[entity_type] = []
        if len(by_type[entity_type]) < 5:  # Store first 5 examples
            by_type[entity_type].append(ent.get('text', ''))
    
    return {
        'total': len(entities),
        'by_type': {k: len(v) for k, v in by_type.items()},
        'examples': by_type
    }

def main():
    print("=" * 80)
    print("ENTITY EXTRACTION TEST ON LARGE GOST DOCUMENTS")
    print("=" * 80)
    
    # Initialize extractor
    print("\nInitializing EntityExtractor with custom patterns...")
    extractor = EntityExtractor(
        model_name="en_core_web_sm",
        russian_model="ru_core_news_sm",
        use_custom_types=True
    )
    
    for i, filepath in enumerate(DOC_FILES, 1):
        doc_name = Path(filepath).stem
        print(f"\n{'='*80}")
        print(f"DOCUMENT {i}: {doc_name}")
        print(f"{'='*80}")
        
        # Load document
        try:
            doc_data = load_document(filepath)
        except Exception as e:
            print(f"ERROR loading document: {e}")
            continue
        
        doc_info = f"{doc_data.get('doc_id', 'N/A')} / {doc_data.get('filename', 'N/A')}"
        print(f"Document Info: {doc_info}")
        print(f"Total Chunks: {doc_data.get('total_chunks', len(doc_data.get('chunks', [])))}")
        
        # Combine all chunk content for extraction
        chunks = doc_data.get('chunks', [])
        if not chunks:
            print("WARNING: No chunks found!")
            continue
        
        # Process first 3 chunks individually to show variety
        num_chunks_to_process = min(3, len(chunks))
        all_entities = []
        
        for chunk_idx in range(num_chunks_to_process):
            chunk = chunks[chunk_idx]
            content = chunk.get('content', '')
            chunk_title = chunk.get('title', f'Chunk {chunk_idx}')[:50]
            
            print(f"\n--- Processing Chunk {chunk_idx}: {chunk_title}... ---")
            print(f"Content length: {len(content)} chars")
            
            # Extract entities
            entities = extract_entities_pattern_based(content, extractor)
            all_entities.extend(entities)
            
            # Show top entities from this chunk
            if entities:
                summary = summarize_entities(entities)
                print(f"  Found {summary['total']} entities")
                for ent_type, count in list(summary['by_type'].items())[:5]:
                    examples = ', '.join(summary['examples'][ent_type][:3])
                    print(f"    • {ent_type}: {count} ({examples[:80]}...)")
            else:
                print("  No entities found")
        
        # Overall statistics for document
        print(f"\n{'─'*80}")
        print(f"DOCUMENT SUMMARY: {doc_name}")
        print(f"{'─'*80}")
        
        if all_entities:
            summary = summarize_entities(all_entities)
            
            print(f"\nTotal Entities Extracted: {summary['total']}")
            print(f"\nEntities by Type:")
            for ent_type, count in sorted(summary['by_type'].items(), key=lambda x: -x[1]):
                print(f"  {ent_type}: {count}")
            
            print(f"\nTop Entity Examples:")
            for ent_type, examples in list(summary['examples'].items())[:8]:
                if examples:
                    print(f"\n  [{ent_type}]")
                    for ex in examples[:3]:
                        print(f"    - {ex}")
        else:
            print("No entities extracted from document")
        
        # Extract standards specifically
        print(f"\n{'─'*80}")
        print(f"STANDARDS EXTRACTION (Pattern-based)")
        print(f"{'─'*80}")
        
        full_text = "\n\n".join([c.get('content', '') for c in chunks[:5]])
        standards = extractor.extract_standards_pattern(full_text)
        
        if standards:
            print(f"Found {len(standards)} standard references:")
            for std in standards[:15]:
                print(f"  • {std['text']} ({std.get('standard_type', 'STANDARD')})")
            if len(standards) > 15:
                print(f"  ... and {len(standards) - 15} more")
        else:
            print("No standards found")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

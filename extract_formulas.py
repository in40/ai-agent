#!/usr/bin/env python3
"""
Extract Mathematical Formulas from GOST Documents
Adds formula extraction to the hybrid pipeline
"""

import sys, json, re
from pathlib import Path
sys.path.insert(0, 'backend/services/rag')

from nlp_tools.entity_extractor import EntityExtractor

DOC_STORE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"
OUTPUT_DIR = "/root/qwen/ai_agent/extraction_results_with_formulas"

print("=" * 80)
print("FORMULA EXTRACTION FROM GOST DOCUMENTS")
print("=" * 80)

# Mathematical formula patterns
FORMULA_PATTERNS = {
    'CRYPTO_FUNCTION': r'(HKDF-Expand-Label|HKDF-Extract|Derive-Secret|Transcript-Hash)\s*\(',
    'VARIABLE_ASSIGNMENT': r'([a-zA-Z_][a-zA-Z0-9_]*(?:\\text\{[^}]+\})?)\s*=',
    'HASH_VALUE': r'[A-F0-9]{16,}',
    'KEY_MATERIAL': r'(MasterSecret|EarlySecret|HandshakeSecret|ClientHello|ServerHello)',
    'TRAFFIC_SECRET': r'(CATS|SATS|CHTS|SHTS|TrafficSecret)',
    'LATEX_MATH': r'\\(frac|sqrt|sum|int|text|multirow)\{[^}]+\}',
    'MODULAR_ARITHMETIC': r'\d+\s*mod\s*\d+',
    'XOR_OPERATION': r'[a-zA-Z0-9_]+\s*xor\s*[a-zA-Z0-9_]+',
}

# Create output directory
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Initialize pattern extractor
extractor = EntityExtractor(use_custom_types=True)

# Get all documents
chunks_files = list(Path(DOC_STORE_PATH).glob("*.chunks.json"))
print(f"\nFound {len(chunks_files)} documents\n")

all_formulas = []
stats = {'processed': 0, 'total_formulas': 0, 'by_type': {}}

# Process each document
for i, chunks_file in enumerate(chunks_files, 1):
    doc_name = chunks_file.stem.replace('.chunks', '')
    
    if i % 20 == 0:
        print(f"[{i}/{len(chunks_files)}] Processing...")
    
    try:
        with open(chunks_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        
        chunks = doc_data.get('chunks', [])
        doc_formulas = []
        
        # Search each chunk for formulas
        for chunk_idx, chunk in enumerate(chunks):
            content = chunk.get('content', '')
            
            # Extract formulas using regex patterns
            for formula_type, pattern in FORMULA_PATTERNS.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    formula = {
                        'text': match if isinstance(match, str) else match[0] if isinstance(match, tuple) else str(match),
                        'type': formula_type,
                        'doc_name': doc_name,
                        'chunk_index': chunk_idx,
                        'source': 'pattern'
                    }
                    
                    doc_formulas.append(formula)
                    all_formulas.append(formula)
                    
                    # Update stats
                    stats['by_type'][formula_type] = stats['by_type'].get(formula_type, 0) + 1
        
        if doc_formulas:
            # Save document formulas
            output_file = Path(OUTPUT_DIR) / f"{doc_name}_formulas.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'doc_name': doc_name,
                    'formula_count': len(doc_formulas),
                    'formulas': doc_formulas
                }, f, ensure_ascii=False, indent=2)
            
            stats['total_formulas'] += len(doc_formulas)
            stats['processed'] += 1
            
            if len(doc_formulas) > 0:
                print(f"  [{i}] {doc_name}: {len(doc_formulas)} formulas")
        
    except Exception as e:
        print(f"  [{i}] {doc_name}: ERROR - {e}")

# Save all formulas combined
with open(Path(OUTPUT_DIR) / "all_formulas.json", 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(all_formulas),
        'formulas': all_formulas
    }, f, ensure_ascii=False, indent=2)

# Save summary
summary = {
    'statistics': stats,
    'formula_types': list(stats['by_type'].keys()),
    'documents_processed': stats['processed']
}

with open(Path(OUTPUT_DIR) / "formula_summary.json", 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# Print final summary
print("\n" + "=" * 80)
print("FORMULA EXTRACTION COMPLETE")
print("=" * 80)
print(f"Documents processed: {stats['processed']}")
print(f"Total formulas found: {stats['total_formulas']}")
print(f"\nFormulas by type:")
for ftype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1])[:15]:
    print(f"  {ftype}: {count}")

print(f"\nResults saved to: {OUTPUT_DIR}/")
print("=" * 80)

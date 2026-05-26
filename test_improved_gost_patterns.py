#!/usr/bin/env python3
"""
Test Improved GOST Pattern Extraction
Tests updated regex patterns against actual document content
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

from nlp_tools.entity_extractor import EntityExtractor

def test_patterns_directly():
    """Test regex patterns directly on sample text"""
    print("=" * 80)
    print("DIRECT PATTERN TESTING")
    print("=" * 80)
    
    # Sample GOST references from actual documents
    test_cases = [
        "ГОСТ Р 52069.0-2013",
        "ГОСТ Р 52069.0—2013", 
        "ГОСТ Р 52633-2014",
        "ГОСТ 1.1",
        "ГОСТ 1.2",
        "ГОСТ 50922-2006",
        "ГОСТ Р 7.0.8",
        "ГОСТ Р 53114",
        "ISO 27001",
        "IEC 61508",
    ]
    
    patterns = {
        "GOST_R_WITH_DECIMAL": r'ГОСТ\s+Р\s+\d+\.\d+[\s\-–—]+\d{4}',
        "GOST_R": r'ГОСТ\s+Р\s+\d+[\s\-–—]+\d{4}',
        "GOST_WITH_DECIMAL": r'ГОСТ\s+\d+\.\d+(?!\d)',
        "GOST_WITH_DECIMAL_YEAR": r'ГОСТ\s+\d+\.\d+[\s\-–—]+\d{4}',
        "GOST_SIMPLE": r'ГОСТ\s+\d+[\s\-–—]\s*\d{4}',
        "ISO": r'ISO\s*\d+(-\d+)?',
        "IEC": r'IEC\s*\d+(-\d+)?',
    }
    
    for test_text in test_cases:
        print(f"\nTesting: '{test_text}'")
        found = False
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, test_text)
            if match:
                print(f"  ✓ {pattern_name}: '{match.group()}'")
                found = True
        if not found:
            print(f"  ✗ No match found")

def test_on_document():
    """Test extraction on actual document"""
    print("\n" + "=" * 80)
    print("DOCUMENT EXTRACTION TEST")
    print("=" * 80)
    
    # Load extractor with improved patterns
    extractor = EntityExtractor(
        model_name="en_core_web_sm",
        russian_model="ru_core_news_sm",
        use_custom_types=True
    )
    
    # Test document
    doc_file = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/gost-r-52069_2c53c42c.txt"
    
    if not Path(doc_file).exists():
        print(f"Document not found: {doc_file}")
        return
    
    print(f"\nLoading document: {Path(doc_file).name}")
    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Document size: {len(content)} chars")
    
    # Test standards extraction
    print("\n--- Standards Extraction ---")
    standards = extractor.extract_standards_pattern(content)
    
    if standards:
        print(f"Found {len(standards)} standard references:")
        
        # Group by type
        by_type = {}
        for std in standards:
            std_type = std.get('standard_type', 'UNKNOWN')
            if std_type not in by_type:
                by_type[std_type] = []
            if len(by_type[std_type]) < 10:
                by_type[std_type].append(std['text'])
        
        for std_type, examples in by_type.items():
            print(f"\n{std_type} ({len([s for s in standards if s.get('standard_type') == std_type])} found):")
            for example in set(examples)[:5]:
                print(f"  • {example}")
            
            if len(set(examples)) > 5:
                print(f"  ... and {len(set(examples)) - 5} more unique")
    else:
        print("No standards found!")
    
    # Test full entity extraction
    print("\n--- Full Entity Extraction (First 5000 chars) ---")
    sample_text = content[:5000]
    entities = extractor.extract_all_entities(
        sample_text,
        use_spacy=True,
        use_patterns=True,
        extract_technologies=True
    )
    
    # Count by type
    by_type = {}
    for ent in entities:
        ent_type = ent.get('label', 'UNKNOWN')
        if ent_type not in by_type:
            by_type[ent_type] = []
        if len(by_type[ent_type]) < 5:
            by_type[ent_type].append(ent.get('text', ''))
    
    print(f"Total entities: {len(entities)}")
    for ent_type, examples in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n{ent_type}:")
        for example in set(examples):
            print(f"  • {example}")

def test_custom_patterns():
    """Test custom entity patterns"""
    print("\n" + "=" * 80)
    print("CUSTOM ENTITY PATTERNS TEST")
    print("=" * 80)
    
    from nlp_tools.custom_entity_types import CUSTOM_ENTITY_PATTERNS, CUSTOM_ENTITY_TYPES
    
    print(f"\nCustom Entity Types ({len(CUSTOM_ENTITY_TYPES)}):")
    for ent_type, description in CUSTOM_ENTITY_TYPES.items():
        patterns_count = len(CUSTOM_ENTITY_PATTERNS.get(ent_type, {}).get('patterns', []))
        print(f"  • {ent_type}: {description} ({patterns_count} patterns)")
    
    # Test GOST pattern specifically
    print("\n--- Testing GOST_STANDARD Pattern ---")
    gost_patterns = CUSTOM_ENTITY_PATTERNS.get('GOST_STANDARD', {}).get('patterns', [])
    print(f"Number of GOST patterns: {len(gost_patterns)}")
    
    test_texts = [
        "Согласно ГОСТ Р 52069.0-2013 требуется...",
        "Используя ГОСТ 1.1 можно определить...",
        "ГОСТ Р 52633-2014 устанавливает...",
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        # Simple test - just show what patterns exist
        for i, pattern in enumerate(gost_patterns):
            print(f"  Pattern {i+1}: {pattern}")

if __name__ == "__main__":
    test_patterns_directly()
    test_on_document()
    test_custom_patterns()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

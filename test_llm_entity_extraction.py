#!/usr/bin/env python3
"""
Test LLM-Based Entity Extraction on 2 Large GOST Documents
Uses LM Studio at fedora:8081 with Qwen3.5-2B model
"""

import sys
import json
import requests
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

# LM Studio configuration
LM_STUDIO_URL = "http://fedora:8081/v1"
LM_MODEL = "Qwen3.5-2B-UD-Q4_K_XL.gguf"

# Entity extraction prompt optimized for GOST documents
ENTITY_EXTRACTION_PROMPT = """You are an expert NLP entity extractor for Russian technical standards (GOST). Extract all entities from the text and classify them.

## Entity Types:
1. STANDARD - Technical standards (GOST, ISO, IEC) with numbers like "ГОСТ Р 52069.0-2013"
2. ORGANIZATION - Government bodies, agencies, institutes (ФСТЭК, ФСБ, институты)
3. TECHNICAL_TERM - Security/crypto terms (шифрование, подпись, ключ)
4. LOCATION - Cities, countries (Москва, Россия)
5. DATE - Dates and periods
6. PERSON - People names
7. DOCUMENT_TYPE - Types of documents (стандарт, закон, приказ)
8. SECURITY_CONCEPT - Security concepts (аутентификация, конфиденциальность)

## Output Format (JSON only):
{{
  "entities": [
    {{"text": "entity text", "type": "ENTITY_TYPE", "confidence": 0.9}}
  ]
}}

Text to analyze:
{text}"""

def extract_entities_llm(text, max_length=4000):
    """Extract entities using LLM"""
    # Truncate if necessary
    if len(text) > max_length:
        text = text[:max_length] + "... [truncated]"
    
    prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)
    
    try:
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={
                "model": LM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert entity extractor. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            },
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"entities": [], "error": "No JSON found"}
            
    except Exception as e:
        return {"entities": [], "error": str(e)}

def test_on_documents():
    """Test LLM extraction on 2 documents"""
    print("=" * 80)
    print("LLM-BASED ENTITY EXTRACTION TEST")
    print(f"Model: {LM_MODEL}")
    print(f"Endpoint: {LM_STUDIO_URL}")
    print("=" * 80)
    
    # Test documents
    docs = [
        "document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/gost-r-52069_2c53c42c.txt",
        "document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_78b35e61.txt"
    ]
    
    # Test on first 10K chars of each document (LLM token limit)
    for doc_path in docs:
        doc_name = Path(doc_path).stem
        print(f"\n{'='*80}")
        print(f"DOCUMENT: {doc_name}")
        print(f"{'='*80}")
        
        if not Path(doc_path).exists():
            print(f"  ERROR: File not found!")
            continue
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use first 10K chars for LLM (to avoid token limits)
        sample_text = content[:10000]
        print(f"  Sample size: {len(sample_text)} chars")
        
        print("  Extracting entities with LLM...")
        result = extract_entities_llm(sample_text)
        
        if "error" in result and result["error"]:
            print(f"  ERROR: {result['error']}")
            continue
        
        entities = result.get("entities", [])
        print(f"  Found {len(entities)} entities")
        
        # Group by type
        by_type = defaultdict(list)
        for ent in entities:
            ent_type = ent.get("type", "UNKNOWN")
            if len(by_type[ent_type]) < 5:
                by_type[ent_type].append(ent.get("text", ""))
        
        if by_type:
            print(f"\n  Entities by type:")
            for ent_type, examples in sorted(by_type.items(), key=lambda x: -len(x[1])):
                unique_examples = list(set(examples))
                print(f"    {ent_type}: {len(unique_examples)} unique")
                for ex in unique_examples[:3]:
                    print(f"      • {ex[:80]}")
        else:
            print("  No entities extracted")
        
        # Show raw response for debugging
        if len(entities) > 0:
            print(f"\n  Sample entities:")
            for ent in entities[:5]:
                print(f"    - {ent.get('text', 'N/A')} ({ent.get('type', 'N/A')})")

def test_standards_specifically():
    """Test LLM extraction focused on GOST standards"""
    print("\n" + "=" * 80)
    print("STANDARDS EXTRACTION TEST (LLM)")
    print("=" * 80)
    
    doc_path = "document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/gost-r-52069_2c53c42c.txt"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()[:10000]
    
    # Simpler prompt for standards only
    standards_prompt = """Extract all GOST standard references from this Russian text. Return ONLY JSON array of standard numbers.

Example output: ["ГОСТ Р 52069.0-2013", "ГОСТ 1.1", "ГОСТ 1.2"]

Text:
{text}"""
    
    prompt = standards_prompt.format(text=content)
    
    print("  Extracting standards with LLM...")
    
    try:
        response = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={
                "model": LM_MODEL,
                "messages": [
                    {"role": "system", "content": "You extract GOST standard numbers. Return ONLY JSON array."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1000
            },
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        import re
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            standards = json.loads(json_match.group(0))
            print(f"  Found {len(standards)} standards:")
            for std in standards[:15]:
                print(f"    • {std}")
            if len(standards) > 15:
                print(f"    ... and {len(standards) - 15} more")
        else:
            print(f"  Could not parse JSON. Raw response: {content[:200]}")
            
    except Exception as e:
        print(f"  ERROR: {e}")

if __name__ == "__main__":
    test_on_documents()
    test_standards_specifically()
    
    print("\n" + "=" * 80)
    print("LLM EXTRACTION TEST COMPLETE")
    print("=" * 80)

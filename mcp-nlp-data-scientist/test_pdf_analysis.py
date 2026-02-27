#!/usr/bin/env python3
"""
Test NLP Data Scientist Server with Real PDF Document
Measures processing time and shows entity extraction results
"""
import os
import sys
import time
import json
import requests
import pdfplumber
from datetime import datetime

# Configuration
PDF_PATH = "/root/qwen/ai_agent/downloads/gost-r-50922-2006.pdf"
NLP_SERVER_URL = "http://localhost:3065/mcp"
LLM_TIMEOUT = 300  # 5 minutes for LLM processing
REQUEST_TIMEOUT = 600  # 10 minutes total

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    print(f"\n📄 Extracting text from: {pdf_path}")
    print(f"   File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    start_time = time.time()
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    text_pages.append(text)
            
            full_text = "\n\n".join(text_pages)
            
        extraction_time = time.time() - start_time
        print(f"   ✓ Text extracted in {extraction_time:.2f}s")
        print(f"   Total characters: {len(full_text):,}")
        print(f"   Total pages: {len(pdf.pages)}")
        
        return full_text, len(pdf.pages)
        
    except Exception as e:
        print(f"   ✗ Error extracting text: {e}")
        return None, 0

def call_nlp_server(tool_name, arguments, timeout=60):
    """Call NLP server tool"""
    payload = {
        "jsonrpc": "2.0",
        "id": f"{tool_name}-{int(time.time())}",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = requests.post(NLP_SERVER_URL, json=payload, timeout=timeout)
        result = response.json()
        
        if "error" in result:
            return {"error": result["error"]}
        
        # Parse the text content
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        return json.loads(content)
        
    except requests.exceptions.Timeout:
        return {"error": f"Request timeout after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}

def analyze_document(text, method="spacy"):
    """Analyze document using NLP server"""
    print(f"\n🔍 Analyzing document with {method}...")
    start_time = time.time()
    
    # Split text into chunks if too long (LLM has limits)
    max_chunk_size = 8000
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    
    print(f"   Split into {len(chunks)} chunks for processing")
    
    all_entities = []
    chunk_times = []
    
    for i, chunk in enumerate(chunks):
        print(f"   Processing chunk {i+1}/{len(chunks)}...")
        chunk_start = time.time()
        
        if method == "llm":
            result = call_nlp_server(
                "extract_entities_llm",
                {"text": chunk, "max_length": 8000},
                timeout=LLM_TIMEOUT
            )
        else:
            result = call_nlp_server(
                "extract_entities",
                {
                    "text": chunk,
                    "use_spacy": True,
                    "use_patterns": True,
                    "extract_technologies": True
                },
                timeout=REQUEST_TIMEOUT
            )
        
        chunk_time = time.time() - chunk_start
        chunk_times.append(chunk_time)
        
        if "error" in result:
            print(f"   ✗ Chunk {i+1} error: {result['error']}")
        else:
            entities = result.get("entities", [])
            all_entities.extend(entities)
            print(f"   ✓ Chunk {i+1}: {len(entities)} entities ({chunk_time:.2f}s)")
    
    total_time = time.time() - start_time
    avg_chunk_time = sum(chunk_times) / len(chunk_times) if chunk_times else 0
    
    print(f"\n   📊 Analysis Summary:")
    print(f"      Total time: {total_time:.2f}s ({total_time/60:.2f} min)")
    print(f"      Avg per chunk: {avg_chunk_time:.2f}s")
    print(f"      Total entities: {len(all_entities)}")
    
    return all_entities, total_time

def extract_standards(text):
    """Extract only technical standards"""
    print(f"\n📋 Extracting technical standards...")
    start_time = time.time()
    
    result = call_nlp_server(
        "extract_standards",
        {"text": text},
        timeout=REQUEST_TIMEOUT
    )
    
    elapsed = time.time() - start_time
    
    if "error" in result:
        print(f"   ✗ Error: {result['error']}")
        return [], elapsed
    
    standards = result.get("standards", [])
    print(f"   ✓ Found {len(standards)} standards in {elapsed:.2f}s")
    
    return standards, elapsed

def get_entity_statistics(entities):
    """Get statistics about extracted entities"""
    from collections import Counter
    
    label_counts = Counter([e["label"] for e in entities])
    
    return {
        "total": len(entities),
        "by_type": dict(label_counts),
        "unique_types": len(label_counts)
    }

def print_entity_summary(entities):
    """Print formatted entity summary"""
    stats = get_entity_statistics(entities)
    
    print(f"\n📊 Entity Statistics:")
    print(f"   Total entities: {stats['total']}")
    print(f"   Unique types: {stats['unique_types']}")
    print(f"\n   By type:")
    
    for entity_type, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
        print(f"      {entity_type}: {count}")
    
    # Show examples of each type
    print(f"\n   Examples by type:")
    shown_types = set()
    for entity in entities:
        label = entity["label"]
        if label not in shown_types and len(shown_types) < 5:
            shown_types.add(label)
            text = entity["text"][:50].replace("\n", " ")
            print(f"      {label}: {text}...")

def main():
    """Main test function"""
    print("=" * 70)
    print("NLP Data Scientist Server - PDF Analysis Test")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"NLP Server: {NLP_SERVER_URL}")
    
    # Check if server is running
    print(f"\n🔌 Checking server connection...")
    try:
        ping_result = requests.post(NLP_SERVER_URL, json={
            "jsonrpc": "2.0",
            "id": "ping-1",
            "method": "tools/call",
            "params": {"name": "ping", "arguments": {}}
        }, timeout=10)
        print(f"   ✓ Server is responding")
    except Exception as e:
        print(f"   ✗ Server not responding: {e}")
        print(f"   Make sure to run: ./start_nlp_server.sh")
        sys.exit(1)
    
    # Check if PDF exists
    if not os.path.exists(PDF_PATH):
        print(f"\n✗ PDF file not found: {PDF_PATH}")
        sys.exit(1)
    
    # Extract text from PDF
    text, page_count = extract_text_from_pdf(PDF_PATH)
    if not text:
        print("\n✗ Failed to extract text from PDF")
        sys.exit(1)
    
    # Test 1: spaCy entity extraction
    print("\n" + "=" * 70)
    print("TEST 1: Entity Extraction (spaCy + Patterns)")
    print("=" * 70)
    
    entities_spacy, time_spacy = analyze_document(text, method="spacy")
    print_entity_summary(entities_spacy)
    
    # Test 2: Standards extraction
    print("\n" + "=" * 70)
    print("TEST 2: Technical Standards Extraction")
    print("=" * 70)
    
    standards, time_standards = extract_standards(text)
    if standards:
        print(f"\n   Found standards:")
        for std in standards:
            print(f"      - {std['text']} ({std.get('standard_type', 'Unknown')})")
    
    # Test 3: LLM entity extraction (on first chunk only for speed)
    print("\n" + "=" * 70)
    print("TEST 3: Entity Extraction (LLM) - First 8000 chars only")
    print("=" * 70)
    
    text_sample = text[:8000]
    entities_llm, time_llm = analyze_document(text_sample, method="llm")
    print_entity_summary(entities_llm)
    
    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Document: {os.path.basename(PDF_PATH)}")
    print(f"Pages: {page_count}")
    print(f"Text length: {len(text):,} characters")
    print(f"\nProcessing Times:")
    print(f"   spaCy extraction: {time_spacy:.2f}s ({time_spacy/60:.2f} min)")
    print(f"   Standards extraction: {time_standards:.2f}s")
    print(f"   LLM extraction (sample): {time_llm:.2f}s")
    print(f"\nResults:")
    print(f"   Entities (spaCy): {len(entities_spacy)}")
    print(f"   Standards found: {len(standards)}")
    print(f"   Entities (LLM sample): {len(entities_llm)}")
    print("\n" + "=" * 70)
    
    # Save results to file
    results_file = "/root/qwen/ai_agent/mcp-nlp-data-scientist/test_results.json"
    results = {
        "timestamp": datetime.now().isoformat(),
        "document": os.path.basename(PDF_PATH),
        "pages": page_count,
        "text_length": len(text),
        "processing_times": {
            "spacy_extraction_seconds": time_spacy,
            "standards_extraction_seconds": time_standards,
            "llm_extraction_seconds": time_llm
        },
        "results": {
            "entities_spacy_count": len(entities_spacy),
            "standards_count": len(standards),
            "entities_llm_count": len(entities_llm),
            "standards_found": standards,
            "entity_types_spacy": get_entity_statistics(entities_spacy)
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()

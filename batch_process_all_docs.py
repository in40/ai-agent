#!/usr/bin/env python3
"""
Batch processor for GOST documents:
1. Re-chunk documents using recursive strategy
2. Incrementally add to Qdrant
3. Generate queries and answers from document content
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import hashlib

# Configuration
DOC_DIR = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"
OUTPUT_DIR = "/root/qwen/ai_agent/batch_processing_output"
CHUNKS_DIR = "/root/qwen/ai_agent/rechunked_chunks"

# Chunking parameters (from successful benchmark)
TARGET_CHUNK_SIZE = 512  # tokens ≈ 2000 chars
OVERLAP_TOKENS = 51  # 10% overlap
MAX_CHUNK_SIZE = 8000  # chars
MIN_CHUNK_SIZE = 500  # chars

# Qdrant configuration
QDRANT_URL = "http://localhost:6333"
QDRANT_KEY = "7b4d2e6a1c8f4e5f9a3b6c8d2e4f7a9b0c6d5e8f1a2b3c4d5e6f7a8b9c0d"
COLLECTION_NAME = "documents"

# Already processed documents
PROCESSED_DOCS = [
    "gost-r-52069_2c53c42c",
    "r-1323565.1_78b35e61"
]

def get_unique_documents() -> List[str]:
    """Get list of unique document base names (excluding already processed)."""
    txt_files = Path(DOC_DIR).glob("*.txt")
    md_files = Path(DOC_DIR).glob("*.md")
    
    all_files = list(txt_files) + list(md_files)
    unique_bases = set()
    
    for f in all_files:
        base = f.stem  # removes .txt or .md
        if base not in PROCESSED_DOCS:
            unique_bases.add(base)
    
    return sorted(list(unique_bases))

def get_document_file(doc_name: str) -> str:
    """Get the file path for a document (prefer .txt over .md)."""
    txt_path = Path(DOC_DIR) / f"{doc_name}.txt"
    md_path = Path(DOC_DIR) / f"{doc_name}.md"
    
    if txt_path.exists():
        return str(txt_path)
    elif md_path.exists():
        return str(md_path)
    else:
        return None

def recursive_chunk(text: str, chunk_size: int = 2000, overlap: int = 200, 
                   min_size: int = 500, max_size: int = 8000) -> List[str]:
    """
    Recursive character splitting with semantic boundaries.
    """
    chunks = []
    
    if len(text) <= max_size:
        # Check if we can find good split points
        if len(text) >= min_size:
            return [text]
    
    # Try to split at paragraph boundaries first
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) <= max_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            if len(para) <= max_size:
                current_chunk = para + "\n\n"
            else:
                # Paragraph too long, split at sentence boundaries
                sentences = re.split(r'([.!?]\s+)', para)
                current_para = ""
                for sent in sentences:
                    if len(current_para) + len(sent) <= max_size:
                        current_para += sent
                    else:
                        if current_para.strip():
                            chunks.append(current_para.strip())
                        current_para = sent
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Filter out tiny chunks
    chunks = [c for c in chunks if len(c) >= min_size]
    
    return chunks

def read_document_content(file_path: str) -> str:
    """Read document content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def generate_queries_from_content(doc_name: str, content: str) -> List[Dict]:
    """Generate natural queries based on document content."""
    queries = []
    
    # Extract title/first section
    lines = content.split('\n')[:20]
    title = lines[0] if lines else doc_name
    
    # Generate general questions
    queries.append({
        "id": 1,
        "query": f"что такое {doc_name}",
        "category": "general",
        "expected_doc": doc_name
    })
    
    # Look for section headers and generate questions
    section_headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)[:10]
    
    for i, header in enumerate(section_headers[:8], 2):
        header_clean = header.strip()[:50]
        queries.append({
            "id": i,
            "query": f"что говорится в разделе о {header_clean}",
            "category": "content",
            "expected_doc": doc_name
        })
    
    # Look for specific terms and standards mentioned
    gost_refs = re.findall(r'ГОСТ\s+Р?\s*[\d.-]+', content)
    for i, ref in enumerate(set(gost_refs[:5]), 10):
        queries.append({
            "id": i,
            "query": f"что такое {ref}",
            "category": "definitions",
            "expected_doc": doc_name
        })
    
    # Ensure we have at least 15 queries
    while len(queries) < 15:
        queries.append({
            "id": len(queries) + 1,
            "query": f"какие требования установлены в {doc_name}",
            "category": "requirements",
            "expected_doc": doc_name
        })
    
    return queries[:20]  # Return up to 20 queries

def generate_answers_from_content(doc_name: str, content: str, queries: List[Dict]) -> List[Dict]:
    """Generate answers based on document content for each query."""
    answers = []
    
    # Get document sections
    sections = re.split(r'^#+\s+', content, flags=re.MULTILINE)
    
    for query in queries:
        query_text = query['query']
        
        # Try to find relevant content
        answer_text = ""
        
        # Search for keywords from query in content
        query_lower = query_text.lower()
        
        # Look for matching paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs[:30]:  # Check first 30 paragraphs
            if any(keyword in para.lower() for keyword in query_lower.split()[:3]):
                answer_text = para[:500] + "..."
                break
        
        if not answer_text:
            # Fallback to first meaningful section
            if len(sections) > 1:
                answer_text = sections[1][:500] + "..."
            else:
                answer_text = content[:500] + "..."
        
        answers.append({
            "query_id": query['id'],
            "query": query['query'],
            "answer": answer_text,
            "doc_name": doc_name
        })
    
    return answers

def chunk_document(doc_name: str) -> Dict:
    """Chunk a single document and return metadata."""
    file_path = get_document_file(doc_name)
    
    if not file_path:
        print(f"  ⚠️ Document not found: {doc_name}")
        return None
    
    print(f"  Processing: {doc_name}")
    
    # Read content
    content = read_document_content(file_path)
    if not content:
        return None
    
    # Chunk content
    chunks = recursive_chunk(content)
    
    print(f"    → Generated {len(chunks)} chunks")
    
    return {
        "doc_name": doc_name,
        "file_path": file_path,
        "total_chars": len(content),
        "total_chunks": len(chunks),
        "chunks": chunks
    }

def main():
    """Main processing function."""
    print("=" * 60)
    print("GOST DOCUMENT BATCH PROCESSOR")
    print("=" * 60)
    
    # Create output directories
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    Path(CHUNKS_DIR).mkdir(exist_ok=True)
    
    # Get documents to process
    print("\n1. Getting document list...")
    docs = get_unique_documents()
    print(f"   Found {len(docs)} documents to process")
    
    # Process each document
    print("\n2. Chunking documents...")
    all_chunks_data = []
    all_queries = []
    all_answers = []
    
    for i, doc_name in enumerate(docs, 1):
        print(f"\n[{i}/{len(docs)}] {doc_name}")
        
        # Chunk document
        chunk_data = chunk_document(doc_name)
        if chunk_data:
            all_chunks_data.append(chunk_data)
            
            # Save chunks to file
            chunks_file = Path(CHUNKS_DIR) / f"{doc_name}.chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "doc_name": doc_name,
                    "chunks": chunk_data['chunks']
                }, f, ensure_ascii=False, indent=2)
            
            # Generate queries
            content = read_document_content(chunk_data['file_path'])
            queries = generate_queries_from_content(doc_name, content)
            all_queries.extend(queries)
            
            # Generate answers
            answers = generate_answers_from_content(doc_name, content, queries)
            all_answers.extend(answers)
    
    # Save combined outputs
    print("\n3. Saving combined outputs...")
    
    # Save all queries
    queries_file = Path(OUTPUT_DIR) / "all_queries.json"
    with open(queries_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_documents": len(all_chunks_data),
            "total_queries": len(all_queries),
            "queries": all_queries
        }, f, ensure_ascii=False, indent=2)
    print(f"   Saved {len(all_queries)} queries to {queries_file}")
    
    # Save all answers
    answers_file = Path(OUTPUT_DIR) / "all_answers.json"
    with open(answers_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_documents": len(all_chunks_data),
            "total_answers": len(all_answers),
            "answers": all_answers
        }, f, ensure_ascii=False, indent=2)
    print(f"   Saved {len(all_answers)} answers to {answers_file}")
    
    # Save summary
    summary = f"""
# Batch Processing Summary

## Documents Processed
- Total: {len(all_chunks_data)} documents
- Already processed (excluded): {len(PROCESSED_DOCS)}

## Chunking Statistics
"""
    for chunk_data in all_chunks_data[:10]:  # Show first 10
        summary += f"- {chunk_data['doc_name']}: {chunk_data['total_chunks']} chunks ({chunk_data['total_chars']} chars)\n"
    
    if len(all_chunks_data) > 10:
        summary += f"\n... and {len(all_chunks_data) - 10} more documents\n"
    
    summary += f"""
## Generated Content
- Total queries: {len(all_queries)}
- Total answers: {len(all_answers)}

## Output Files
- `{OUTPUT_DIR}/all_queries.json` - All queries in JSON format
- `{OUTPUT_DIR}/all_answers.json` - All answers in JSON format
- `{CHUNKS_DIR}/` - Individual chunk files for each document
"""
    
    summary_file = Path(OUTPUT_DIR) / "PROCESSING_SUMMARY.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\n4. Complete! Summary saved to {summary_file}")

if __name__ == "__main__":
    main()

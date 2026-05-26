#!/usr/bin/env python3
"""
Re-chunk documents using recursive character splitting with strict size limits
Based on FloTorch 2026 benchmark recommendations:
- Recursive character splitting at 512 tokens ~ 2000 chars
- Minimum chunk size: 500 chars (avoid tiny fragments)
- Maximum chunk size: 8000 chars (prevent diluted embeddings)
"""

import json
import re
from pathlib import Path

# Configuration based on benchmarks
TARGET_CHUNK_SIZE = 2000     # ~512 tokens
OVERLAP_CHARS = 200          # 10% overlap
MIN_CHUNK_SIZE = 500         # Avoid tiny fragments  
MAX_CHUNK_SIZE = 8000        # Hard limit to prevent diluted embeddings

def split_text_to_chunks(text: str) -> list:
    """
    Split text into chunks with strict size limits.
    Tries to split at paragraph boundaries first, then falls back to character splitting.
    """
    chunks = []
    
    # First try splitting by paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_len = len(para)
        
        # If single paragraph exceeds max, split it by lines or characters
        if para_len > MAX_CHUNK_SIZE:
            # Flush current chunk first
            if current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                if len(chunk_text) > MAX_CHUNK_SIZE:
                    # Split this oversized chunk further
                    chunks.extend(force_split_chunk(chunk_text))
                else:
                    chunks.append(chunk_text)
                current_chunk = []
                current_size = 0
            
            # Split oversized paragraph
            chunks.extend(force_split_chunk(para))
            continue
        
        # Check if adding this paragraph exceeds target
        if current_size + para_len + 2 > TARGET_CHUNK_SIZE:
            # Flush current chunk
            if current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                if len(chunk_text) > MAX_CHUNK_SIZE:
                    chunks.extend(force_split_chunk(chunk_text))
                else:
                    chunks.append(chunk_text)
            current_chunk = [para]
            current_size = para_len
        else:
            current_chunk.append(para)
            current_size += para_len
    
    # Flush remaining
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        if len(chunk_text) > MAX_CHUNK_SIZE:
            chunks.extend(force_split_chunk(chunk_text))
        else:
            chunks.append(chunk_text)
    
    return chunks

def force_split_chunk(text: str) -> list:
    """Force split an oversized chunk by character count"""
    chunks = []
    
    while len(text) > MAX_CHUNK_SIZE:
        # Find best split point near TARGET_CHUNK_SIZE
        split_point = TARGET_CHUNK_SIZE
        
        # Try to split at paragraph boundary
        if '\n\n' in text[:split_point+500]:
            last_newline = text.rfind('\n\n', 0, split_point + 500)
            if last_newline > TARGET_CHUNK_SIZE // 2:
                split_point = last_newline
        
        # Try to split at line boundary
        elif '\n' in text[:split_point+500]:
            last_newline = text.rfind('\n', 0, split_point + 500)
            if last_newline > TARGET_CHUNK_SIZE // 2:
                split_point = last_newline
        
        chunk = text[:split_point].strip()
        chunks.append(chunk)
        text = text[split_point:].strip()
    
    if text:
        chunks.append(text)
    
    return chunks

def add_overlap(chunks: list) -> list:
    """Add overlap between consecutive chunks"""
    if len(chunks) <= 1:
        return chunks
    
    overlapped = []
    for i, chunk in enumerate(chunks):
        if i > 0 and OVERLAP_CHARS > 0:
            prev = chunks[i-1]
            overlap = prev[-OVERLAP_CHARS:] if len(prev) > OVERLAP_CHARS else prev
            # Don't duplicate if chunk already starts with overlap
            if not chunk.startswith(overlap.strip()[:50]):
                chunk = overlap.strip() + '\n\n' + chunk
        
        # Ensure chunk doesn't exceed max after adding overlap
        if len(chunk) > MAX_CHUNK_SIZE:
            chunk = chunk[:MAX_CHUNK_SIZE]
        
        overlapped.append(chunk)
    
    return overlapped

def chunk_document(text: str, doc_id: str, source_file: str) -> dict:
    """Chunk a document using recursive strategy with strict size limits"""
    
    # Step 1: Split into chunks with size limits
    raw_chunks = split_text_to_chunks(text)
    
    # Step 2: Add overlap
    final_chunks = add_overlap(raw_chunks)
    
    # Create chunk metadata
    chunks_data = []
    for i, content in enumerate(final_chunks):
        chunks_data.append({
            'chunk_id': f"{doc_id}_chunk_{i:04d}",
            'chunk_index': i,
            'content': content,
            'section': '',
            'title': f'Chunk {i+1}',
            'token_count': len(content) // 4,
            'source_file': source_file
        })
    
    # Calculate statistics
    sizes = [len(c['content']) for c in chunks_data]
    
    return {
        'doc_id': doc_id,
        'filename': f"{doc_id}.txt",
        'total_chunks': len(chunks_data),
        'chunking_strategy': 'recursive_512tokens_strict_limits',
        'chunking_config': {
            'target_chunk_size': TARGET_CHUNK_SIZE,
            'overlap_chars': OVERLAP_CHARS,
            'min_chunk_size': MIN_CHUNK_SIZE,
            'max_chunk_size': MAX_CHUNK_SIZE
        },
        'chunks': chunks_data,
        'statistics': {
            'original_text_length': len(text),
            'total_chunks': len(chunks_data),
            'avg_chunk_size': sum(sizes) / len(sizes) if sizes else 0,
            'min_chunk_size': min(sizes) if sizes else 0,
            'max_chunk_size': max(sizes) if sizes else 0
        }
    }

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python rechunk_recursive.py <doc_id> <source_file>")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    source_file = sys.argv[2]
    
    # Read source file
    with open(source_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Processing {doc_id}...")
    print(f"Source file size: {len(text):,} chars")
    
    # Chunk document
    result = chunk_document(text, doc_id, source_file)
    
    # Save to chunks.json
    output_file = Path(source_file).parent / f"{doc_id}.chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Chunking complete!")
    print(f"  Strategy: {result['chunking_strategy']}")
    print(f"  Total chunks: {result['total_chunks']}")
    stats = result['statistics']
    print(f"  Avg chunk size: {stats['avg_chunk_size']:.0f} chars")
    print(f"  Min chunk size: {stats['min_chunk_size']} chars")
    print(f"  Max chunk size: {stats['max_chunk_size']} chars")
    print(f"  Output: {output_file}")

if __name__ == '__main__':
    main()

# Vector Search Quality Improvement Plan

## Current Issues Summary

### 1. Chunk Size Problems
| Issue | Count | Impact |
|-------|-------|--------|
| Giant chunks (>50K chars) | 9 | Diluted embeddings |
| Tiny chunks (<500 chars) | 976 (26%) | Insufficient context |
| Optimal chunks (1K-2K) | 1,154 (31%) | Good quality |

### 2. Search Quality Problems
- Top relevance scores: 0.38-0.65 (should be 0.7-0.9+)
- Duplicate results in search
- Poor separation between relevant/non-relevant documents

---

## Improvements

### A. Fix Chunking Size Limits

In `backend/services/rag/smart_ingestion_enhanced.py`:

```python
# Add chunk size validation (after line 790 where coverage is checked)
MAX_CHUNK_SIZE = 8000   # ~2000 tokens - optimal for bge-m3
MIN_CHUNK_SIZE = 500    # Minimum meaningful context

def validate_chunk_sizes(chunks: List[Dict]) -> List[Dict]:
    """Filter and merge chunks based on size constraints"""
    valid_chunks = []
    pending_small = []
    
    for chunk in chunks:
        content_len = len(chunk.get('content', ''))
        
        if content_len > MAX_CHUNK_SIZE:
            # Split large chunks
            split_chunks = _split_large_chunk(chunk, MAX_CHUNK_SIZE)
            valid_chunks.extend(split_chunks)
        elif content_len < MIN_CHUNK_SIZE:
            # Collect small chunks for merging
            pending_small.append(chunk)
        else:
            # Good size chunk
            if pending_small:
                # Merge with previous small chunks
                merged = _merge_chunks(pending_small + [chunk])
                valid_chunks.append(merged)
                pending_small = []
            else:
                valid_chunks.append(chunk)
    
    return valid_chunks

def _split_large_chunk(chunk: Dict, max_size: int) -> List[Dict]:
    """Split oversized chunk by paragraph boundaries"""
    content = chunk.get('content', '')
    paragraphs = content.split('\n\n')
    
    split_chunks = []
    current_content = []
    current_size = 0
    
    for para in paragraphs:
        if current_size + len(para) > max_size and current_content:
            # Create new chunk
            split_chunks.append({
                **chunk,
                'content': '\n\n'.join(current_content),
                'chunk_index': len(split_chunks)
            })
            current_content = [para]
            current_size = len(para)
        else:
            current_content.append(para)
            current_size += len(para)
    
    if current_content:
        split_chunks.append({
            **chunk,
            'content': '\n\n'.join(current_content),
            'chunk_index': len(split_chunks)
        })
    
    return split_chunks

def _merge_chunks(chunks: List[Dict]) -> Dict:
    """Merge multiple small chunks into one"""
    if len(chunks) == 1:
        return chunks[0]
    
    merged_content = ' '.join([c.get('content', '') for c in chunks])
    return {
        'chunk_id': f"merged_{'_'.join([c['chunk_id'] for c in chunks])}",
        'chunk_index': 0,
        'content': merged_content,
        'section': chunks[0].get('section', ''),
        'title': f"Merged: {chunks[0].get('title', '')}",
        'token_count': len(merged_content) // 4,
    }
```

### B. Add Chunk Quality Validation

Add to `chunk_document_with_llm()` function after JSON parsing:

```python
# After extracting chunks from LLM response (around line 790)
logger.info(f"[VALIDATION] Checking chunk sizes...")

# Validate chunk sizes
original_count = len(valid_chunks)
valid_chunks = validate_chunk_sizes(valid_chunks)
size_adjusted_count = len(valid_chunks)

if size_adjusted_count != original_count:
    logger.warning(
        f"[VALIDATION] Chunk size adjustment: "
        f"{original_count} → {size_adjusted_count} chunks"
    )

# Check for giant chunks that slipped through
giant_chunks = [c for c in valid_chunks if len(c.get('content', '')) > 50000]
if giant_chunks:
    logger.error(
        f"[VALIDATION] CRITICAL: {len(giant_chunks)} chunks exceed 50K chars! "
        f"These will severely degrade embedding quality."
    )
```

### C. Re-process Documents

Create script to re-chunk existing documents:

```python
# run_rechunking.py
"""
Re-process all documents with improved chunking limits
"""
import json
from pathlib import Path

def rechunk_document(chunk_file: Path):
    """Apply new chunking rules to existing document"""
    with open(chunk_file, 'r') as f:
        data = json.load(f)
    
    chunks = data.get('chunks', [])
    valid_chunks = validate_chunk_sizes(chunks)
    
    # Update metadata
    data['chunks'] = valid_chunks
    data['total_chunks'] = len(valid_chunks)
    data['chunking_quality'] = {
        'original_chunks': len(chunks),
        'adjusted_chunks': len(valid_chunks),
        'max_chunk_size': max(len(c.get('content', '')) for c in valid_chunks),
        'min_chunk_size': min(len(c.get('content', '')) for c in valid_chunks),
    }
    
    # Save updated file
    with open(chunk_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return data['chunking_quality']

# Process all chunk files
base_dir = Path("/root/qwen/ai_agent/document-store-mcp-server/data/ingested")
chunk_files = list(base_dir.rglob("*.chunks.json"))

print(f"Re-processing {len(chunk_files)} documents...")
for chunk_file in chunk_files:
    quality = rechunk_document(chunk_file)
    print(f"  {chunk_file.name}: {quality}")
```

---

## Expected Results After Improvements

| Metric | Current | Target |
|--------|---------|--------|
| Max chunk size | 145K | ≤8K |
| Chunks >50K | 9 (0.2%) | 0 |
| Chunks <500 | 976 (26%) | <100 (<3%) |
| Optimal chunks (1K-2K) | 31% | 60%+ |
| Top search scores | 0.4-0.6 | 0.7-0.9+ |
| Duplicate results | Yes | No |

---

## Next Steps

1. **Apply chunk size validation** to `smart_ingestion_enhanced.py`
2. **Re-process existing documents** with new rules
3. **Clear and rebuild Qdrant collection**
4. **Test with Russian queries** to verify improvement
5. **Monitor similarity scores** - should see significant improvement

---

## Additional Enhancements (Future)

### Metadata Filtering
Add searchable metadata fields:
- `document_type`: GOST, R, ISO/IEC
- `security_domain`: cryptography, biometrics, networks, etc.
- `publication_year`: For temporal filtering
- `topic_tags`: Auto-extracted keywords

### Hybrid Search Improvements
- Add BM25 keyword search alongside vector
- Use reranker for better result ordering
- Implement query expansion for Russian synonyms

### Embedding Model Verification
- Confirm bge-m3 is properly loaded with Russian support
- Test embeddings with known Russian queries
- Consider model-specific optimizations

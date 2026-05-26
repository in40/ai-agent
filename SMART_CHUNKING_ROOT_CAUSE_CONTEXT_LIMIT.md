# CRITICAL ROOT CAUSE: Smart Chunking Context Window Exceeded

**Date**: March 29, 2026  
**Severity**: CRITICAL  
**Job Affected**: `job_777c327b39b6`

---

## ACTUAL ROOT CAUSE DISCOVERED

The smart chunking is failing because **the prompt exceeds the LLM's context window**, NOT because of JSON parsing errors!

### Error from LLM Server

```
HTTP 400 Bad Request
{
  "error": "The number of tokens to keep from the initial prompt is 
            greater than the context length (n_keep: 25701 >= n_ctx: 4096). 
            Try to load the model with a larger context length, or provide 
            a shorter input."
}
```

### The Numbers

| Component | Size |
|-----------|------|
| Model | `qwen3.5-0.8b` |
| Model Context Window | 4,096 tokens |
| Prompt Template | ~4,650 chars (~930 tokens) |
| Document Text (current limit) | 50,000 chars (~10,000 tokens) |
| **Total Sent to LLM** | **~11,000+ tokens** |
| **Exceeds Context By** | **~7,000 tokens (270%)** |

### Document Analysis

The failing document `r-1323565.1_395de1a8.md`:
- **Full size**: 140,102 chars (~28,000 tokens)
- **Current code sends**: 50,000 chars (truncated)
- **Still exceeds context**: 10,000+ tokens vs 4,096 limit

---

## Why Previous Analysis Was Misleading

The error message "Failed to parse LLM response: Expecting ',' delimiter" was a **symptom**, not the root cause.

**What actually happens:**
1. Code sends 50K chars + prompt template to LLM
2. LLM server rejects with 400 error (context exceeded)
3. The error handling may not catch this properly
4. Code tries to parse empty/error response as JSON
5. JSON parsing fails with "Expecting ',' delimiter"

---

## Solutions

### Solution 1: Reduce Text Limit (QUICK FIX)

**Change**: Reduce `document_content[:50000]` to fit context window

**Calculation**:
- Context: 4096 tokens
- Reserve 30% for output: 1229 tokens
- Reserve for prompt (930 tokens): 930 tokens  
- Available for text: 4096 - 1229 - 930 = **1937 tokens**
- Character limit: 1937 × 5 chars/token = **~9,500 chars**

**Code Change**:
```python
# In smart_ingestion_enhanced.py, line ~398
# OLD:
full_prompt = prompt.format(input_text=document_content[:50000])

# NEW:
MAX_TEXT_CHARS = 9000  # Safe limit for 4096 context window
full_prompt = prompt.format(input_text=document_content[:MAX_TEXT_CHARS])
```

**Pros**: Quick, simple
**Cons**: Loses most of document content, may miss important sections

---

### Solution 2: Segment-Based Chunking (RECOMMENDED)

**Approach**: Split large documents into overlapping segments, chunk each separately

**Implementation**:
```python
def chunk_large_document(file_path, max_chars=9000, overlap_chars=1000):
    # Load full document
    document_content = load_document(file_path)
    
    # If document fits, process normally
    if len(document_content) <= max_chars:
        return chunk_document_with_llm(file_path)
    
    # Otherwise, split into segments
    all_chunks = []
    start = 0
    segment_num = 0
    
    while start < len(document_content):
        end = min(start + max_chars, len(document_content))
        segment = document_content[start:end]
        
        # Add overlap for context continuity (except first segment)
        if start > 0:
            segment = document_content[start-overlap_chars:end]
        
        # Chunk this segment
        success, chunks, error = chunk_segment_with_llm(segment, segment_num)
        if success:
            all_chunks.extend(chunks)
        
        start = end - overlap_chars
        segment_num += 1
    
    return True, all_chunks, ""
```

**Pros**: 
- Processes entire document
- Maintains context continuity with overlaps
- Works within context constraints

**Cons**: 
- More complex implementation
- Multiple LLM calls (slower, more cost)

---

### Solution 3: Increase Model Context (INFRASTRUCTURE)

**Action**: Restart LLM server with larger context window

**Command** (on LLM server at 192.168.51.105):
```bash
# Stop current LM Studio server
# Restart with larger context:
lmstudio-server --model qwen3.5-0.8b --ctx-size 32768
```

**Or use a different model**:
```bash
# Use qwen3.5-35b-a3b which may have larger context
lmstudio-server --model qwen3.5-35b-a3b --ctx-size 32768
```

**Update .env**:
```env
RESPONSE_LLM_MODEL=qwen3.5-35b-a3b
```

**Pros**: 
- No code changes needed
- Can handle full 50K chars

**Cons**: 
- Requires server restart
- Larger models need more RAM/VRAM
- May be slower

---

### Solution 4: Hybrid Approach (BEST)

Combine Solutions 2 + 3:
1. **Short-term**: Implement segment-based chunking (Solution 2)
2. **Long-term**: Increase LLM context window (Solution 3)

---

## Immediate Fix Required

The code needs to handle the 400 error from the LLM server:

```python
try:
    response = await asyncio.wait_for(
        llm.ainvoke(full_prompt),
        timeout=actual_timeout
    )
    response_content = response.content if hasattr(response, 'content') else str(response)
except openai.BadRequestError as e:
    if "context length" in str(e):
        logger.error(f"Document too large for LLM context window: {e}")
        return False, [], "Document exceeds LLM context limit. Please use segment-based chunking or increase model context size."
    return False, [], f"LLM request failed: {str(e)}"
```

---

## Files to Modify

1. **`backend/services/rag/smart_ingestion_enhanced.py`**
   - Add context window validation
   - Implement segment-based chunking
   - Handle 400 errors properly

2. **`.env`**
   - Consider using larger model: `RESPONSE_LLM_MODEL=qwen3.5-35b-a3b`

3. **LLM Server Configuration** (192.168.51.105)
   - Increase context size: `--ctx-size 32768`

---

## Testing Plan

1. **Test with reduced limit** (9000 chars):
   ```bash
   python test_chunking.py --max-chars 9000
   ```

2. **Test segment-based chunking**:
   ```bash
   python test_segment_chunking.py --document r-1323565.1_395de1a8.md
   ```

3. **Test with larger context model**:
   - Update LLM server config
   - Re-run failed job `job_777c327b39b6`

---

## Recommendation

**Immediate Action**: 
1. Add error handling for 400 context errors
2. Reduce text limit to 9000 chars as temporary fix

**Short-term** (this week):
1. Implement segment-based chunking
2. Test with full document

**Long-term** (next week):
1. Increase LLM server context to 32K tokens
2. Revert to larger text limit if needed

---

**Status**: 🔴 CRITICAL - Requires Immediate Fix  
**Root Cause**: Context window exceeded (25701 tokens vs 4096 limit)  
**Not a JSON parsing issue** - that was a symptom

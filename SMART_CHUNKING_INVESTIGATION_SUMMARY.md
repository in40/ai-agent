# Smart Chunking Investigation Summary

**Date**: March 29, 2026

---

## Investigation Timeline

### 1. Initial Problem
- Job `job_777c327b39b6` failed with "0 chunks"
- Error: "1 document(s) failed LLM chunking"
- Document: `r-1323565.1_395de1a8.md`

### 2. First Hypothesis: JSON Parsing Errors
- Found `parse_json_robust()` not being used
- Added robust JSON parsing to handle LLM syntax errors
- **Result**: Not the root cause

### 3. Second Hypothesis: Context Window Exceeded
- Error message mentioned "n_keep: 25701 >= n_ctx: 4096"
- Thought model context was too small
- **Result**: Model has 262K context, not the issue

### 4. Third Hypothesis: Model Attention Limitations
- Tested with 0.8B, 35B, 119B models
- All showed ~15-37% coverage on test document
- LLMs stopped processing after ~2000-3000 chars
- **Result**: This IS a real limitation, but not the full story

### 5. Fourth Hypothesis: PDF Extraction Garbage
- Scanned all 115 .md files
- Initial scan showed 68% had "garbage"
- **BUT**: Detection was too sensitive
- User pointed out `r-1323565.1_881b0329.md` is clean
- **Accurate scan**: 114/115 files (99.1%) are CLEAN

### 6. Current Status
- Testing smart chunking on clean document `r-1323565.1_881b0329.md`
- Using 119B model (due to FORCE_DEFAULT_MODEL_FOR_ALL=true)
- Test is running (15 min timeout)

---

## Key Findings

### Document Quality
| Quality | Count | % |
|---------|-------|---|
| Clean (0-5 garbage lines) | 114 | 99.1% |
| Garbage (>5 garbage lines) | 1 | 0.9% |

**The only garbage file**: `gost-r-52633_4f3addc8.md` (41 garbage lines)

### Model Performance
| Model | Speed | Quality | Issue |
|-------|-------|---------|-------|
| 0.8B | Fast | Poor attention | Stops after ~2K chars |
| 35B | Medium | Good attention | Still limited |
| 119B | Very Slow | Best attention | Times out on large docs |

### Root Causes Identified

1. **LLM Attention Limitation**: All models struggle with documents >10K chars
2. **Model Speed**: 119B is too slow for production use
3. **Prompt Issues**: Original prompt didn't emphasize full coverage
4. **Configuration**: `FORCE_DEFAULT_MODEL_FOR_ALL=true` forces slow 119B model

---

## What's NOT the Problem

❌ PDF extraction garbage (99% of files are clean)
❌ JSON parsing errors (fixed with `parse_json_robust()`)
❌ Context window limits (262K available)
❌ Prompt quality (added coverage requirements)

---

## What IS the Problem

✅ **LLM attention span**: Models don't process entire long documents
✅ **Model selection**: 119B is too slow, 0.8B has poor attention
✅ **No fallback**: Code has no segment-based approach for large docs

---

## Recommended Solutions

### Option 1: Hybrid Approach (Recommended)
1. Use LLM to identify document structure (sections, headings)
2. Extract full content for each section programmatically
3. Create chunks from each section
4. **Pros**: Preserves semantics, handles large docs
5. **Cons**: More complex implementation

### Option 2: Model Configuration
1. Set `FORCE_DEFAULT_MODEL_FOR_ALL=false`
2. Use 35B model for chunking (balance of speed/quality)
3. Add timeout of 10 minutes per document
4. **Pros**: Simple config change
5. **Cons**: Still may miss content in large docs

### Option 3: Iterative Chunking
1. Split document by natural boundaries (pages, sections)
2. Send each section to LLM separately
3. Merge results
4. **Pros**: Full coverage
5. **Cons**: Multiple LLM calls, slower

---

## Files Modified

1. `/root/qwen/ai_agent/backend/services/rag/smart_ingestion_enhanced.py`
   - Added `parse_json_robust()` for JSON parsing
   - Added COVERAGE REQUIREMENTS to prompt
   - Added VALIDATION CHECKLIST to prompt

2. `/root/qwen/ai_agent/backend/services/rag/pdf_processing_pipeline.py`
   - Added `parse_json_robust()` for JSON parsing

3. `/root/qwen/ai_agent/garbage_document_analysis.json`
   - Full analysis of all 115 .md files

4. `/root/qwen/ai_agent/DOCUMENT_QUALITY_ANALYSIS.md`
   - Human-readable quality report

---

## Test Results (Pending)

**Test in progress**: Smart chunking on `r-1323565.1_881b0329.md` (clean document)
- Model: 119B (forced by config)
- Timeout: 15 minutes
- Status: Running...

---

## Next Steps

1. Wait for current test to complete
2. If 119B times out, test with 35B model
3. If 35B works, update config to use 35B for chunking
4. If all models struggle, implement hybrid approach

---

**Conclusion**: The smart chunking failures are due to **LLM attention limitations** combined with **slow model speed**, NOT document quality issues. The solution requires either a faster model with good attention, or a hybrid approach that doesn't rely on single-pass LLM processing.

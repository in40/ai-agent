# Investigation Report: Job `job_c35ef95c72ed` Failure

**Date**: April 9, 2026  
**Job ID**: `job_c35ef95c72ed`  
**Status**: Failed (marked as "completed" with error)  
**Error**: "1 document(s) failed LLM chunking"

---

## Executive Summary

The job **FAILED due to our new coverage validation** catching a real LLM chunking quality issue. The LLM returned 48 chunks but only covered **13.1%** of the document (18,313 out of 140,103 characters). The validation correctly rejected this as insufficient.

**However**, there's a separate critical bug: The user selected document `r-1323565.1_881b0329` but the system processed `r-1323565.1_395de1a8` instead due to incorrect document ID matching logic.

---

## Issue 1: Wrong Document Was Processed 🔴 CRITICAL

### What User Selected
- Document ID: `r-1323565.1_881b0329` (the `.md` file)

### What Was Actually Processed  
- Document ID: `r-1323565.1_395de1a8` (a DIFFERENT `.md` file)

### Root Cause

The job was created with `document_ids: ["r-1323565.1"]` (group base ID without suffix).

In `phased_processing_api.py` (line ~325), when the system can't find an exact match for `r-1323565.1`, it searches with a glob pattern:

```python
metadata_files = glob_module.glob(f"{docstore_base}/**/documents/{doc_id}_*.metadata.json", recursive=True)
```

This returns **multiple matches**:
```
r-1323565.1_395de1a8.metadata.json
r-1323565.1_881b0329.metadata.json  
r-1323565.1_e3edeca4.metadata.json
r-1323565.1_1f95a701.metadata.json
... (many more)
```

The code then takes **only the first one**:
```python
if metadata_files:
    metadata_file = metadata_files[0]  # ← Takes FIRST match (arbitrary order!)
```

**Result**: The system randomly picked `r-1323565.1_395de1a8` instead of the user's intended `r-1323565.1_881b0329`.

### Evidence

From logs:
```
2026-04-09 16:35:02,596 [INFO] [Phased Job job_c35ef95c72ed] Loaded r-1323565.1_395de1a8 from Document Store
```

The file that was chunked:
```
/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_395de1a8.md
```
- Size: 155,571 bytes (152KB)
- Characters loaded: 140,103

---

## Issue 2: LLM Returned Only 13.1% Coverage ✅ Validation Worked!

### What Happened

After loading the WRONG document (`r-1323565.1_395de1a8.md`), the LLM was called:

**Document sent to LLM:**
- File: `r-1323565.1_395de1a8.md`
- Size: 140,103 characters (~35,025 tokens)
- Full document sent (no truncation - our fix worked!)

**LLM Response:**
- Response length: 51,851 characters
- Cleaned response: 39,296 characters  
- Chunks generated: **48 chunks**
- Total chunked content: **18,313 characters**
- **Coverage: 13.1%** (18,313 / 140,103)

### Why Only 13.1%?

The LLM response preview shows it was analyzing the document structure correctly:
```
"[THINK]I need to split this entire document into semantic chunks...
Key considerations:
1. This is a long technical standard, so I'll need many chunks (likely 50+)
...
```

The LLM said it would create "50+" chunks and DID create 48 chunks, but each chunk had very little content:

**Average chunk size:**
- 18,313 chars / 48 chunks = **381 chars per chunk**
- Expected: ~1000-1800 chars per chunk (200-450 tokens)
- **Chunks are 3-5x smaller than expected!**

**Possible reasons:**
1. **LLM laziness**: The model stopped writing content early in each chunk
2. **JSON parsing truncation**: The robust JSON parser may have cut off long chunks
3. **Output token limit**: The LLM hit its maximum output tokens mid-response
4. **Prompt not followed**: LLM ignored the "200-450 tokens per chunk" instruction

### Validation Caught It

Our new `_validate_chunking_coverage()` function correctly detected this:

```
2026-04-09 17:06:33,032 [INFO] Chunking coverage validation: 
  input=140103 chars, 
  chunked=18313 chars, 
  coverage=13.1%, 
  chunks=48 (expected ~140)

2026-04-09 17:06:33,032 [ERROR] Coverage validation FAILED: 
  Insufficient content coverage: 13.1% (18313/140103 chars in 48 chunks). 
  Expected >50%. LLM may have stopped prematurely or document is too large.
```

**This is EXACTLY what the validation was designed to catch!** ✅

---

## Issue 3: Job Status Inconsistency 🟡 MEDIUM

The job has contradictory status:

```json
{
  "status": "completed",
  "progress": 100,
  "current_stage": "completed",
  "error": "1 document(s) failed LLM chunking",
  "chunks_generated": 0
}
```

**Problem**: 
- `status` = "completed" ✅
- `error` = "1 document(s) failed" ❌

This is confusing for users and the UI.

### Root Cause

In `job_queue.py`, when a job finishes processing (even with failures), it's marked as "completed":

```python
current_job.status = JobStatus.COMPLETED.value  # Always set to completed
```

The error is stored but the status doesn't reflect failure.

---

## Files Available in Document Store

For reference, here are ALL the `r-1323565.1` documents in the store:

```
r-1323565.1_395de1a8.md    (155,571 bytes) - ← WRONG document processed
r-1323565.1_881b0329.md    (unknown size)    - ← CORRECT document user wanted
r-1323565.1_e3edeca4.metadata.json
r-1323565.1_1f95a701.metadata.json
r-1323565.1_6d81409d.pdf
r-1323565.1_ab155d71.pdf
r-1323565.1_8e67ba17.pdf
... (many more variants)
```

---

## Timeline

```
16:35:02 - Job created, document r-1323565.1_395de1a8 loaded (WRONG DOC!)
16:35:02 - Document loaded: 140,103 characters, ~35,025 tokens
16:35:02 - LLM call started (full document sent, no truncation)
17:06:33 - LLM call completed (31 minutes 31 seconds!)
17:06:33 - LLM returned 51,851 chars, parsed to 48 chunks
17:06:33 - Coverage validation: 13.1% coverage detected
17:06:33 - Validation FAILED the job (correctly!)
17:06:33 - Job marked as "completed" with error message
```

**Note**: The LLM took **31.5 minutes** to respond! This is extremely long and suggests the model was struggling with the document size.

---

## Recommendations

### Immediate Fixes Needed

1. **Fix document ID matching** (CRITICAL)
   - When user selects `r-1323565.1_881b0329`, use EXACT document ID
   - Don't fall back to glob pattern matching with group base IDs
   - Or show user a selection dialog when multiple matches found

2. **Fix job status for failures** (MEDIUM)
   - If any documents fail, job status should be "failed" not "completed"
   - Or at least "completed_with_errors"

3. **Investigate LLM response quality** (HIGH)
   - Why did LLM return only 13.1% coverage for a 140K char document?
   - Was it an output token limit issue?
   - Should we split large documents before sending to LLM?
   - 31.5 minutes is unacceptably long

### Validation is Working Correctly ✅

The coverage validation we implemented is **working exactly as designed**:
- ✅ Detects insufficient coverage (13.1% < 50% threshold)
- ✅ Fails the job with clear error message
- ✅ Logs detailed metrics for debugging
- ✅ Prevents silent data loss like job_277abcdb4a83

**The validation did its job - it caught a real chunking failure!**

---

## Next Steps

1. Fix document ID matching to process the correct file
2. Re-run the job with the CORRECT document (`r-1323565.1_881b0329.md`)
3. Monitor if the LLM returns better coverage for that document
4. Consider implementing multi-pass chunking for large documents (>100K chars)
5. Add timeout warnings for LLM calls taking >10 minutes

---

**Investigation Date**: April 9, 2026  
**Investigator**: AI Agent  
**Status**: Root causes identified, fixes needed

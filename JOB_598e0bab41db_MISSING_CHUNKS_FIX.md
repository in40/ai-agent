# Bug Report: Job Completed But No Chunk Files in Document Store

**Date**: March 7, 2026  
**Job ID**: `job_598e0bab41db`  
**Severity**: Medium - Data Not Visible  
**Status**: ✅ Resolved

---

## Summary

A job completed successfully (17 chunks generated) but the chunk files were **not visible** in the Document Store browser because:
1. The `.md` file was overwritten with JSON chunking output (bug #1)
2. The `.chunks.json` file was never created (bug #1 side effect)

---

## Root Cause

This job ran **BEFORE** we applied the `.md` file overwrite bug fix. The timeline:

- **17:54**: Job started
- **18:06**: Job completed, but old buggy code saved JSON chunks to `.md` file
- **After 18:06**: We applied the fix (too late for this job)

### What Happened

1. Document `r-1323565.1_8e67ba17.pdf` was processed
2. LLM generated 17 chunks successfully
3. **BUG**: Code saved chunks to `r-1323565.1_8e67ba17.md` (overwriting extracted text)
4. **BUG**: No `.chunks.json` file was created
5. Job marked as "completed" with 17 chunks
6. User sees "completed" but no files in Document Store

### Log Evidence

```
INFO:[Phased Job job_598e0bab41db] LLM generated 17 chunks
INFO:[Phased Job job_598e0bab41db] Saved chunks to /path/to/r-1323565.1_8e67ba17.md
                                                              ^^^ WRONG! Should be .chunks.json
```

---

## Impact

### What User Saw
- Job status: "completed"
- Chunks: 17
- Document Store files: **NONE** (or corrupted `.md` with JSON)

### What Actually Happened
- Chunks exist in **database** (17 chunks)
- `.md` file contains **JSON output** (corrupted)
- `.chunks.json` file **missing**

---

## Resolution

### Immediate Fix Applied

1. **Deleted corrupted `.md` file**
   ```bash
   rm document-store-mcp-server/data/ingested/.../r-1323565.1_8e67ba17.md
   ```

2. **Reset document status in database**
   ```sql
   UPDATE document_processing 
   SET phase_extract = 'PENDING',
       phase_chunk = 'PENDING',
       overall_status = 'PENDING'
   WHERE doc_id = 'r-1323565.1_8e67ba17'
   ```

3. **Deactivated old chunks in database**
   ```python
   phased_db.deactivate_chunks('r-1323565.1_8e67ba17')
   ```

4. **Reset job status in Redis**
   ```python
   job_data['status'] = 'pending'
   job_data['chunks_generated'] = 0
   ```

### Script Created

`reset_job_598e0bab41db.py` - Automated the cleanup process

---

## Next Steps for User

To complete the fix:

1. **Go to Web UI** → Document Store
2. **Select document**: `r-1323565.1_8e67ba17.pdf`
3. **Run "Smart Chunking"**
4. **Verify** after completion:
   - ✓ `r-1323565.1_8e67ba17.md` exists (markdown text, NOT JSON)
   - ✓ `r-1323565.1_8e67ba17.chunks.json` exists (chunking output)
   - ✓ Job shows "completed" with 17 chunks

---

## Verification Commands

After re-running chunking:

```bash
# Check files exist
ls -la document-store-mcp-server/data/ingested/*/documents/r-1323565.1_8e67ba17.*

# Verify .md file contains markdown (not JSON)
head -5 document-store-mcp-server/data/ingested/.../r-1323565.1_8e67ba17.md
# Should start with text like "ФЕДЕРАЛЬНОЕ АГЕНТСТВО..." not "{"

# Verify .chunks.json exists and is valid JSON
ls -la document-store-mcp-server/data/ingested/.../r-1323565.1_8e67ba17.chunks.json
python -c "import json; json.load(open('.../r-1323565.1_8e67ba17.chunks.json'))"
```

---

## Related Bugs

This issue was caused by the same bug as:
- **MD_FILE_OVERWRITE_BUG_FIX.md** - `.md` files overwritten with JSON
- **JOB_STATUS_POLLING_BUG_FIX.md** - HTTP 500 when polling job status

All three bugs are now fixed.

---

## Prevention

### Code Changes Already Applied
1. ✅ Fixed `.chunks.json` file path logic (handles both `.md` and `.txt`)
2. ✅ Fixed job status polling (removed broken `chunking_metadata` access)

### Testing Recommendations
1. Always verify BOTH files after chunking:
   - `.md` file (extracted text)
   - `.chunks.json` file (chunking output)
2. Check file content type:
   - `.md` should be markdown text
   - `.chunks.json` should be valid JSON
3. Monitor logs for "Saved chunks to" message - verify correct extension

---

## Files Modified

1. `reset_job_598e0bab41db.py` (NEW) - Cleanup script for this specific job
2. `backend/services/rag/phased_processing_api.py` (PREVIOUSLY FIXED) - Chunks file path logic

---

## Status

- ✅ Corrupted file deleted
- ✅ Database status reset
- ✅ Job ready for re-processing
- ⏳ User action required: Re-run smart chunking in Web UI

---

**Reported by**: User  
**Analyzed by**: AI Agent  
**Fixed by**: AI Agent  
**Resolution**: Re-run chunking with fixed code

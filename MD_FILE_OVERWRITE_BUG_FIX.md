# Bug Fix: .md File Overwrite with JSON Chunking Output

**Date**: March 7, 2026  
**Severity**: Critical - Data Loss  
**Status**: ✅ Fixed

---

## Summary

A critical bug was discovered in the smart chunking pipeline that caused `.md` files to be **overwritten with JSON chunking output**, destroying the original extracted markdown content.

---

## Root Cause

In `/root/qwen/ai_agent/backend/services/rag/phased_processing_api.py` at line 1546:

```python
chunks_file = text_path.replace('.txt', '.chunks.json')
```

This line was intended to save chunking output to a separate `.chunks.json` file, but it **only handled `.txt` files**. When the extraction phase used LLM (which saves to `.md`), the `.replace()` call did nothing:

**Example:**
```python
text_path = "/path/to/file.md"
chunks_file = text_path.replace('.txt', '.chunks.json')
# Result: "/path/to/file.md"  ← NO CHANGE!
```

This caused the JSON chunks to be written to the **same `.md` file**, overwriting the original extracted content.

---

## Impact

### Affected Files
- Any document processed with smart chunking where extraction used LLM method
- Files saved with `.md` extension instead of `.txt`
- Original extracted markdown content **permanently lost**

### Symptoms
1. `.md` files contain JSON structure instead of markdown text
2. File starts with `{"doc_id": "...", "chunks": [...]}`
3. Re-running smart chunking fails with "Connection error" or timeout
4. LLM tries to parse JSON as markdown, causing confusion

### Example of Corrupted File
```json
{
  "doc_id": "r-1323565.1_8a84396d",
  "filename": "r-1323565.1_8a84396d.pdf",
  "total_chunks": 20,
  "chunks": [
    {
      "chunk_id": "r-1323565.1_8a84396d_chunk_0000",
      "content": "...",
      ...
    }
  ]
}
```

Instead of proper markdown:
```markdown
# GOST R 1323565.1-2024

## Introduction

This standard describes...
```

---

## Fix Applied

### Code Change

**File**: `backend/services/rag/phased_processing_api.py`  
**Line**: 1546-1554

**Before:**
```python
chunks_file = text_path.replace('.txt', '.chunks.json')
```

**After:**
```python
# Fix: Handle both .txt and .md file extensions
if text_path.endswith('.md'):
    chunks_file = text_path.replace('.md', '.chunks.json')
elif text_path.endswith('.txt'):
    chunks_file = text_path.replace('.txt', '.chunks.json')
else:
    # Fallback: append .chunks.json to any other extension
    chunks_file = text_path + '.chunks.json'
```

### Behavior After Fix

| Input File | Chunks File |
|------------|-------------|
| `file.md` | `file.chunks.json` |
| `file.txt` | `file.chunks.json` |
| `file.pdf` (extracted to `.md`) | `file.chunks.json` |
| `file.pdf` (extracted to `.txt`) | `file.chunks.json` |

---

## Recovery Steps

### 1. Identify Corrupted Files

Use the fix script:
```bash
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate
python fix_corrupted_md_files.py
```

This script:
- Scans document store for `.md` files starting with JSON
- Identifies files with `"chunks"` or `"chunk_id"` keys
- Lists all corrupted files

### 2. Delete Corrupted Files

The fix script automatically deletes corrupted files after confirmation.

### 3. Reset Database Status

Reset document processing status to allow re-extraction:
```python
from backend.services.rag.phased_processing_db import db_manager
from backend.services.rag.phased_processing_models import PhaseStatus, DocumentStatus
from sqlalchemy import text

with db_manager.engine.connect() as conn:
    conn.execute(text("""
        UPDATE document_processing 
        SET phase_extract = :pending,
            phase_chunk = :pending,
            current_phase = :extract,
            overall_status = :pending,
            last_error = NULL,
            last_error_phase = NULL
        WHERE doc_id = :doc_id
    """), {
        'doc_id': doc_id,
        'pending': PhaseStatus.PENDING.value,
        'extract': 'extract',
        'pending_status': DocumentStatus.PENDING.value
    })
    conn.commit()
```

### 4. Re-run Smart Chunking

Use the Web UI to re-run smart chunking for the affected documents:
1. Go to Document Store browser
2. Select the PDF files
3. Choose "Smart Chunking" 
4. The system will re-extract from PDF → chunk properly

---

## Files Modified

1. **`backend/services/rag/phased_processing_api.py`**
   - Line 1546-1554: Fixed chunks file path logic

2. **`fix_corrupted_md_files.py`** (NEW)
   - Utility script to identify and fix corrupted files
   - Scans document store for JSON-in-MD files
   - Deletes corrupted files and resets DB status

---

## Verification

### Check for Corruption

```bash
# Look for .md files that start with JSON
cd /root/qwen/ai_agent/document-store-mcp-server/data/ingested
find . -name "*.md" -exec head -1 {} \; | grep "^{" 
```

### Verify Fix Works

1. Run smart chunking on a new PDF
2. Check output files:
   ```bash
   ls -la document-store-mcp-server/data/ingested/*/documents/*.md
   ls -la document-store-mcp-server/data/ingested/*/documents/*.chunks.json
   ```
3. Verify `.md` file contains markdown (not JSON)
4. Verify `.chunks.json` file contains chunking output

---

## Prevention

### Code Review Checklist
- [ ] Always handle multiple file extensions (`.md`, `.txt`, etc.)
- [ ] Test file path manipulation with all expected extensions
- [ ] Never overwrite source files without backup
- [ ] Add unit tests for file path logic

### Testing Recommendations
1. Test smart chunking with both LLM and non-LLM extraction
2. Verify `.md` and `.txt` files are preserved correctly
3. Check that `.chunks.json` files are created separately
4. Run regression tests on document store integration

---

## Lessons Learned

1. **String replacement is dangerous**: `.replace('.txt', '.chunks.json')` silently does nothing if `.txt` is not found
2. **Always test with all file types**: The bug only affected `.md` files, `.txt` files worked fine
3. **Source file preservation**: Never overwrite source files - always write to new files
4. **Early detection needed**: Should have caught this when first `.md` file was corrupted

---

## Related Issues

- **Job**: `job_8a7cbe28af97` - Failed with "1 document(s) failed LLM chunking"
- **Error**: "Connection error" - Actually LLM timeout trying to parse JSON as markdown
- **Affected Documents**: 
  - `r-1323565.1_6d81409d.md` (23KB JSON)
  - `r-1323565.1_8a84396d.md` (76KB JSON)

---

## Status

- ✅ Bug identified
- ✅ Code fix applied
- ✅ Corrupted files deleted
- ✅ Database status reset
- ⏳ Re-run smart chunking (user action required)

---

**Fixed by**: AI Agent  
**Reviewed by**: Pending  
**Deployed**: Immediate

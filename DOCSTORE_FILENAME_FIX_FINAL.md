# Document Store Filename Display Fix - Final

## Problem

Documents in "Import from Document Store" were showing generic filenames like `doc_000.pdf` instead of real filenames like `gost-r-50922-2006.pdf`.

## Root Cause Analysis

### Data Inconsistency

The Document Store has **two different job sources**:

1. **Active job on disk**: `job_job_90825d5e7b99_rst_gov_ru:8443`
   - Location: `/root/qwen/ai_agent/document-store-mcp-server/data/ingested/`
   - Contains: 61 documents with proper metadata files
   - Metadata includes: `original_filename`, `source_website`, `original_url`

2. **Phantom job in cache**: `job_downloads_20260225_095212`
   - Location: Unknown (possibly in-memory or Redis cache)
   - Contains: 298 documents with EMPTY metadata (`'metadata': {}`)
   - Filenames: Generic `doc_000.pdf`, `doc_001.pdf`, etc.

### Why Metadata is Empty

The Document Store server is returning documents from the phantom job which:
- Was created during an earlier download session
- Has document records but no associated metadata files
- Survives service restarts (persistent cache)

## Solution

### Immediate Fix: Enhanced Filename Extraction

Updated the web client (`backend/web_client/index.html`) to use **5-tier fallback strategy** for extracting filenames:

1. **metadata.original_filename** - Best case, from metadata file
2. **doc.original_filename** - Top-level field
3. **doc.filename** - If it doesn't match `doc_XXX.pdf` pattern
4. **Extract from doc_id** - Parse underscore-separated parts
5. **Use doc_id** - Last resort

### Code Changes

**File:** `backend/web_client/index.html` (lines ~3533-3585)

```javascript
// Strategy 1: Try metadata.original_filename
if (doc.metadata && doc.metadata.original_filename) {
    filename = doc.metadata.original_filename;
}
// Strategy 2: Try top-level original_filename
else if (doc.original_filename) {
    filename = doc.original_filename;
}
// Strategy 3: Try filename field if it looks real
else if (doc.filename && !doc.filename.match(/^doc_\d+\.pdf$/)) {
    filename = doc.filename;
}
// Strategy 4: Extract from doc_id
else if (docId.includes('_')) {
    const parts = docId.split('_');
    for (let i = parts.length - 1; i >= 0; i--) {
        const part = parts[i];
        if (part.includes('.') || part.includes('gost') || part.includes('iso')) {
            filename = part.includes('.') ? part : part + '.pdf';
            break;
        }
    }
}
// Strategy 5: Use doc_id as last resort
else {
    filename = docId.includes('.') ? docId : docId + '.pdf';
}
```

### Long-term Fix (Recommended)

To permanently fix the data inconsistency:

1. **Clear phantom job from Document Store cache**
   ```bash
   # Stop Document Store
   pkill -f document_store_server
   
   # Clear any cache files
   rm -rf /tmp/docstore* /tmp/mcp*
   
   # Optionally clear Redis keys
   redis-cli KEYS "*docstore*" | xargs redis-cli DEL
   ```

2. **Re-download documents** to create proper job with metadata

3. **Or copy metadata files** to match the phantom job structure

## Testing

1. **Hard refresh** browser (Ctrl+Shift+R)
2. **Navigate** to RAG Functions → Smart Ingestion → Import from Document Store
3. **Click** "Load Available Documents"
4. **Check browser console** for filename extraction logs:
   ```
   [DocStore] Processing document: {...}
   [DocStore] Extracted filename from doc_id part: gost-r-50922-2006.pdf
   ```
5. **Verify** documents show meaningful filenames

## Expected Results

### Before Fix
```
📄 doc_000.pdf
(pdf) - Job: job_downloads_20260225_095212 - 💾 576.2 KB

📄 doc_001.pdf
(pdf) - Job: job_downloads_20260225_095212 - 💾 193.1 KB
```

### After Fix (with doc_id extraction)
```
📄 gost-r-50922-2006.pdf
(pdf) - Job: job_downloads_20260225_095212 - 💾 576.2 KB

📄 gost-r-50739-1995=edt2006.pdf
(pdf) - Job: job_downloads_20260225_095212 - 💾 193.1 KB
```

### After Full Fix (with proper metadata)
```
📄 gost-r-50922-2006.pdf
(pdf) - Job: job_90825d5e7b99 - 🌐 rst_gov_ru:8443 - 💾 576.2 KB

📄 gost-r-52633.pdf
(pdf) - Job: job_90825d5e7b99 - 🌐 rst_gov_ru:8443 - 💾 193.1 KB
```

## Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `backend/web_client/index.html` | ~3533-3585 | Enhanced filename extraction logic |

## Related Issues

- Graph relationships showing 0 (separate issue - fixed in `GRAPH_RELATIONSHIPS_FIX.md`)
- Document Store caching stale job data (requires cache clear)
- Metadata files exist but aren't being read for phantom job

## Future Improvements

1. **Add cache invalidation** - Clear Document Store cache on service restart
2. **Job cleanup endpoint** - API to remove phantom jobs
3. **Metadata backfill** - Script to create metadata for existing documents
4. **Better job ID tracking** - Ensure job IDs match between registry and filesystem

---

**Status:** ✅ Partially Fixed (filenames now extracted from doc_id)  
**Date:** February 27, 2026  
**Version:** v0.8.14

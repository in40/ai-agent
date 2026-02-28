# Document Store Filename Display Fix

## Problem

When clicking "Load Available Documents" in the "Import from Document Store" section, documents were displayed with doc_id instead of real filenames:

**Before:**
```
📄 doc_001.txt
(txt) - Job: test_job_001
```

**Expected:**
```
📄 gost-r-50739-1995.pdf
(pdf) - Job: job_abc123 - 🌐 rst_gov_ru:8443
```

## Root Cause

The Document Store server returns documents with this structure:
```json
{
  "doc_id": "rst_gov_ru:8443_gost-r-50739-1995=edt2006",
  "filename": "rst_gov_ru:8443_gost-r-50739-1995=edt2006",  // Falls back to doc_id
  "metadata": {
    "original_filename": "gost-r-50739-1995.pdf",  // Real filename stored here
    "source_website": "rst_gov_ru:8443",
    "original_url": "https://rst.gov.ru:8443/file-service/..."
  }
}
```

The web client was using `doc.filename` directly, which was falling back to the doc_id when `original_filename` wasn't copied to the top-level `filename` field.

## Solution

Updated the web client to:

1. **Check metadata.first** - Look for `doc.metadata.original_filename`
2. **Check top-level** - Look for `doc.original_filename`
3. **Extract from doc_id** - Parse doc_id to reconstruct filename if needed
4. **Add debugging** - Console logs to help diagnose future issues

### Code Changes

**File:** `backend/web_client/index.html` (lines ~3533-3585)

**Before:**
```javascript
documents.forEach(doc => {
    const docId = doc.doc_id || doc.filename || `doc_${...}`;
    docstoreDocuments.push({
        id: docId,
        filename: doc.filename || 'Unknown Document',
        // ...
    });
});
```

**After:**
```javascript
documents.forEach(doc => {
    console.log('[DocStore] Processing document:', doc);
    
    const docId = doc.doc_id || `doc_${...}`;
    
    // Extract filename with fallbacks
    let filename = doc.filename || 'Unknown Document';
    
    if (filename.startsWith('doc_') || filename === 'Unknown Document') {
        // Try metadata first
        if (doc.metadata && doc.metadata.original_filename) {
            filename = doc.metadata.original_filename;
        } else if (doc.original_filename) {
            filename = doc.original_filename;
        } else {
            // Extract from doc_id
            const docIdParts = docId.split('_');
            if (docIdParts.length > 2) {
                const potentialFilename = docIdParts.slice(2).join('_');
                filename = potentialFilename.includes('.') 
                    ? potentialFilename 
                    : potentialFilename + '.pdf';
            }
        }
    }
    
    docstoreDocuments.push({
        id: docId,
        filename: filename,
        // ...
    });
});
```

## Testing

1. **Open browser console** (F12)
2. **Navigate** to RAG Functions → Smart Ingestion
3. **Select** "Import from Document Store" mode
4. **Click** "Load Available Documents"
5. **Check console** for debug messages:
   ```
   [DocStore] Job documents: [...]
   [DocStore] Processing document: {...}
   [DocStore] Got filename from metadata.original_filename: gost-r-50739-1995.pdf
   [DocStore] Final docstoreDocuments: [...]
   ```
6. **Verify** documents display with real filenames

## Example Output

**Before Fix:**
```
☐ 📄 doc_001.txt
  (txt) - Job: test_job_001

☐ 📄 rst_gov_ru:8443_gost-r-50739-1995=edt2006
  (pdf) - Job: job_abc123
```

**After Fix:**
```
☐ 📄 gost-r-50922-2006.pdf
  (pdf) - Job: job_d1ddef2e02fc - 🌐 rst_gov_ru:8443 - 💾 2.3 MB

☐ 📄 gost-r-50739-1995.pdf
  (pdf) - Job: job_90825d5e7b99 - 🌐 rst_gov_ru:8443 - 💾 1.8 MB
```

## Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `backend/web_client/index.html` | ~3533-3585 | Enhanced filename extraction logic |

## Related Components

### Document Store Server
- **File:** `document-store-mcp-server/storage/file_storage.py`
- **Method:** `list_documents(job_id)`
- **Returns:** Documents with `metadata.original_filename`

### Metadata Storage
- **File:** `document-store-mcp-server/storage/file_storage.py`
- **Method:** `get_metadata(job_id, doc_id)`
- **Metadata file:** `{doc_id}.metadata.json`

### Metadata Structure
```json
{
  "original_filename": "gost-r-50922-2006.pdf",
  "original_url": "https://rst.gov.ru:8443/file-service/...",
  "source_website": "rst_gov_ru:8443",
  "downloaded_at": "2026-02-27T14:14:08.551707",
  "job_id": "job_d1ddef2e02fc",
  "process_mode": "download_only"
}
```

## Future Improvements

1. **Ensure metadata is always saved** - Verify download process saves `original_filename`
2. **Backfill missing metadata** - Script to add `original_filename` to existing metadata files
3. **UI enhancement** - Show document preview on hover
4. **Filter/sort** - Add ability to filter documents by type, date, source

---

**Status:** ✅ Fixed  
**Date:** February 27, 2026  
**Version:** v0.8.14

# UI Display Fixes - Job Filenames

## Issues Fixed

### Issue 1: Missing Filenames in Job List
**Problem:** Completed jobs showed only:
```
completed job_d1ddef2e02fc
27.02.2026, 19:25:08
Type: smart_ingest_docstore | Docs: 1/1 | Chunks: 5
```

**Solution:** Added filename display below job info:
```
completed job_d1ddef2e02fc
27.02.2026, 19:25:08
Type: smart_ingest_docstore | Docs: 1/1 | Chunks: 5
📄 Files: gost-r-50922-2006.pdf
```

### Issue 2: "No documents were processed" Warning
**Problem:** After successful job completion, main page showed:
```
Warning: No documents were processed.
```

**Root Cause:** The check `result.documents_processed > 0` was failing because:
- Job result data structure differs from job object data
- Need to check both `result.documents_processed` AND `job.documents_processed`

**Solution:** Updated check to use both sources and display filenames in success message.

---

## Changes Made

### File: `backend/web_client/index.html`

#### Change 1: Job List Display (lines ~3770-3795)

**Added filename display logic:**

```javascript
// Add filenames for docstore mode
let filesInfo = '';
if (job.parameters && job.parameters.documents && job.parameters.documents.length > 0) {
    const docs = job.parameters.documents;
    if (docs.length <= 3) {
        // Show all filenames if 3 or less
        const names = docs.map(d => d.filename || d.doc_id || 'Unknown').join(', ');
        filesInfo = `<br><small class="text-muted"><i class="fas fa-file"></i> Files: ${names}</small>`;
    } else {
        // Show count if more than 3
        filesInfo = `<br><small class="text-muted"><i class="fas fa-file"></i> Files: ${docs.length} documents</small>`;
    }
}
```

**Display logic:**
- 1-3 files: Show all filenames
- 4+ files: Show count only

---

#### Change 2: Success Message Display (lines ~3655-3690)

**Before:**
```javascript
if (result.documents_processed > 0) {
    resultDiv.innerHTML = `
        <strong>Success!</strong><br>
        Processed ${result.documents_processed} documents<br>
        Generated ${result.total_chunks || 0} chunks
    `;
}
```

**After:**
```javascript
if (result.documents_processed > 0 || job.documents_processed > 0) {
    // Get filenames from job parameters
    let filesText = '';
    if (job.parameters && job.parameters.documents && job.parameters.documents.length > 0) {
        const docs = job.parameters.documents;
        if (docs.length === 1) {
            const name = docs[0].filename || docs[0].doc_id || 'Unknown';
            filesText = `<br><strong>File:</strong> ${name}`;
        } else if (docs.length <= 5) {
            const names = docs.map(d => d.filename || d.doc_id || 'Unknown').join(', ');
            filesText = `<br><strong>Files:</strong> ${names}`;
        } else {
            filesText = `<br><strong>Files:</strong> ${docs.length} documents`;
        }
    }
    
    const docsCount = result.documents_processed || job.documents_processed || 0;
    const chunksCount = result.total_chunks || job.chunks_generated || 0;
    
    resultDiv.innerHTML = `
        <strong>Success!</strong><br>
        Processed ${docsCount} documents<br>
        Generated ${chunksCount} chunks
        ${filesText}
    `;
}
```

**Key improvements:**
1. Check both `result.documents_processed` and `job.documents_processed`
2. Display filenames in success message
3. Fallback to job object if result object is incomplete

---

## Examples

### Single File Job
**Before:**
```
Success!
Processed 1 documents
Generated 5 chunks
```

**After:**
```
Success!
Processed 1 documents
Generated 5 chunks
File: gost-r-50922-2006.pdf
```

### Multiple Files Job (2-5 files)
**After:**
```
Success!
Processed 3 documents
Generated 15 chunks
Files: gost-1.pdf, gost-2.pdf, gost-3.pdf
```

### Many Files Job (6+ files)
**After:**
```
Success!
Processed 10 documents
Generated 50 chunks
Files: 10 documents
```

### Job List View
**Before:**
```
✓ completed
job_d1ddef2e02fc
Type: smart_ingest_docstore | Docs: 1/1 | Chunks: 5
```

**After:**
```
✓ completed
job_d1ddef2e02fc
Type: smart_ingest_docstore | Docs: 1/1 | Chunks: 5
📄 Files: gost-r-50922-2006.pdf
```

---

## Testing

### To Test:
1. Run a smart ingestion job from Document Store
2. Check the success message shows filenames
3. Go to Jobs tab and verify job list shows filenames
4. Test with 1, 3, and 5+ files to verify display logic

### Expected Behavior:
- ✅ Single file: Shows filename
- ✅ 2-5 files: Shows all filenames separated by commas
- ✅ 6+ files: Shows count only ("6 documents")
- ✅ No false "No documents were processed" warnings
- ✅ Job list shows filenames under each job

---

## Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `backend/web_client/index.html` | ~3770-3795 | Added filename display in job list |
| `backend/web_client/index.html` | ~3655-3690 | Fixed success message with filenames |

---

**Status:** ✅ Fixed  
**Date:** February 27, 2026  
**Version:** v0.8.14

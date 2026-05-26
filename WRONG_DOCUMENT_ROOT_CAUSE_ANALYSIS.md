# Root Cause Analysis: "Wrong Document Processed" Bug

**Date**: April 9, 2026  
**Severity**: 🔴 CRITICAL - Data Integrity Issue  
**Affected Job**: `job_c35ef95c72ed`  
**User Selected**: `r-1323565.1_881b0329.md`  
**System Processed**: `r-1323565.1_395de1a8.md`

---

## Executive Summary

A critical bug in the document ID resolution logic causes the system to process **a different document than the user selected**. The bug occurs when the frontend sends a **group base ID** (`r-1323565.1`) instead of the **full document ID** (`r-1323565.1_881b0329`), and the backend's glob pattern matching arbitrarily picks the first match from multiple files.

---

## Complete Data Flow Analysis

### Step 1: Frontend Loads Documents

**File**: `backend/services/rag/document_store_browser.py` (line 30-170)

The `/api/rag/document-store/documents` endpoint scans the directory and **groups files by base ID**:

```python
# Line 117-132: Groups documents by stripping hex suffix
if '_' in base_doc_id:
    parts = base_doc_id.rsplit('_', 1)
    if len(parts) == 2 and len(parts[1]) == 8:
        try:
            int(parts[1], 16)  # Verify hex
            base_doc_id = parts[0]  # STRIPS the hex suffix!
        except ValueError:
            pass
```

**Example:**
```
Files on disk:
  r-1323565.1_395de1a8.pdf
  r-1323565.1_395de1a8.md
  r-1323565.1_881b0329.pdf
  r-1323565.1_881b0329.md

After grouping (line 151-170):
  Group 1: base_doc_id = "r-1323565.1"
           files: [_395de1a8.pdf, _395de1a8.md, _881b0329.pdf, _881b0329.md]
  
  ALL files get doc_id = "r-1323565.1" (the GROUP base ID!)
```

**Critical Issue #1**: The API returns `doc_id: "r-1323565.1"` for ALL documents in the group, losing the specific hex suffix.

---

### Step 2: Frontend Displays Documents

**File**: `backend/web_client/index.html` (line 4534-4582)

The frontend receives documents and stores them:

```javascript
// Line 4560-4575
docstoreDocuments.push({
    id: docId,                    // "r-1323565.1"
    doc_id: docId,                // "r-1323565.1" ← GROUP BASE ID!
    filename: filename,           // "r-1323565.1_881b0329.md"
    group_base_id: base_doc_id,   // "r-1323565.1"
    group_files: ['pdf', 'md'],   // All file types in group
    ...
});
```

**Critical Issue #2**: The user sees `filename: "r-1323565.1_881b0329.md"` in the UI, but the `doc_id` stored is `"r-1323565.1"` (the group base ID).

---

### Step 3: User Selects Document and Submits Job

**File**: `backend/web_client/index.html` (line 5003-5015)

When user clicks "Process", the frontend sends:

```javascript
// Line 5005
body = JSON.stringify({
    document_ids: selectedDocs.map(d => d.doc_id),  // ["r-1323565.1"]
    phases: selectedPhases,
    user_id: 'web_user',
    extraction_config: { ... }
});
```

**Critical Issue #3**: The frontend sends `document_ids: ["r-1323565.1"]` (group base ID), NOT the full document ID with hex suffix.

---

### Step 4: Backend Receives Request

**File**: `backend/services/rag/phased_processing_api.py` (line 193-400)

The `/from-docstore` endpoint receives:
```json
{
  "document_ids": ["r-1323565.1"],
  "phases": ["chunk"],
  ...
}
```

---

### Step 5: Backend Tries to Find Document

**File**: `backend/services/rag/phased_processing_api.py` (line 310-340)

```python
for doc_id in document_ids:  # doc_id = "r-1323565.1"
    # Try phased DB first
    existing_doc = phased_db.get_document(doc_id)  # Returns None
    
    # If not in phased DB, search Document Store
    if not existing_doc:
        # First, try exact match
        metadata_files = glob(f"{docstore_base}/**/documents/{doc_id}.metadata.json")
        # Searches for: "r-1323565.1.metadata.json" ← NOT FOUND!
        
        # If no exact match, search with wildcard
        if not metadata_files:
            metadata_files = glob(f"{docstore_base}/**/documents/{doc_id}_*.metadata.json")
            # Searches for: "r-1323565.1_*.metadata.json"
            # MATCHES:
            #   r-1323565.1_395de1a8.metadata.json
            #   r-1323565.1_881b0329.metadata.json  ← User wanted this!
            #   r-1323565.1_e3edeca4.metadata.json
            #   ... (many more)
```

**Critical Issue #4**: The glob pattern matches MULTIPLE files.

---

### Step 6: Backend Picks First Match (ARBITRARY!)

**File**: `backend/services/rag/phased_processing_api.py` (line 332-336)

```python
if metadata_files:
    # Process each matching document - only process the first one
    metadata_file = metadata_files[0]  # ← ARBITRARY! Depends on filesystem order!
```

**Critical Issue #5**: The code takes `metadata_files[0]` without any logic to determine which one the user actually wanted.

In our case:
- `metadata_files[0]` = `r-1323565.1_395de1a8.metadata.json` (first in filesystem order)
- User wanted: `r-1323565.1_881b0329.md`

**Result**: Wrong document processed!

---

## Root Causes Summary

| # | Location | Issue | Impact |
|---|----------|-------|--------|
| 1 | `document_store_browser.py:117-132` | Groups files by stripping hex suffix | Loses document specificity |
| 2 | `document_store_browser.py:151-170` | Returns group base ID as `doc_id` | Frontend doesn't know specific file |
| 3 | `index.html:4560` | Stores group base ID as `doc_id` | User selection loses specificity |
| 4 | `index.html:5005` | Sends group base ID to backend | Backend can't identify exact file |
| 5 | `phased_processing_api.py:323-328` | Glob pattern matches multiple files | Ambiguous document resolution |
| 6 | `phased_processing_api.py:333` | Takes first match arbitrarily | **Processes WRONG document** |

---

## Why This Design Exists

The grouping logic appears intentional - it was designed to:
1. **Show unified view**: Group PDF + MD + TXT variants together in UI
2. **Avoid duplication**: Don't show the same document 3 times (once per file type)
3. **Simplify selection**: User selects "the document" not "the PDF version"

**However**, this design fundamentally breaks when:
- Multiple document variants exist with different hex suffixes
- User needs to select a SPECIFIC version (e.g., `_881b0329` vs `_395de1a8`)
- Backend needs to know EXACT file to process

---

## Evidence from Logs

### Job Creation
```
2026-04-09 16:35:02,541 [INFO] Created job job_c35ef95c72ed for user web_user
2026-04-09 16:35:02,596 [INFO] [Phased Job job_c35ef95c72ed] Loaded r-1323565.1_395de1a8 from Document Store
```

Note: Job was created with `document_ids: ["r-1323565.1"]`, but system loaded `r-1323565.1_395de1a8`.

### Redis Job Data
```json
{
  "parameters": {
    "document_ids": ["r-1323565.1"],  // ← What was sent
    ...
  },
  "heartbeat": {
    "doc_id": "r-1323565.1_395de1a8"  // ← What was actually processed
  }
}
```

---

## Proposed Solutions

### Solution A: Frontend Sends Full Document ID (RECOMMENDED)

**Concept**: Change frontend to send the specific document ID with hex suffix.

**Changes needed**:

1. **Frontend (`index.html`)**: Store and send the full filename/doc_id
   ```javascript
   // When loading documents
   docstoreDocuments.push({
       id: docId,                        // "r-1323565.1_881b0329" ← FULL ID
       doc_id: docId,                    // "r-1323565.1_881b0329" ← FULL ID
       filename: filename,               // "r-1323565.1_881b0329.md"
       group_base_id: base_doc_id,       // "r-1323565.1" ← Keep for grouping
       ...
   });
   
   // When sending job
   document_ids: selectedDocs.map(d => d.doc_id),  // Now sends full ID!
   ```

2. **Backend (`phased_processing_api.py`)**: Try exact match FIRST
   ```python
   # Try exact match with FULL doc_id
   metadata_files = glob(f"{docstore_base}/**/documents/{doc_id}.metadata.json")
   
   if metadata_files:
       # Perfect match! Use it
       metadata_file = metadata_files[0]
   else:
       # No exact match - this is an error, don't fallback to wildcard
       logger.error(f"Document {doc_id} not found")
       continue
   ```

**Pros**:
- ✅ Precise document selection
- ✅ No ambiguity
- ✅ User gets exactly what they selected
- ✅ Backward compatible (old jobs with group IDs will fail explicitly)

**Cons**:
- ❌ Requires frontend changes
- ❌ May break existing UI grouping logic

---

### Solution B: Backend Validates Ambiguous Matches

**Concept**: Keep current behavior but add validation to reject ambiguous requests.

**Changes needed**:

1. **Backend (`phased_processing_api.py`)**:
   ```python
   metadata_files = glob(f"{docstore_base}/**/documents/{doc_id}_*.metadata.json")
   
   if len(metadata_files) > 1:
       # AMBIGUOUS - reject with error
       error_msg = (
           f"Ambiguous document ID '{doc_id}' matches {len(metadata_files)} files: "
           f"{[os.path.basename(f) for f in metadata_files[:5]]}. "
           f"Please specify full document ID with hex suffix."
       )
       logger.error(error_msg)
       # Mark job as failed
       continue
   
   if len(metadata_files) == 1:
       # Exactly one match - use it
       metadata_file = metadata_files[0]
   ```

**Pros**:
- ✅ Fails explicitly instead of processing wrong document
- ✅ Forces users/API to be specific
- ✅ No silent data corruption

**Cons**:
- ❌ Breaks existing workflows that rely on group base IDs
- ❌ Requires user to know full document ID
- ❌ Doesn't solve the underlying ambiguity

---

### Solution C: Backend Asks User to Disambiguate (UI Change)

**Concept**: When multiple matches found, return error with options for user to choose.

**Changes needed**:

1. **Backend**: Return list of matches when ambiguous
   ```python
   if len(metadata_files) > 1:
       return jsonify({
           'success': False,
           'error': 'Ambiguous document ID',
           'matches': [
               {
                   'doc_id': extract_doc_id(f),
                   'filename': os.path.basename(f),
                   'size': os.path.getsize(f),
                   ...
               }
               for f in metadata_files
           ]
       }), 400
   ```

2. **Frontend**: Show selection dialog with matches

**Pros**:
- ✅ User-friendly
- ✅ Explicit choice
- ✅ Prevents wrong document processing

**Cons**:
- ❌ Complex UI changes
- ❌ Interrupts workflow
- ❌ Overkill for most cases

---

## Recommended Implementation: Solution A

### Phase 1: Backend Changes

**File**: `backend/services/rag/document_store_browser.py`

**Line 117-132**: DON'T strip hex suffix for grouping - use it ONLY for display grouping, keep full doc_id:

```python
# NEW LOGIC: Keep full doc_id for uniqueness, use group_base_id for display
full_doc_id = filename  # e.g., "r-1323565.1_881b0329.md"
file_ext = os.path.splitext(filename)[1].lower()

# Remove file extension
base_with_hex = full_doc_id[:-len(file_ext)]  # "r-1323565.1_881b0329"

# Extract group base ID for display grouping
group_base_id = base_with_hex
if '_' in base_with_hex:
    parts = base_with_hex.rsplit('_', 1)
    if len(parts) == 2 and len(parts[1]) == 8:
        try:
            int(parts[1], 16)
            group_base_id = parts[0]  # "r-1323565.1" for grouping
        except ValueError:
            pass

# Use FULL doc_id (with hex) as unique identifier
if base_with_hex not in doc_groups:
    doc_groups[base_with_hex] = {
        'doc_id': base_with_hex,          # FULL ID with hex!
        'group_base_id': group_base_id,   # For display grouping
        'files': [],
        'metadata': metadata
    }
```

**Line 151-170**: Return full doc_id:

```python
for full_doc_id, group_data in doc_groups.items():
    for file_info in group_data['files']:
        all_documents.append({
            'doc_id': full_doc_id,                    # ← FULL ID!
            'group_base_id': group_data['group_base_id'],  # For UI grouping
            'original_filename': file_info['filename'],
            ...
        })
```

---

### Phase 2: Frontend Changes

**File**: `backend/web_client/index.html`

**Line 4560**: Use full doc_id:

```javascript
docstoreDocuments.push({
    id: doc.doc_id,                    // Full ID: "r-1323565.1_881b0329"
    doc_id: doc.doc_id,                // Full ID: "r-1323565.1_881b0329"
    group_base_id: doc.group_base_id,  // For display: "r-1323565.1"
    filename: doc.original_filename,
    ...
});
```

The rest of the frontend code stays the same - it already sends `d.doc_id`, which will now be the full ID!

---

### Phase 3: Backend Validation

**File**: `backend/services/rag/phased_processing_api.py`

**Line 320-340**: Add strict matching:

```python
for doc_id in document_ids:
    # Try to get from phased DB first
    existing_doc = phased_db.get_document(doc_id)
    
    if not existing_doc:
        # Search Document Store - try EXACT match only
        import glob as glob_module
        
        # Try exact match with FULL doc_id
        metadata_files = glob_module.glob(
            f"{docstore_base}/**/documents/{doc_id}.metadata.json", 
            recursive=True
        )
        
        if not metadata_files:
            # Try with .pdf extension (some docs don't have metadata)
            metadata_files = glob_module.glob(
                f"{docstore_base}/**/documents/{doc_id}.pdf", 
                recursive=True
            )
        
        if not metadata_files:
            logger.error(f"Document {doc_id} not found in Document Store")
            continue
        
        if len(metadata_files) > 1:
            logger.error(
                f"Document {doc_id} matched {len(metadata_files)} files: "
                f"{[os.path.basename(f) for f in metadata_files]}"
            )
            continue
        
        # Exactly one match - use it
        metadata_file = metadata_files[0]
        ...
```

---

## Migration Strategy

1. **Deploy backend changes first** (document_store_browser.py)
   - New API returns full doc_id
   - Old frontend still works (uses group_base_id for display)

2. **Deploy frontend changes** (index.html)
   - Frontend now sends full doc_id
   - Backend strictly validates

3. **Deploy backend validation** (phased_processing_api.py)
   - Reject ambiguous matches
   - Log errors for debugging

---

## Testing Plan

### Test 1: Specific Document Selection
1. Open Document Store browser
2. Select `r-1323565.1_881b0329.md`
3. Submit chunking job
4. **Verify**: Job processes `r-1323565.1_881b0329`, NOT `_395de1a8`

### Test 2: Multiple Variants
1. Document store has both `_395de1a8` and `_881b0329`
2. Select `_881b0329`
3. **Verify**: Correct document processed

### Test 3: Backward Compatibility
1. Old job with `document_ids: ["r-1323565.1"]`
2. **Verify**: Job fails with clear error "Ambiguous document ID"

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|------------|
| Breaks existing jobs | Medium | High | Add migration or fallback logic |
| UI grouping broken | Low | Medium | Use group_base_id for display |
| Performance (glob search) | Low | Low | Add index or cache |

---

**Conclusion**: The bug is caused by loss of document specificity during the grouping process. Solution A (sending full doc_id) is the cleanest fix that maintains data integrity while requiring minimal UI changes.

**Recommended next step**: Implement Solution A in phases as outlined above.

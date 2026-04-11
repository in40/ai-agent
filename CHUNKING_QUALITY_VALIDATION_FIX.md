# Chunking Quality Validation Fix

**Date**: April 8, 2026  
**Severity**: Critical - Silent Data Loss  
**Status**: 🔄 Implementation in Progress  
**Trigger**: Job `job_277abcdb4a83` completed with only 2 chunks from 155KB document (0.44% coverage)

---

## Problem Summary

Job `job_277abcdb4a83` processed a 155KB, 721-line Russian government standard document (`r-1323565.1_395de1a8.pdf`) but generated only **2 chunks** covering **691 characters** (0.44% of the document). The job was marked as **completed successfully** with no warnings or errors.

### Root Causes Identified

1. **No coverage validation**: Code accepts any number of chunks from LLM without verifying document coverage
2. **Input character limit**: Prompt truncates document to 50K chars, losing 68% of a 155KB document
3. **No minimum chunk count validation**: No sanity check based on document size
4. **No warning propagation**: Job status endpoint has no mechanism to report quality warnings

---

## Implementation Plan

### Phase 1: Remove Input Character Limits (Solution 2)

**File**: `backend/services/rag/smart_ingestion_enhanced.py`  
**Line**: ~534

**Current Code:**
```python
# Prepare full prompt with input text injected
full_prompt = prompt.format(input_text=document_content[:50000])  # Limit to 50K chars
```

**New Code:**
```python
# Prepare full prompt with input text injected
# REMOVED: No artificial limit on input text - LLM should process entire document
logger.info(f"Document content length: {len(document_content)} characters ({len(document_content)/1000:.1f}K chars)")
full_prompt = prompt.format(input_text=document_content)
```

**Rationale:**
- Modern LLMs have large context windows (128K+ tokens)
- The 50K char limit caused 68% content loss for 155KB document
- If context window is exceeded, LLM will return an error (which we handle)
- Better to fail explicitly than silently lose content

**Impact:**
- All document content will be sent to LLM
- May increase LLM call time for very large documents
- May fail for documents exceeding LLM context window (but will fail explicitly with error)

---

### Phase 2: Add Content Coverage Validation (Solution 1)

**File**: `backend/services/rag/smart_ingestion_enhanced.py`  
**Location**: After JSON parsing, before returning success

**New validation function to add:**

```python
def _validate_chunking_coverage(document_content: str, chunks: List[Dict]) -> tuple[bool, str]:
    """
    Validate that LLM chunking adequately covered the input document.
    
    Args:
        document_content: Original document text
        chunks: List of chunk dictionaries with 'content' field
    
    Returns:
        Tuple of (is_valid, warning_or_error_message)
    """
    if not chunks:
        return False, "No chunks generated"
    
    # Calculate total chunked content length
    total_chunked_length = sum(len(c.get('content', '')) for c in chunks)
    input_length = len(document_content)
    
    if input_length == 0:
        return False, "Empty document content"
    
    # Calculate coverage ratio
    coverage_ratio = total_chunked_length / input_length
    
    # Log coverage for monitoring
    logger.info(
        f"Chunking coverage validation: "
        f"input={input_length} chars, "
        f"chunked={total_chunked_length} chars, "
        f"coverage={coverage_ratio:.1%}, "
        f"chunks={len(chunks)}"
    )
    
    # Critical threshold: Less than 50% coverage is a hard failure
    if coverage_ratio < 0.50:
        error_msg = (
            f"Insufficient content coverage: {coverage_ratio:.1%} "
            f"({total_chunked_length}/{input_length} chars in {len(chunks)} chunks). "
            f"Expected >50%. LLM may have stopped prematurely."
        )
        logger.error(f"Coverage validation FAILED: {error_msg}")
        return False, error_msg
    
    # Warning threshold: Less than 70% coverage is a warning
    if coverage_ratio < 0.70:
        warning_msg = (
            f"Low content coverage: {coverage_ratio:.1%} "
            f"({total_chunked_length}/{input_length} chars in {len(chunks)} chunks). "
            f"Expected >70%. Some content may be missing."
        )
        logger.warning(f"Coverage validation WARNING: {warning_msg}")
        return True, warning_msg  # Success but with warning
    
    # Good coverage
    logger.info(f"Coverage validation PASSED: {coverage_ratio:.1%}")
    return True, ""
```

**Integration point in `chunk_document_with_llm` function:**

```python
# After successful JSON parsing and chunk filtering (around line 640)
logger.info(f"[DEBUG] Successfully parsed JSON: {len(chunks)} chunks found")

# === NEW: Validate chunking coverage ===
is_valid, coverage_message = _validate_chunking_coverage(document_content, chunks)

if not is_valid:
    # Hard failure - insufficient coverage
    logger.error(f"Chunking validation failed: {coverage_message}")
    return False, [], coverage_message

# If we have a warning, store it in chunks metadata for later
if coverage_message:
    logger.warning(f"Chunking validation warning: {coverage_message}")
    # Warning will be propagated to job status
# === END NEW VALIDATION ===

# Filter out invalid chunks (parsing artifacts without proper structure)
valid_chunks = []
for chunk in chunks:
    if isinstance(chunk, dict) and 'chunk_id' in chunk and 'content' in chunk:
        valid_chunks.append(chunk)
    else:
        logger.warning(f"Filtered out invalid chunk: {chunk}")
chunks = valid_chunks
logger.info(f"[DEBUG] After filtering: {len(chunks)} valid chunks")

# Return coverage warning in result tuple
return True, chunks, coverage_message if coverage_message else ""
```

**Change function signature:**

The function currently returns `Tuple[bool, List[Dict], str]` where the third element is error message. We'll use the same pattern - if there's a warning, return it in the error field but still set success=True. The caller will need to distinguish between warnings and errors.

**Actually, better approach:** Add warning to chunk metadata:

```python
# After validation, inject warning into first chunk's metadata
if coverage_message and is_valid:
    if chunks:
        chunks[0]['_coverage_warning'] = coverage_message
```

Then the caller can check for this metadata field.

---

### Phase 3: Add Minimum Chunk Count Validation (Solution 3)

**File**: `backend/services/rag/smart_ingestion_enhanced.py`  
**Location**: Inside `_validate_chunking_coverage` function

**Additional validation logic to add:**

```python
def _validate_chunking_coverage(document_content: str, chunks: List[Dict]) -> tuple[bool, str]:
    """... (docstring from above) ..."""
    if not chunks:
        return False, "No chunks generated"
    
    # Calculate total chunked content length
    total_chunked_length = sum(len(c.get('content', '')) for c in chunks)
    input_length = len(document_content)
    
    if input_length == 0:
        return False, "Empty document content"
    
    # Calculate coverage ratio
    coverage_ratio = total_chunked_length / input_length
    
    # === NEW: Minimum chunk count validation ===
    # Estimate expected chunks based on document size
    # Average chunk target: 200-450 tokens ≈ 800-1800 characters
    # Use conservative estimate: 1000 chars per chunk
    estimated_chunks_needed = max(1, input_length // 1000)
    min_expected_chunks = max(3, estimated_chunks_needed)  # At least 3 chunks
    
    chunk_count_warning = ""
    if len(chunks) < min_expected_chunks:
        chunk_count_warning = (
            f"Suspiciously few chunks: {len(chunks)} generated vs "
            f"~{min_expected_chunks} expected for {input_length}-char document. "
            f"Expected ~1 chunk per 1000 characters."
        )
        logger.warning(f"Chunk count validation WARNING: {chunk_count_warning}")
    # === END CHUNK COUNT VALIDATION ===
    
    # Log coverage for monitoring
    logger.info(
        f"Chunking coverage validation: "
        f"input={input_length} chars, "
        f"chunked={total_chunked_length} chars, "
        f"coverage={coverage_ratio:.1%}, "
        f"chunks={len(chunks)} (expected ~{min_expected_chunks})"
    )
    
    # Critical threshold: Less than 50% coverage is a hard failure
    if coverage_ratio < 0.50:
        error_msg = (
            f"Insufficient content coverage: {coverage_ratio:.1%} "
            f"({total_chunked_length}/{input_length} chars in {len(chunks)} chunks). "
            f"Expected >50%. LLM may have stopped prematurely."
        )
        logger.error(f"Coverage validation FAILED: {error_msg}")
        return False, error_msg
    
    # Warning threshold: Less than 70% coverage OR insufficient chunk count
    warnings = []
    if coverage_ratio < 0.70:
        warnings.append(
            f"Low content coverage: {coverage_ratio:.1%} "
            f"({total_chunked_length}/{input_length} chars)"
        )
    
    if chunk_count_warning:
        warnings.append(chunk_count_warning)
    
    if warnings:
        warning_msg = " | ".join(warnings)
        logger.warning(f"Chunking validation warnings: {warning_msg}")
        return True, warning_msg  # Success but with warning
    
    # Good coverage
    logger.info(f"Coverage validation PASSED: {coverage_ratio:.1%}")
    return True, ""
```

---

### Phase 4: Propagate Warnings to Job Status

#### 4a. Update phased_processing_api.py to capture warnings

**File**: `backend/services/rag/phased_processing_api.py`  
**Location**: Around line 1683-1760 (chunk phase processing)

**Current code:**
```python
success, llm_chunks, error = chunk_document_with_llm_sync(...)

if success:
    # Convert LLM chunks to our Chunk format
    chunks = []
    for i, c in enumerate(llm_chunks):
        chunks.append(Chunk(...))
    
    # Store cleaning method in metadata for UI notification
    if cleaning_method == "latex_converted":
        chunking_metadata = {
            'cleaning_method': cleaning_method,
            'warning': 'LaTeX formulas converted...'
        }
    ...
```

**New code:**
```python
success, llm_chunks, error_or_warning = chunk_document_with_llm_sync(...)

if success:
    # Convert LLM chunks to our Chunk format
    chunks = []
    for i, c in enumerate(llm_chunks):
        chunks.append(Chunk(...))
    
    # Initialize chunking_metadata
    chunking_metadata = {}
    
    # Check for coverage warning (stored in first chunk metadata by validator)
    coverage_warning = None
    if llm_chunks and '_coverage_warning' in llm_chunks[0]:
        coverage_warning = llm_chunks[0].pop('_coverage_warning')  # Extract and remove from chunk
        logger.warning(f"[Phased Job {job_id}] Coverage warning: {coverage_warning}")
    
    # Also check error_or_warning field for coverage warnings
    # If success=True but error field has text, it's a warning (not an error)
    chunking_warning = error_or_warning if success and error_or_warning else None
    
    # Combine warnings
    final_warning = coverage_warning or chunking_warning
    if final_warning:
        chunking_metadata['coverage_warning'] = final_warning
    
    # Store cleaning method in metadata for UI notification
    if cleaning_method == "latex_converted":
        chunking_metadata['cleaning_method'] = cleaning_method
        if not chunking_metadata.get('warning'):
            chunking_metadata['warning'] = 'LaTeX formulas converted to natural language descriptions (mathematical meaning preserved)'
    elif cleaning_method == "aggressive":
        chunking_metadata['cleaning_method'] = cleaning_method
        if not chunking_metadata.get('warning'):
            chunking_metadata['warning'] = 'LaTeX formulas may be corrupted due to aggressive JSON cleaning'
    else:
        chunking_metadata['cleaning_method'] = cleaning_method
    
    # Log summary
    logger.info(
        f"[Phased Job {job_id}] LLM generated {len(chunks)} chunks "
        f"(total content: {sum(c.content_length for c in chunks)} chars)"
    )
    
    if final_warning:
        logger.warning(f"[Phased Job {job_id}] WARNING: {final_warning}")
```

#### 4b. Store warnings in job parameters (Redis)

Since the `document_processing` table doesn't have a generic JSONB metadata column, we'll store warnings in the job's parameters dictionary in Redis. This is already being used for heartbeat tracking.

**File**: `backend/services/rag/phased_processing_api.py`  
**Location**: After chunking completes, around line 1790

**Add after saving chunks:**

```python
# Store warning in job parameters for UI display
if final_warning:
    try:
        from backend.services.rag.job_queue import job_queue as jq
        current_job = jq.get_job(job_id)
        if current_job:
            # Initialize warnings list if not exists
            if 'warnings' not in current_job.parameters:
                current_job.parameters['warnings'] = []
            
            # Add warning with context
            current_job.parameters['warnings'].append({
                'type': 'chunking_coverage',
                'doc_id': doc.doc_id,
                'message': final_warning,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'warning'  # Could be 'error' in future
            })
            
            # Save updated job
            jq.update_job(current_job)
            logger.info(f"[Phased Job {job_id}] Warning saved to job parameters")
    except Exception as e:
        logger.error(f"[Phased Job {job_id}] Failed to save warning: {e}")
```

#### 4c. Update get_job_status to return warnings

**File**: `backend/services.rag/phased_processing_api.py`  
**Location**: `get_job_status` function (line 1970)

**Current code:**
```python
# Note: chunking_metadata warning checks removed - metadata not currently persisted to DB
# Warnings would be shown here if we stored chunking_metadata in the database
warnings = None

return jsonify({
    'success': True,
    'job_id': job_id,
    'progress': progress.to_dict(),
    'documents': {
        'total': len(all_docs),
        'completed': len(completed_docs),
        'failed': len(failed_docs),
        'processing': len(processing_docs),
    },
    'failed_document_ids': [d.doc_id for d in failed_docs],
    'warnings': warnings if warnings else None
})
```

**New code:**
```python
# Collect warnings from job parameters
warnings_list = []

try:
    from backend.services.rag.job_queue import job_queue
    job = job_queue.get_job(job_id)
    if job and job.parameters:
        # Check for warnings stored in job parameters
        job_warnings = job.parameters.get('warnings', [])
        if job_warnings:
            warnings_list.extend(job_warnings)
        
        # Also check heartbeat for coverage warnings
        heartbeat = job.parameters.get('heartbeat', {})
        if heartbeat.get('coverage_warning'):
            warnings_list.append({
                'type': 'chunking_coverage',
                'message': heartbeat['coverage_warning'],
                'timestamp': heartbeat.get('timestamp'),
                'severity': 'warning'
            })
except Exception as e:
    logger.debug(f"Could not check job warnings: {e}")

# Format warnings for response
warnings = warnings_list if warnings_list else None

return jsonify({
    'success': True,
    'job_id': job_id,
    'progress': progress.to_dict(),
    'documents': {
        'total': len(all_docs),
        'completed': len(completed_docs),
        'failed': len(failed_docs),
        'processing': len(processing_docs),
    },
    'failed_document_ids': [d.doc_id for d in failed_docs],
    'warnings': warnings
})
```

---

### Phase 5: Add Enhanced Logging for Debugging

**File**: `backend/services/rag/smart_ingestion_enhanced.py`  
**Location**: After document loading, before LLM call

**Add detailed logging:**

```python
# Load document
document_loader = DocumentLoader()
docs = document_loader.load_document(file_path)
logger.info(f"[DEBUG] Loaded {len(docs)} documents")

document_content = ""
for doc in docs:
    document_content += doc.page_content + "\n"

if not document_content.strip():
    return False, [], "Empty document content"

# === NEW: Log document size for monitoring ===
doc_length = len(document_content)
doc_tokens_estimate = doc_length // 4  # Rough estimate
logger.info(
    f"[CHUNKING] Document loaded: {doc_length} characters, "
    f"~{doc_tokens_estimate} tokens, "
    f"file={file_path}"
)
# === END NEW LOGGING ===
```

---

## Files to Modify

1. **`backend/services/rag/smart_ingestion_enhanced.py`**
   - Remove 50K character limit (line ~534)
   - Add `_validate_chunking_coverage()` function (new)
   - Integrate validation in `chunk_document_with_llm()` (line ~640)
   - Add document size logging (line ~510)
   - Update return value handling to include warnings

2. **`backend/services/rag/phased_processing_api.py`**
   - Capture coverage warnings from chunking (line ~1683-1790)
   - Store warnings in job parameters (new code after chunking)
   - Update `get_job_status()` to return warnings (line ~1970)
   - Add chunk count logging (line ~1720)

3. **`CHUNKING_QUALITY_VALIDATION_FIX.md`** (this file)
   - Implementation plan and documentation

---

## Testing Strategy

### Unit Tests

1. **Test coverage validation function:**
   ```python
   def test_validate_coverage_full():
       doc = "A" * 10000
       chunks = [{'content': "A" * 9000}]
       valid, msg = _validate_chunking_coverage(doc, chunks)
       assert valid == True
       assert "warning" not in msg.lower()
   
   def test_validate_coverage_low():
       doc = "A" * 10000
       chunks = [{'content': "A" * 300}]  # Only 3%
       valid, msg = _validate_chunking_coverage(doc, chunks)
       assert valid == False
       assert "insufficient" in msg.lower()
   
   def test_validate_coverage_warning():
       doc = "A" * 10000
       chunks = [{'content': "A" * 6000}]  # 60%
       valid, msg = _validate_chunking_coverage(doc, chunks)
       assert valid == True
       assert "low" in msg.lower()
   
   def test_validate_chunk_count():
       doc = "A" * 50000  # Should need ~50 chunks
       chunks = [{'content': "A" * 1000}] * 2  # Only 2 chunks
       valid, msg = _validate_chunking_coverage(doc, chunks)
       assert valid == True  # Coverage might be ok
       assert "few chunks" in msg.lower() or "suspiciously" in msg.lower()
   ```

### Integration Tests

1. **Re-run job_277abcdb4a83:**
   - Reset job status
   - Re-run chunking
   - Verify warning is generated
   - Check job status endpoint returns warning

2. **Test with small document:**
   - Upload 5KB document
   - Verify no warnings generated
   - Verify normal chunking (5-10 chunks)

3. **Test with large document:**
   - Upload 200KB document
   - Verify full content sent to LLM (no truncation)
   - Verify appropriate number of chunks generated (100+)

### Manual Verification

```bash
# 1. Check job status endpoint
curl -s http://localhost:5003/api/rag/phased/job/job_277abcdb4a83/status | python3 -m json.tool

# Expected response should include:
# {
#   "warnings": [
#     {
#       "type": "chunking_coverage",
#       "doc_id": "r-1323565.1_395de1a8",
#       "message": "Low content coverage: 0.44% ...",
#       "severity": "warning"
#     }
#   ]
# }

# 2. Check RAG service logs for validation messages
grep "Coverage validation" rag_service.log
grep "Chunking coverage validation" rag_service.log

# 3. Verify chunks.json files
find document-store-mcp-server/data/ingested -name "*.chunks.json" -exec python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
print(f\"{sys.argv[1]}: {data['total_chunks']} chunks, strategy={data['chunking_strategy']}\")
" {} \;
```

---

## Expected Behavior After Fix

### Scenario 1: Good chunking (>70% coverage, sufficient chunks)
- ✅ Job completes successfully
- ✅ No warnings shown
- ✅ All content chunked properly

### Scenario 2: Poor chunking (<50% coverage)
- ❌ Job fails with explicit error
- ⚠️ Error message shows coverage percentage
- 📝 User can retry with different settings

### Scenario 3: Acceptable but suboptimal (50-70% coverage OR too few chunks)
- ✅ Job completes successfully
- ⚠️ Warning shown in job status UI
- 📝 Warning message includes:
  - Coverage percentage
  - Chunks generated vs expected
  - Document size
- 📝 User can decide to re-run or accept

---

## Rollback Plan

If issues arise after deployment:

1. **Immediate rollback:**
   ```bash
   cd /root/qwen/ai_agent
   git stash  # If changes committed
   ./start_all_services_fast.sh  # Restart with old code
   ```

2. **Disable validation only:**
   - Set environment variable: `DISABLE_CHUNKING_VALIDATION=true`
   - Restart RAG service

3. **Restore character limit:**
   - Revert line 534 in `smart_ingestion_enhanced.py`
   - Restart RAG service

---

## Deployment Steps

1. ✅ Create implementation plan (this file)
2. ✅ Modify `smart_ingestion_enhanced.py`:
   - ✅ Remove character limit (line ~534)
   - ✅ Add validation function (new, ~100 lines)
   - ✅ Integrate validation (line ~750)
   - ✅ Add logging (line ~530)
3. ✅ Modify `phased_processing_api.py`:
   - ✅ Capture warnings (line ~1705)
   - ✅ Store in job parameters (line ~1815)
   - ✅ Update get_job_status (line ~2025)
4. ✅ Unit tests passed (test_chunking_validation_standalone.py)
5. ⏳ Integration tests (restart services and verify)
6. ⏳ Monitor logs for 24 hours
7. ⏳ Check for false positives/negatives
8. ⏳ Adjust thresholds if needed

**Implementation Date**: April 8, 2026  
**Services Restarted**: Yes (./start_all_services_fast.sh --no-gui)  
**Unit Tests**: ✅ All 6 tests passed

---

## Monitoring & Alerts

After deployment, monitor:

1. **Coverage validation failures** (should catch silent failures like job_277abcdb4a83)
2. **Coverage warnings** (50-70% range - may indicate LLM issues)
3. **Chunk count anomalies** (too few chunks for document size)
4. **LLM timeout increases** (removing 50K limit may cause timeouts for very large docs)

### Key Metrics to Track

```python
# In monitoring dashboard (future):
- avg_coverage_ratio per day
- pct_jobs_with_warnings per day
- avg_chunks_per_kb per document_type
- llm_timeout_rate (may increase with larger inputs)
```

---

## Future Enhancements (Not in Scope)

1. **Multi-pass chunking** (Solution 4): Split large documents and chunk in parallel
2. **PDF extraction quality validation** (Solution 5): Verify MD file matches PDF content
3. **Database schema update**: Add JSONB `processing_metadata` column to `document_processing`
4. **UI improvements**: Show warnings prominently in job status page
5. **Automatic retry**: Re-chunk documents with insufficient coverage automatically
6. **Adaptive chunking**: Adjust chunk size based on document type and content

---

**Status**: Ready for implementation  
**Priority**: High (prevents silent data loss)  
**Estimated risk**: Low (adds validation, doesn't change core logic)  
**Backward compatibility**: Yes (existing jobs unaffected, only new jobs validated)

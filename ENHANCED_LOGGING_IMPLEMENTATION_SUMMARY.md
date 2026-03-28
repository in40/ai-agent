# Enhanced Logging Implementation Summary

**Date**: March 8, 2026  
**Status**: ✅ Complete

---

## Implemented Features

### 1. ✅ DEBUG Level Logging

**Files Modified**:
- `backend/services/rag/app.py` - Added configurable log level
- `backend/services/rag/phased_processing_api.py` - Added DEBUG logs
- `rag_component/document_loader.py` - Added DEBUG logs

**Changes**:

#### app.py (Line 47-54)
```python
# Initialize logging with configurable level
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized at {log_level} level")
```

**Usage**:
```bash
export LOG_LEVEL=DEBUG  # Enable debug logging
export LOG_LEVEL=INFO   # Default
export LOG_LEVEL=WARNING  # Only warnings and errors
```

#### document_loader.py - Added DEBUG logs:
- LLM client initialization details
- Image conversion details (DPI, format)
- Per-page processing details
- Response metadata (tokens, finish_reason)
- Cleanup timing

---

### 2. ✅ Request/Response Logging

**File**: `rag_component/document_loader.py`

**Added**:
- System prompt logging (first 200 chars + full in DEBUG)
- User prompt logging (first 200 chars + full in DEBUG)
- LLM request details (model, max_tokens, timeout)
- LLM response metadata (usage, finish_reason)
- Response preview (first 500 chars in DEBUG)

**Example Output**:
```
INFO: LLM extraction prompt (system): You are a PDF to Markdown converter. Output ONLY the markdown content...
INFO: LLM extraction prompt (user): Convert this PDF page to clean markdown. Preserve all mathematical...
DEBUG: LLM extraction prompt (system, full): You are a PDF to Markdown converter...
INFO: Page 1: LLM request: model=qwen3.5-35b, max_tokens=32000, timeout=43200s
INFO: Page 1: LLM response: 2345 chars
DEBUG: Page 1: LLM response usage: prompt=1234, completion=567, total=1801
DEBUG: Page 1: LLM response finish_reason: stop
DEBUG: Page 1: LLM response (first 500 chars): # GOST R...
```

---

### 3. ✅ Timing Breakdown

**Files**: Both `phased_processing_api.py` and `document_loader.py`

**Added**:

#### Phase-level timing:
```python
extract_phase_start = time.time()
# ... extraction code ...
extract_phase_time = time.time() - extract_phase_start
logger.info(f"[Phased Job {job_id}] Phase Extract completed in {extract_phase_time:.2f}s")
```

#### Document-level timing:
```python
doc_start = time.time()
# ... extraction ...
doc_time = time.time() - doc_start
logger.info(f"Extracted {len(text)} chars in {doc_time:.2f}s ({len(text)/doc_time:.0f} chars/sec)")
```

#### Per-page timing (LLM extraction):
```python
img_time = time.time() - img_start
logger.debug(f"Page {page_num}: Image conversion {img_time:.2f}s ({len(img_base64)} bytes base64)")

llm_time = time.time() - llm_start
logger.info(f"Page {page_num}: LLM call {llm_time:.2f}s")

clean_time = time.time() - clean_start
logger.debug(f"Page {page_num}: Markdown cleanup {clean_time:.2f}s")

page_total = time.time() - page_start
logger.info(f"Page {page_num}: Total {page_total:.2f}s ({len(page_markdown)} chars)")
```

#### Total LLM extraction timing:
```python
llm_total_time = time.time() - llm_total_start
logger.info(f"LLM extraction complete: {len(full_markdown)} chars in {llm_total_time:.2f}s ({len(full_markdown)/llm_total_time:.0f} chars/sec)")
```

---

### 5. ✅ Fallback Chain Logging

**File**: `backend/services/rag/phased_processing_api.py`

**Added detailed fallback logging**:
```python
if method == 'auto':
    logger.info(f"[Phased Job {job_id}] Auto mode: Trying PyMuPDF first...")
    try:
        text = loader._extract_with_pymupdf(...)
        logger.info(f"✓ PyMuPDF succeeded: {len(text)} chars")
    except Exception as e:
        logger.warning(f"✗ PyMuPDF failed: {type(e).__name__}: {str(e)[:200]}")
        logger.info(f"Auto mode: Trying pdfminer...")
        try:
            text = loader._extract_with_pdfminer(...)
            logger.info(f"✓ pdfminer succeeded: {len(text)} chars")
        except Exception as e2:
            logger.warning(f"✗ pdfminer failed: {type(e2).__name__}: {str(e2)[:200]}")
            logger.info(f"Auto mode: Trying Tesseract OCR (slow)...")
            # ... etc
```

**Example Output**:
```
INFO: Auto mode: Trying PyMuPDF first...
WARNING: ✗ PyMuPDF failed: PyMuPDFError: cannot open file
INFO: Auto mode: Trying pdfminer...
WARNING: ✗ pdfminer failed: PDFMinerError: encrypted PDF
INFO: Auto mode: Trying Tesseract OCR (slow)...
INFO: ✓ Tesseract succeeded: 45678 chars
```

---

### 6. ✅ Config Validation Logging

**File**: `backend/services/rag/phased_processing_api.py` (create_job_from_docstore endpoint)

**Added**:
```python
# Log received config
logger.info(f"[create_job_from_docstore] Received extraction_config: {json.dumps(extraction_config, indent=2)}")

# Validate method
valid_methods = ['auto', 'pymupdf', 'pdfminer', 'tesseract', 'llm']
method = extraction_config.get('method', 'auto')
if method not in valid_methods:
    logger.warning(f"Invalid extraction method '{method}', using 'auto' instead")
    extraction_config['method'] = 'auto'
else:
    logger.info(f"✓ Extraction method '{method}' is valid")

# Validate page_range
# ... validation logic ...
logger.info(f"✓ Page range valid: {start}-{end if end else 'end'}")

# Log final validated config
logger.info(f"Final extraction_config after validation: {json.dumps(extraction_config, indent=2)}")
```

---

## Files Modified

| File | Lines Added | Changes |
|------|-------------|---------|
| `backend/services/rag/app.py` | ~7 | Configurable LOG_LEVEL |
| `backend/services/rag/phased_processing_api.py` | ~80 | Timing, fallback, validation, DEBUG logs |
| `rag_component/document_loader.py` | ~40 | LLM request/response, timing, DEBUG logs |
| **Total** | **~127** | |

---

## Testing Instructions

### 1. Test DEBUG Logging
```bash
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate
export LOG_LEVEL=DEBUG
python -m backend.services.rag.app

# In another terminal, run extraction job
# Check logs show detailed debug info
```

### 2. Test Request/Response Logging
```bash
export LOG_LEVEL=DEBUG
# Run LLM extraction
# Verify logs show:
# - Prompts (first 200 chars + full in DEBUG)
# - Response metadata (tokens, finish_reason)
# - Response preview
```

### 3. Test Timing
```bash
export LOG_LEVEL=INFO
# Run extraction
# Verify logs show:
# - "in X.XXs" for each step
# - "chars/sec" throughput
# - Per-page timing breakdown
```

### 4. Test Fallback Chain
```bash
# Test with method='auto' and problematic PDF
# Verify logs show:
# - "Trying PyMuPDF..."
# - "✗ PyMuPDF failed: ..."
# - "Trying pdfminer..."
# - "✓ pdfminer succeeded: ..."
```

### 5. Test Config Validation
```bash
# Send invalid method: 'invalid_method'
# Verify log shows:
# - "Invalid extraction method 'invalid_method', using 'auto' instead"
```

---

## Example Log Output

```
2026-03-08 10:00:00,000 [INFO] backend.services.rag.app: Logging initialized at INFO level
2026-03-08 10:00:01,000 [INFO] backend.services.rag.phased_processing_api: [create_job_from_docstore] Received extraction_config: {
  "method": "llm",
  "page_range": "all"
}
2026-03-08 10:00:01,001 [INFO] backend.services.rag.phased_processing_api: ✓ Extraction method 'llm' is valid
2026-03-08 10:00:01,002 [INFO] backend.services.rag.phased_processing_api: ✓ Page range: all
2026-03-08 10:00:05,000 [INFO] backend.services.rag.phased_processing_api: [Phased Job job_abc123] Running Phase: Extract
2026-03-08 10:00:05,001 [INFO] backend.services.rag.phased_processing_api: Extraction config: method=llm, page_range=all
2026-03-08 10:00:05,002 [INFO] backend.services.rag.phased_processing_api: Extracting: r-1323565.1_8a84396d (r-1323565.1_8a84396d.pdf)
2026-03-08 10:00:05,003 [INFO] backend.services.rag.phased_processing_api: Using LLM extraction...
2026-03-08 10:00:06,000 [INFO] rag_component.document_loader: Sending PDF to LLM: url=http://192.168.51.237:1234/v1, model=qwen3.5-35b, timeout=43200s
2026-03-08 10:00:06,001 [INFO] rag_component.document_loader: LLM extraction prompt (system): You are a PDF to Markdown converter...
2026-03-08 10:00:06,002 [INFO] rag_component.document_loader: Converting all pages to images
2026-03-08 10:00:08,000 [INFO] rag_component.document_loader: Converted PDF to 15 images
2026-03-08 10:00:08,001 [INFO] rag_component.document_loader: Processing page 1
2026-03-08 10:00:08,500 [INFO] rag_component.document_loader: Page 1: Sending image to LLM (base64 size: 234567 bytes)
2026-03-08 10:00:13,500 [INFO] rag_component.document_loader: Page 1: LLM call 5.00s
2026-03-08 10:00:13,501 [INFO] rag_component.document_loader: Page 1: LLM response: 2345 chars
2026-03-08 10:00:13,502 [INFO] rag_component.document_loader: Page 1: LLM returned 2345 chars
2026-03-08 10:00:13,503 [INFO] rag_component.document_loader: Processing page 2
...
2026-03-08 10:01:30,000 [INFO] rag_component.document_loader: LLM extraction complete: 35678 total chars in 84.00s (425 chars/sec)
2026-03-08 10:01:30,001 [INFO] backend.services.rag.phased_processing_api: Extracted 35678 chars from r-1323565.1_8a84396d using llm in 85.00s (420 chars/sec)
2026-03-08 10:01:30,002 [INFO] backend.services.rag.phased_processing_api: Phase Extract completed in 85.00s
```

---

## Status

- ✅ Configurable log level (LOG_LEVEL env var)
- ✅ DEBUG level logging for detailed troubleshooting
- ✅ Request/response logging for LLM calls
- ✅ Timing breakdown for all operations
- ✅ Fallback chain logging
- ✅ Config validation logging

**Ready for production use!**

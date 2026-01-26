# Solution for Converting All PDF Files to Markdown

## Problem Identified
The original implementation used `signal.alarm()` for timeout handling, which only works in the main thread. During web uploads, PDF processing occurs in a separate thread, causing the timeout mechanism to fail with the error:
```
signal only works in main thread of the main interpreter
```

When this happened, the system would fall back to PyPDFLoader instead of using the marker library for markdown conversion.

## Solution Implemented

### 1. Replaced Signal-Based Timeout with Threading-Based Timeout
- Removed the `signal.alarm()`-based timeout mechanism
- Implemented a threading-based timeout using `ThreadPoolExecutor` with `future.result(timeout=seconds)`
- This approach works reliably in both main and child threads

### 2. Increased Timeout Duration
- Increased the timeout from 180 seconds to 300 seconds (5 minutes)
- Complex PDFs with many pages or complex layouts require more processing time
- The marker library also needs time to download and load models on first use

### 3. Updated Code Files

#### rag_component/pdf_converter.py:
- Replaced signal-based timeout with ThreadPoolExecutor-based timeout
- Created internal `_perform_conversion` method to run conversion in a separate thread
- Maintained the same external API for compatibility

#### rag_component/document_loader.py:
- Increased timeout from 180 to 300 seconds to allow more time for complex PDFs
- Updated comments to reflect the new approach

## Expected Results
With these changes:
1. All PDF files will be processed using the marker library instead of falling back to PyPDFLoader
2. PDF files will be converted to markdown and stored in the `rag_converted_markdown` directory
3. The system will be more reliable in processing complex PDFs
4. The timeout mechanism will work consistently across both direct processing and web uploads

## Benefits
- More accurate text extraction from complex PDF layouts
- Preservation of document structure in markdown format
- Consistent behavior regardless of processing context (main thread vs. child thread)
- Better user experience with properly converted documents

## Verification
The changes have been tested and confirmed to resolve the threading issue that was preventing the marker library from processing PDF files during web uploads.
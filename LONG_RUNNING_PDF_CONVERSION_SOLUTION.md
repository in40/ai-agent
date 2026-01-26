# Handling Long-Running PDF Conversions

## Problem Identified
Complex PDF files like "Приказ ФСТЭК России от 18 февраля 2013 г. N 21.pdf" require significantly longer processing times than the default timeouts allowed. The marker library needs to load large ML models and process complex layouts, which can take hours for complex documents.

## Changes Implemented

### 1. Increased Document Loader Timeout
- Updated `rag_component/document_loader.py` to increase timeout from 300 seconds to 3600 seconds (1 hour)
- This allows more time for the marker library to process complex PDFs

### 2. Increased Server Timeouts
- Updated `backend/services/rag/app.py` to increase Gunicorn timeout from 600 seconds to 7200 seconds (2 hours)
- Updated `backend/app.py` to increase Gunicorn timeout from 600 seconds to 7200 seconds (2 hours)
- This ensures the server doesn't terminate long-running requests

### 3. Preserved Threading-Based Timeout Mechanism
- Kept the threading-based timeout mechanism implemented previously
- This approach works reliably in both main and child threads
- Replaced the problematic signal-based timeout that only works in the main thread

## Expected Results
With these changes:
1. Complex PDF files will have up to 1 hour to complete conversion in the document loader
2. Server processes will not terminate requests prematurely (up to 2 hours)
3. The marker library will have sufficient time to load models and process complex layouts
4. PDF files that previously failed due to timeouts will now complete successfully

## Important Notes
- The conversion process may still take a significant amount of time for complex documents
- Memory usage will remain high during processing (as analyzed in MEMORY_USAGE_ANALYSIS.md)
- The system prioritizes accuracy over speed for document conversion
- Users should expect longer wait times for complex PDF uploads

## Verification
The system has been updated to handle long-running PDF conversions. The specific file "Приказ ФСТЭК России от 18 февраля 2013 г. N 21.pdf" should now complete processing successfully, though it may take a considerable amount of time depending on the complexity of the document structure.
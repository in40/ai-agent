# Smart Ingestion - Web Page Processing Feature

## Overview

The Smart Ingestion feature now supports processing web pages to automatically extract, download, chunk, and ingest documents into the vector database.

## New Workflow

### Web Page Processing Flow

```
User provides URL
       ↓
1. Fetch Web Page
   (HTTP GET with 30s timeout)
       ↓
2. Extract Document Links
   (BeautifulSoup HTML parsing)
   - Looks for: .pdf, .docx, .txt, .html, .md
   - Resolves relative URLs
       ↓
3. Download Documents (PARALLEL)
   (via Download MCP Server)
   - Configurable parallelism: DOWNLOAD_PARALLELISM
   - Saves to temp files
       ↓
4. Chunk Documents (PARALLEL)
   (LLM-based semantic chunking)
   - Uses Smart Ingestion prompt
   - Configurable parallelism: CHUNKING_PARALLELISM
   - Cleans up temp files
       ↓
5. Ingest Chunks (PARALLEL)
   (to Vector Database)
   - Configurable parallelism: INGESTION_PARALLELISM
   - Rich metadata preserved
       ↓
Results displayed to user
```

## Configuration

### Environment Variables

Add these to your `.env` file to control parallelism:

```bash
# Base parallelism (used as default for all stages)
PARALLELISM=8

# Stage-specific parallelism (overrides PARALLELISM)
DOWNLOAD_PARALLELISM=8      # Number of concurrent downloads
CHUNKING_PARALLELISM=4      # Number of concurrent LLM chunking operations
INGESTION_PARALLELISM=4     # Number of concurrent vector DB ingestions

# Optional: Limit documents per page
MAX_DOCUMENTS_PER_PAGE=10   # Default limit for web page processing
```

## Usage

### Via Web Interface

1. Navigate to **RAG Functions** → **Smart Ingestion**
2. Select **"Process Web Page"** mode
3. Enter the web page URL (e.g., `https://example.com/standards`)
4. Set maximum documents to process (default: 10)
5. Select or customize your chunking prompt
6. Click **"Process Web Page"**
7. Monitor progress in real-time
8. Review detailed results

### Via API

```bash
curl -X POST http://localhost:5000/api/rag/process_web_page \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://example.com/documents",
    "prompt": "# Your chunking prompt...",
    "ingest_chunks": true,
    "max_documents": 10
  }'
```

### Response Format

```json
{
  "page_url": "https://example.com/documents",
  "documents_to_process": 10,
  "documents_downloaded": 8,
  "documents_chunked": 8,
  "chunks_generated": 156,
  "documents_ingested": 8,
  "processing_time": 245.67,
  "document_results": [
    {
      "filename": "GOST_R_12345-2020.pdf",
      "url": "https://example.com/docs/gost.pdf",
      "chunks": 23,
      "status": "success"
    }
  ],
  "errors": [
    {
      "url": "https://example.com/docs/missing.pdf",
      "stage": "download",
      "error": "404 Not Found"
    }
  ]
}
```

## Features

### Document Link Extraction

- **Supported Formats**: PDF, DOCX, TXT, HTML, MD
- **URL Resolution**: Automatically resolves relative URLs
- **Pattern Matching**: Recognizes common document path patterns (`/docs/`, `/papers/`, etc.)

### Parallel Processing

Each stage has configurable parallelism:

| Stage | Default | Configurable Via |
|-------|---------|------------------|
| Download | 8 | `DOWNLOAD_PARALLELISM` |
| Chunking | 4 | `CHUNKING_PARALLELISM` |
| Ingestion | 4 | `INGESTION_PARALLELISM` |

### Error Handling

- **Graceful Degradation**: Continues processing even if some documents fail
- **Detailed Error Reporting**: Each error includes stage, filename/URL, and error message
- **Temp File Cleanup**: Automatically cleans up temporary files after processing

### Integration

- **Download MCP Server**: Uses existing MCP download service for document retrieval
- **Smart Ingestion Prompts**: Reuses existing prompt management system
- **Vector Store**: Integrates with existing Chroma/Qdrant setup

## Architecture

### Backend Components

```
/backend/services/rag/
├── smart_ingestion.py           # Original smart ingestion (file upload)
├── smart_ingestion_enhanced.py  # NEW: Web page processing
└── app.py                       # RAG service (routes registered here)

/backend/services/gateway/
└── app.py                       # Gateway proxy routes
```

### Key Functions

1. **`extract_document_links_from_page(page_url, html_content)`**
   - Parses HTML with BeautifulSoup
   - Extracts links to supported document formats
   - Resolves relative URLs

2. **`download_document_via_mcp(url)`**
   - Discovers Download MCP service via registry
   - Calls MCP download endpoint
   - Saves content to temp file

3. **`chunk_document_with_llm(file_path, prompt, filename)`**
   - Loads document content
   - Calls LLM with chunking prompt
   - Parses JSON response

4. **`ingest_chunks_to_vectorstore(chunks, document_id, filename)`**
   - Creates LangChain Document objects
   - Adds to vector store with metadata

## Performance Considerations

### Processing Time Estimates

| Operation | Time per Document | Notes |
|-----------|------------------|-------|
| Web page fetch | 1-3 seconds | One-time |
| Link extraction | < 1 second | One-time |
| Download (parallel) | 2-5 seconds | Per document, parallelized |
| LLM chunking (parallel) | 10-30 seconds | Per document, parallelized |
| Ingestion (parallel) | 1-3 seconds | Per document, parallelized |

**Total for 10 documents**: ~2-5 minutes (with parallelism)

### Resource Usage

- **Memory**: Proportional to `PARALLELISM` setting
- **CPU**: LLM chunking is most intensive
- **Network**: Download stage uses most bandwidth
- **Disk**: Temporary files cleaned up automatically

## Troubleshooting

### Common Issues

**"No document links found on the page"**
- Ensure the page contains links to supported formats (.pdf, .docx, etc.)
- Check if links are JavaScript-rendered (not supported yet)

**"No documents were successfully downloaded"**
- Verify Download MCP server is running
- Check if URLs are accessible
- Review download service logs

**"Failed to parse LLM response"**
- LLM may not have returned valid JSON
- Check LLM service is running
- Try a simpler prompt or smaller document

**Timeout errors**
- Increase timeout in gateway route (default: 600s)
- Reduce `max_documents` setting
- Check LLM service performance

## Future Enhancements

Potential improvements:
1. Support for JavaScript-rendered pages (Selenium/Playwright)
2. Recursive crawling (follow links within same domain)
3. Document type filtering UI
4. Progress streaming (real-time updates)
5. Batch URL processing (multiple pages at once)
6. Download caching (skip already processed documents)

## Files Modified/Created

### Created:
- `/backend/services/rag/smart_ingestion_enhanced.py` - Web page processing workflow
- `/SMART_INGESTION_WEB_PAGE_FEATURE.md` - This documentation

### Modified:
- `/backend/web_client/index.html` - Added web page UI and JavaScript
- `/backend/services/rag/app.py` - Registered enhanced routes
- `/backend/services/gateway/app.py` - Added proxy route

## Testing Checklist

- [ ] Web page URL input works
- [ ] Mode switching (Upload ↔ Web Page) works
- [ ] Document link extraction works
- [ ] Parallel downloads work
- [ ] LLM chunking works for downloaded documents
- [ ] Vector DB ingestion works
- [ ] Progress bar updates correctly
- [ ] Error handling displays properly
- [ ] Results summary is accurate
- [ ] Temp files are cleaned up

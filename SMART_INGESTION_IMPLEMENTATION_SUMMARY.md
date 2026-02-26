# Smart Ingestion Feature Implementation Summary

## Overview
The Smart Ingestion feature adds a new subtab to the "RAG Functions" tab that enables LLM-powered intelligent document chunking before ingestion into the vector database. This is particularly useful for technical standards (GOST, ISO, IEC, RFC) with complex structures like formulas, tables, and procedural sequences.

## Features Implemented

### 1. Backend Components

#### Smart Ingestion Service (`/backend/services/rag/smart_ingestion.py`)
A new Flask service that handles:

**Prompt Management Endpoints:**
- `GET /api/rag/prompts` - List all saved prompts
- `GET /api/rag/prompts/<prompt_id>` - Get a specific prompt
- `POST /api/rag/prompts` - Save a new prompt
- `PUT /api/rag/prompts/<prompt_id>` - Update an existing prompt
- `DELETE /api/rag/prompts/<prompt_id>` - Delete a prompt

**Smart Ingestion Endpoints:**
- `POST /api/rag/smart_ingest` - Complete smart ingestion workflow (upload + LLM chunking + ingest)
- `POST /api/rag/chunk_document` - Chunk a document without ingestion (preview mode)

**Key Features:**
- Default prompt optimized for Russian technical standards (GOST)
- Semantic-aware chunking that preserves formulas, tables, and procedural sequences
- Metadata generation for each chunk (section, chunk_type, formula detection, etc.)
- Targeted overlap only at procedural boundaries (30-50 tokens)
- Zero overlap for discrete sections

#### Gateway Routes (`/backend/services/gateway/app.py`)
Added proxy routes to forward smart ingestion requests to the RAG service:
- All prompt management endpoints
- Smart ingestion endpoint with multipart form data support
- Chunk document endpoint

#### RAG Service Integration (`/backend/services/rag/app.py`)
- Automatic registration of smart ingestion routes on startup
- Seamless integration with existing RAG functionality

### 2. Frontend Components

#### Web Client (`/backend/web_client/index.html`)

**New "Smart Ingestion" Subtab** with:

**Prompt Management Section:**
- Dropdown to select from saved prompts
- Large textarea for editing prompt content
- Save/Update/Delete/Reset buttons
- Form to save new prompts with name and description

**File Upload Section:**
- Drag-and-drop zone for file uploads
- Multiple file selection support
- File list with size display

**Ingestion Options:**
- Checkbox to enable/disable immediate ingestion
- Preview mode available (chunk without ingest)

**Progress & Results Display:**
- Real-time progress bar
- Status messages during processing
- Detailed results per file
- Generated chunks preview

**JavaScript Functionality:**
- Prompt loading on page load
- Prompt CRUD operations
- File upload handling with drag-and-drop
- Smart ingestion workflow with progress tracking
- Error handling and user feedback

### 3. Default Prompt Template

The system includes a comprehensive default prompt optimized for:
- **Technical Standards**: GOST, ISO, IEC, RFC documents
- **Semantic Preservation**: Formulas, tables, definitions, procedures
- **Chunk Size**: 200-450 tokens target
- **Overlap Strategy**: Targeted only at procedural boundaries
- **Metadata Generation**: Section IDs, chunk types, formula detection
- **Russian Language Support**: Preserves «ёлочки» quotes, ГОСТ references, mathematical notation

## Architecture

```
User Interface (Web Client)
        ↓
API Gateway (port 5000)
        ↓
RAG Service (port 5003)
        ↓
┌─────────────────────────────────┐
│  Smart Ingestion Workflow:      │
│  1. Upload files                │
│  2. Extract content             │
│  3. Send to LLM with prompt     │
│  4. Parse JSON chunking result  │
│  5. Ingest chunks to vector DB  │
└─────────────────────────────────┘
        ↓
Vector Store (Chroma/Qdrant)
```

## Files Modified/Created

### Created:
1. `/backend/services/rag/smart_ingestion.py` - Smart ingestion service (new)
2. `/data/smart_ingestion_prompts/` - Directory for saved prompts (created on first use)

### Modified:
1. `/backend/web_client/index.html` - Added Smart Ingestion subtab UI and JavaScript
2. `/backend/services/gateway/app.py` - Added smart ingestion proxy routes
3. `/backend/services/rag/app.py` - Integrated smart ingestion routes

## Usage Instructions

### 1. Access the Smart Ingestion Tab
1. Open the web client at `https://localhost` (or your configured URL)
2. Click on "RAG Functions" tab
3. Click on "Smart Ingestion" subtab

### 2. Select or Create a Prompt
1. Choose from the dropdown menu or use the default prompt
2. Edit the prompt content if needed
3. Save custom prompts for reuse

### 3. Upload Documents
1. Drag and drop files or click to browse
2. Select supported formats: PDF, DOCX, TXT, HTML, MD
3. Choose whether to ingest immediately or just preview chunks

### 4. Start Smart Ingestion
1. Click "Start Smart Ingestion"
2. Monitor progress in real-time
3. Review results when complete

### 5. Review Results
- Total files processed
- Success/error count per file
- Total chunks generated
- Processing time
- Chunk preview

## API Examples

### Save a Custom Prompt
```bash
curl -X POST http://localhost:5000/api/rag/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "My Custom Chunking Prompt",
    "description": "Optimized for scientific papers",
    "content": "# Your prompt content here..."
  }'
```

### Smart Ingest a Document
```bash
curl -X POST http://localhost:5000/api/rag/smart_ingest \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@document.pdf" \
  -F "prompt=# Your chunking prompt..." \
  -F "ingest_chunks=true"
```

### Chunk Document (Preview Mode)
```bash
curl -X POST http://localhost:5000/api/rag/chunk_document \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": "Document text content...",
    "prompt": "# Your chunking prompt...",
    "filename": "document.txt"
  }'
```

## Testing Checklist

- [ ] Prompt dropdown loads on tab switch
- [ ] Default prompt is displayed correctly
- [ ] Save new prompt works
- [ ] Update existing prompt works
- [ ] Delete prompt works (not default)
- [ ] Reset to default prompt works
- [ ] File upload via drag-and-drop works
- [ ] File upload via click-to-browse works
- [ ] Multiple file selection works
- [ ] Smart ingestion starts successfully
- [ ] Progress bar updates during processing
- [ ] Results display correctly
- [ ] Chunks are ingested into vector DB
- [ ] Preview mode (no ingest) works
- [ ] Error handling displays user-friendly messages

## Configuration

### Environment Variables
No new environment variables required. The feature uses existing LLM configuration:
- `RESPONSE_LLM_PROVIDER` - LLM provider for chunking
- `RESPONSE_LLM_MODEL` - LLM model for chunking

### Storage
- **Prompts**: Stored in `/data/smart_ingestion_prompts/` as JSON files
- **Uploaded Files**: Processed temporarily, cleaned up after ingestion

## Performance Considerations

- **LLM Calls**: Each document requires one LLM call for chunking
- **Processing Time**: Varies by document size and LLM speed (typically 10-60 seconds per document)
- **Token Limits**: Documents are limited to 500K characters to fit within LLM context windows
- **Timeout**: 12-hour timeout for large batch processing

## Future Enhancements

Potential improvements for future versions:
1. Batch processing queue for large document sets
2. Chunk preview before ingestion
3. Manual chunk editing interface
4. Chunk quality scoring/validation
5. A/B testing for different prompts
6. Export chunks as JSON
7. Import pre-chunked JSON from external sources

## Troubleshooting

### Common Issues

**"Failed to load prompts"**
- Check RAG service is running
- Verify authentication token is valid
- Check browser console for errors

**"Smart ingestion failed"**
- Verify LLM provider is configured and accessible
- Check document size (max 500K characters)
- Review RAG service logs for detailed error

**"Prompt not saving"**
- Ensure `/data/smart_ingestion_prompts/` directory exists and is writable
- Check prompt name is unique
- Verify prompt content meets minimum length (10 chars)

**"Chunks not appearing in search"**
- Verify ingestion completed successfully
- Check vector store is properly configured
- Try querying with different terms

## Security Notes

- All endpoints require `WRITE_RAG` permission
- File uploads validated for type and size
- Prompt content sanitized (except for template variables)
- Temporary files cleaned up after processing
- JWT token required for all API calls

## Conclusion

The Smart Ingestion feature provides a powerful, LLM-driven approach to document chunking that preserves semantic integrity while optimizing for vector search. The default prompt is specifically tuned for technical standards but can be customized for any document type through the prompt management interface.

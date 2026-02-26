# GraphRAG Smart Ingestion Workflow

**Version**: 1.0.0  
**Date**: 2026-02-24  
**Status**: ✅ Implementation Complete - Ready for Testing

---

## 📋 Overview

The GraphRAG Smart Ingestion system provides a unified interface for document processing with three source types and three processing modes, enabling flexible RAG (Retrieval Augmented Generation) pipelines with hybrid vector + graph search capabilities.

---

## 🎯 Architecture

### Source Types

| Source | Description | Use Case |
|--------|-------------|----------|
| **Upload Files** | Direct file upload (PDF, DOCX, TXT, MD, HTML) | Local documents, manual uploads |
| **Process Web Page** | Extract documents from web page URLs | Automated collection from web portals |
| **Import from Store** | Select from existing Document Store jobs | Re-processing, hybrid workflows |

### Processing Modes

| Mode | Description | Output |
|------|-------------|--------|
| **Download Only** | Cache documents without processing | Files stored in Document Store |
| **Vector RAG** | Chunk + ingest to vector database (Qdrant) | Vector embeddings for semantic search |
| **Hybrid Graph RAG** | Vector RAG + entity extraction to Neo4j | Vector + graph knowledge base |

---

## 🏗️ System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (index.html)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Upload Files │  │ Process Web  │  │ Import from Doc Store│  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └─────────────────┼──────────────────────┘              │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │ Processing Mode │                            │
│                  │   Selector      │                            │
│                  └────────┬────────┘                            │
└───────────────────────────┼─────────────────────────────────────┘
                            │ HTTP POST /api/rag/unified_ingest
┌───────────────────────────▼─────────────────────────────────────┐
│              BACKEND (smart_ingestion_unified.py)               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Document Store Client (document_store_client.py)        │  │
│  │  - list_ingestion_jobs                                   │  │
│  │  - list_documents                                        │  │
│  │  - get_document_batch                                    │  │
│  │  - search_documents                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Processing Pipeline                                     │  │
│  │  1. Download/Retrieve documents                          │  │
│  │  2. Chunk with LLM (smart chunking prompt)               │  │
│  │  3. Vector ingestion (Qdrant)                            │  │
│  │  4. Entity extraction (GraphRAG service)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
┌────────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│  Document Store │ │   Qdrant    │ │     Neo4j       │
│    MCP Server   │ │  Vector DB  │ │   Graph DB      │
│   Port 3070     │ │  Port 6333  │ │  Port 7687      │
│                 │ │             │ │  (remote)       │
│  - File storage │ │  - Embed-   │ │  - Entities     │
│  - Metadata     │ │    dings    │ │  - Relations    │
│  - Index        │ │  - Search   │ │  - Graph search │
└─────────────────┘ └─────────────┘ └─────────────────┘
```

---

## 🚀 API Reference

### Unified Ingestion Endpoint

**POST** `/api/rag/unified_ingest`

#### Request Body

```json
{
  "source_type": "file|web|document_store",
  "processing_mode": "download_only|vector_rag|hybrid_graph_rag",
  "prompt": "chunking prompt template",
  
  // For source_type: "file"
  "files": [<multipart form data>],
  
  // For source_type: "web"
  "url": "https://example.com/documents",
  "max_documents": 10,
  "use_background": false,
  
  // For source_type: "document_store"
  "job_id": "job_12345",
  "doc_ids": ["doc_001", "doc_002"]  // empty = all documents
}
```

#### Response

```json
{
  "source_type": "file",
  "processing_mode": "hybrid_graph_rag",
  "documents_processed": 5,
  "documents_chunked": 5,
  "chunks_generated": 47,
  "documents_ingested": 5,
  "entities_extracted": 123,
  "processing_time": 45.67,
  "document_results": [
    {
      "filename": "document1.pdf",
      "document_id": "doc_001",
      "chunks": 12,
      "status": "hybrid_processed",
      "vector_ingested": true,
      "graph_extracted": true,
      "entities_count": 28
    }
  ],
  "errors": []
}
```

---

### Document Store Endpoints

#### List Ingestion Jobs

**GET** `/api/rag/document_store/jobs`

**Query Parameters:**
- `status` (optional): Filter by job status
- `limit` (optional): Maximum results (default: 100)

**Response:**
```json
{
  "success": true,
  "jobs": [
    {
      "job_id": "job_12345",
      "document_count": 15,
      "status": "completed",
      "created_at": "2026-02-24T10:30:00Z"
    }
  ],
  "total": 1,
  "document_store_available": true
}
```

#### List Job Documents

**GET** `/api/rag/document_store/jobs/{job_id}/documents`

**Query Parameters:**
- `search` (optional): Search query for filtering
- `limit` (optional): Maximum results (default: 100)

**Response:**
```json
{
  "success": true,
  "job_id": "job_12345",
  "documents": [
    {
      "doc_id": "doc_001",
      "metadata": {
        "filename": "GOST_R_12345-2020.pdf",
        "format": "pdf",
        "size_bytes": 1024000
      }
    }
  ],
  "total": 1
}
```

#### Search Documents

**GET** `/api/rag/document_store/search?q={query}`

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Maximum results (default: 50)

---

### GraphRAG Entity Extraction Endpoint

**POST** `/api/rag/graphrag/extract_entities`

**Request:**
```json
{
  "document_id": "doc_001",
  "chunks": [
    {
      "chunk_id": 1,
      "content": "chunk text content...",
      "metadata": {...}
    }
  ],
  "prompt_template": "optional custom prompt"
}
```

**Response:**
```json
{
  "document_id": "doc_001",
  "entities_count": 28,
  "relationships_count": 15,
  "entities": [
    {
      "id": "gost_r_12345_2020",
      "name": "GOST R 12345-2020",
      "type": "Document",
      "description": "Russian technical standard",
      "metadata": {
        "source_chunk": 1,
        "confidence": 0.95
      }
    }
  ],
  "relationships": [
    {
      "source": "gost_r_12345_2020",
      "target": "information_security",
      "type": "GOVERNS",
      "description": "Standard governs security requirements",
      "metadata": {
        "source_chunk": 1,
        "confidence": 0.9
      }
    }
  ],
  "neo4j_result": {
    "entities_stored": 28,
    "relationships_stored": 15
  }
}
```

---

## 🧪 Testing Guide

### 1. Test File Upload + Vector RAG

```bash
curl -X POST http://localhost:5000/api/rag/unified_ingest \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "source_type=file" \
  -F "processing_mode=vector_rag" \
  -F "prompt=Default smart chunking prompt..." \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"
```

### 2. Test Web Page + Hybrid Graph RAG

```bash
curl -X POST http://localhost:5000/api/rag/unified_ingest \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "web",
    "processing_mode": "hybrid_graph_rag",
    "url": "https://example.com/standards",
    "max_documents": 5,
    "prompt": "Default smart chunking prompt..."
  }'
```

### 3. Test Document Store Import

```bash
# First, list available jobs
curl -X GET http://localhost:5000/api/rag/document_store/jobs \
  -H "Authorization: Bearer YOUR_TOKEN"

# Then import from store
curl -X POST http://localhost:5000/api/rag/unified_ingest \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "document_store",
    "processing_mode": "hybrid_graph_rag",
    "job_id": "job_12345",
    "doc_ids": ["doc_001", "doc_002"],
    "prompt": "Default smart chunking prompt..."
  }'
```

### 4. Test GraphRAG Entity Extraction Directly

```bash
curl -X POST http://192.168.51.187:8000/extract_entities \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "test_doc",
    "chunks": [
      {
        "chunk_id": 1,
        "content": "GOST R 12345-2020 establishes requirements for information security..."
      }
    ]
  }'
```

---

## 📊 Monitoring

### Check Service Health

```bash
# Smart Ingestion Service
curl http://localhost:5005/health

# Document Store MCP Server
curl -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# GraphRAG Service
curl http://192.168.51.187:8000/health

# Neo4j Graph Database
cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n) as entity_count"
```

### View Graph Statistics

```bash
curl http://192.168.51.187:8000/graph_stats
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Document Store
export DOCUMENT_STORE_URL=http://127.0.0.1:3070/mcp
export DOCUMENT_STORE_ENABLED=true

# GraphRAG
export GRAPHRAG_SERVICE_URL=http://192.168.51.187:8000
export GRAPHRAG_ENABLED=true
export NEO4J_URI=bolt://192.168.51.187:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password
export GRAPH_LLM_PROVIDER=openai
export GRAPH_LLM_MODEL=gpt-4

# Smart Ingestion
export SMART_INGESTION_BACKGROUND_THRESHOLD=50
export DOWNLOAD_PARALLELISM=4
export CHUNKING_PARALLELISM=4
export INGESTION_PARALLELISM=4
```

---

## 📁 File Structure

```
/root/qwen/ai_agent/
├── backend/
│   ├── services/
│   │   └── rag/
│   │       ├── smart_ingestion_unified.py    # Main unified ingestion service
│   │       ├── smart_ingestion_enhanced.py   # Legacy web page processing
│   │       ├── smart_ingestion.py            # Legacy file upload
│   │       ├── document_store_client.py      # Document Store MCP client
│   │       └── graphrag_service.py           # GraphRAG entity extraction
│   └── web_client/
│       └── index.html                        # Frontend UI (updated)
│
├── document-store-mcp-server/
│   └── document_store_server/
│       ├── server.py                         # MCP server
│       ├── handlers/
│       │   └── document_handlers.py          # 8 document operation handlers
│       └── storage/
│           ├── file_storage.py               # File system backend
│           ├── metadata_manager.py           # Metadata management
│           └── document_index.py             # Indexing & search
│
└── GRAPHRAG_WORKFLOW.md                      # This documentation
```

---

## 🎯 Use Cases

### 1. Technical Standards Processing

**Scenario**: Process Russian GOST standards for semantic search

1. **Source**: Upload PDF files or import from existing jobs
2. **Mode**: Hybrid Graph RAG
3. **Result**: 
   - Semantic chunks in Qdrant for similarity search
   - Entities (standards, requirements, concepts) in Neo4j
   - Relationships (references, implements, governs)

### 2. Web Portal Harvesting

**Scenario**: Extract documents from government/corporate portals

1. **Source**: Process Web Page URL
2. **Mode**: Download Only (initial), then Vector RAG
3. **Result**: 
   - Documents cached in Document Store
   - Selective re-processing with different modes

### 3. Iterative Refinement

**Scenario**: Re-process documents with improved prompts

1. **Source**: Import from Document Store
2. **Mode**: Vector RAG with custom prompt
3. **Result**: 
   - Improved chunking without re-downloading
   - A/B testing of prompts

---

## ⚠️ Important Notes

1. **Neo4j Remote Server**: The GraphRAG service expects Neo4j at `192.168.51.187:7687`. Update `NEO4J_URI` if different.

2. **LLM Provider**: Entity extraction uses the configured LLM provider. Ensure API keys are set.

3. **Document Store Dependency**: The Document Store MCP Server (port 3070) must be running for document store imports.

4. **Background Processing**: For >50 documents, use `use_background: true` to process asynchronously.

5. **Token Limits**: Document text is truncated to 50K characters for entity extraction to avoid LLM token limits.

---

## 🐛 Troubleshooting

### Document Store Not Available

```bash
# Check if Document Store is running
curl http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# Restart if needed
cd /root/qwen/ai_agent/document-store-mcp-server
./start_document_store.sh
```

### GraphRAG Service Unreachable

```bash
# Check GraphRAG health
curl http://192.168.51.187:8000/health

# Verify Neo4j connection
cypher-shell -u neo4j -p password -a bolt://192.168.51.187:7687 "RETURN 1"
```

### Entity Extraction Failing

- Check LLM API key is configured
- Verify document chunks are not empty
- Review logs for parsing errors

---

## 📈 Future Enhancements

- [ ] Vector embeddings in Document Store for hybrid search
- [ ] Caching layer (Redis) for frequently accessed documents
- [ ] Authentication/API keys for Document Store
- [ ] Incremental entity updates (avoid re-extraction)
- [ ] Graph visualization in frontend
- [ ] Advanced search combining vector + graph results

---

**Implementation Status**: ✅ Complete  
**Test Status**: ⏳ Pending  
**Ready for Production**: After testing

---

## 📞 Support

For issues or questions:
1. Check service health endpoints
2. Review logs in respective service directories
3. Verify configuration environment variables
4. Test individual components before full workflow

---

**Last Updated**: 2026-02-24  
**Version**: 1.0.0

# Document Storage & Retrieval MCP Server - Analysis & Proposal

**Date**: 2026-02-24  
**Context**: Need to provide MCP-based access to PDF documents downloaded during smart ingestion

---

## 📊 Current Situation Analysis

### What We Know

1. **Smart Ingestion Process** downloads PDF documents via an MCP download server
2. **Documents are stored** somewhere (likely in `/root/qwen/ai_agent/backend/services/rag/` based on job recovery scripts)
3. **Redis tracks jobs** with keys like `smart_ingestion_job:{job_id}`
4. **116 documents were downloaded** for job `job_db128a16815d` (from recovery script)

### Current Gap

❌ **No MCP interface to retrieve full document content**
- Documents are downloaded but not easily accessible via MCP
- GraphRAG needs document content for entity extraction
- IT Lead agents can't reference original documents
- No standardized way to serve document content to other MCP servers

---

## 🔍 MCP Server Patterns for Document Serving

Based on research and MCP best practices, here are the proven patterns:

### Pattern 1: **Resource-Based Document Server** (Recommended for Read-Only Access)

```
MCP Server exposes:
├── Resources (passive data containers)
│   ├── document://{job_id}/{doc_id}  - Individual documents
│   ├── document://{job_id}/metadata  - Document metadata
│   └── document://latest             - Most recent ingestion
├── Tools (active operations)
│   ├── get_document_content          - Retrieve full text
│   ├── get_document_metadata         - Get metadata
│   ├── list_job_documents            - List all docs in job
│   └── search_documents              - Search within documents
```

**Pros:**
- ✅ Follows MCP resource pattern (standard for data access)
- ✅ Clean separation: resources for data, tools for operations
- ✅ Supports streaming for large documents
- ✅ Built-in metadata support

**Cons:**
- ❌ Requires implementing resource handlers
- ❌ More complex than simple tool-based approach

**Best For:** Read-only document access with metadata

---

### Pattern 2: **Tool-Based Document Server** (Simpler)

```
MCP Server exposes only Tools:
├── get_document(job_id, doc_id) → {content, metadata}
├── list_documents(job_id) → [{doc_id, filename, size, ...}]
├── search_documents(job_id, query) → [{doc_id, snippets, ...}]
└── get_document_batch(job_id, [doc_ids]) → [{doc_id, content, ...}]
```

**Pros:**
- ✅ Simpler implementation (tools only, no resources)
- ✅ Familiar API pattern (function calls)
- ✅ Easy to add filtering, pagination, search
- ✅ Can return structured responses

**Cons:**
- ❌ Less "MCP-native" than resource pattern
- ❌ No automatic resource discovery

**Best For:** Quick implementation, operational access

---

### Pattern 3: **Hybrid File System + MCP Server** (Most Flexible)

```
┌─────────────────────────────────────────────────────┐
│  File System Storage                                │
│  /var/documents/ingested/                           │
│  ├── {job_id}/                                      │
│  │   ├── documents/                                 │
│  │   │   ├── {doc_id}.pdf                          │
│  │   │   ├── {doc_id}.txt                          │
│  │   │   └── {doc_id}.metadata.json                │
│  │   └── index.json                                 │
│  └── ...                                            │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  MCP Server (FastAPI + MCP SDK)                     │
│  - Reads from file system                           │
│  - Exposes via MCP resources/tools                  │
│  - Adds authentication, caching, search             │
└─────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Documents persist independently of MCP server
- ✅ Can serve via HTTP API AND MCP
- ✅ Easy backup, migration, inspection
- ✅ Supports multiple access patterns

**Cons:**
- ❌ More infrastructure (file system management)
- ❌ Need to handle file permissions, cleanup

**Best For:** Production deployments with multiple access needs

---

### Pattern 4: **Database-Backed Document Store** (Enterprise)

```
┌─────────────────────────────────────────────────────┐
│  PostgreSQL Database                                │
│  documents:                                         │
│  - id, job_id, filename, content (text)             │
│  - metadata (JSONB), embeddings (vector)            │
│  - created_at, updated_at                           │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  MCP Server                                         │
│  - Queries database                                 │
│  - Exposes via MCP                                  │
│  - Full-text search, vector search                  │
└─────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ ACID compliance, transactions
- ✅ Full-text search built-in
- ✅ Can store embeddings alongside content
- ✅ Easy to query, filter, aggregate

**Cons:**
- ❌ Database overhead for simple file storage
- ❌ Large text blobs in DB can be slow
- ❌ More complex backup/recovery

**Best For:** Enterprise deployments with existing PostgreSQL

---

## 🎯 Recommended Approach

### **Option A: Extend Existing Download Server** (If It Exists)

**IF** there's already an MCP download server that downloaded the documents:

```yaml
Decision: Add document retrieval tools to existing server

Implementation:
  1. Add new tools to existing download server:
     - get_downloaded_document(job_id, doc_id)
     - list_downloaded_documents(job_id)
     - get_document_metadata(job_id, doc_id)
  
  2. Store documents in structured file system:
     /var/documents/ingested/{job_id}/{doc_id}.{pdf,txt,metadata.json}
  
  3. Add simple index file per job:
     /var/documents/ingested/{job_id}/index.json

Pros:
  - Minimal new infrastructure
  - Logical: download server already manages documents
  - Single server to maintain

Cons:
  - Need to find/understand existing download server code
  - May require refactoring existing server

Effort: 2-4 hours
```

---

### **Option B: Build New Document Server** (Recommended)

**Build a dedicated MCP Document Server** for storing and serving ingested documents:

```yaml
Decision: Build new "Document Store MCP Server"

Architecture:
  Storage: File system (/var/documents/ingested/)
  Server:  FastAPI + MCP SDK (following mcp-std-skeleton pattern)
  Port:    3070 (new port in your ecosystem)
  Tools:
    - list_ingestion_jobs() → [{job_id, status, doc_count, ...}]
    - list_documents(job_id) → [{doc_id, filename, size, ...}]
    - get_document(job_id, doc_id, format="txt|pdf|md") → {content, metadata}
    - get_document_batch(job_id, [doc_ids]) → [{doc_id, content, ...}]
    - search_documents(job_id, query) → [{doc_id, snippets, score, ...}]
    - delete_job_documents(job_id) → {deleted_count, ...}

Integration:
  - GraphRAG service calls this server to get documents for entity extraction
  - IT Lead agents can retrieve original documents for reference
  - RAG service can store downloaded documents here

Pros:
  - Clean separation of concerns
  - Reusable across projects
  - Follows your existing MCP server pattern
  - Can add features (search, caching, auth) later

Cons:
  - New server to deploy and maintain
  - ~1 day implementation time

Effort: 6-8 hours
```

---

### **Option C: Use GraphRAG Neo4j for Document Storage** (Consolidated)

**Store documents in the Neo4j graph database** we just deployed:

```yaml
Decision: Store documents in Neo4j alongside entities

Schema:
  (d:Document {
    id: "doc_123",
    job_id: "job_db128a16815d",
    filename: "api_guide.pdf",
    content: "Full text content...",
    metadata: {size: 12345, pages: 10, ...},
    embedding: [0.123, ...]  # Optional vector embedding
  })

Tools (via GraphRAG API):
  - POST /documents/{job_id}/list
  - GET /documents/{job_id}/{doc_id}
  - POST /documents/search

Pros:
  - No new infrastructure (use existing Neo4j)
  - Documents and entities in same database
  - Can query documents + entities together
  - Vector search ready

Cons:
  - Neo4j not optimized for large text blobs
  - Mixing operational data (documents) with graph data (entities)
  - May need to increase Neo4j memory/disk

Effort: 4-6 hours
```

---

## 📋 Implementation Comparison

| Aspect | Option A: Extend Existing | Option B: New Server | Option C: Neo4j Storage |
|--------|--------------------------|----------------------|------------------------|
| **Implementation Time** | 2-4 hours | 6-8 hours | 4-6 hours |
| **New Infrastructure** | None | 1 server | None (use existing) |
| **Code Complexity** | Medium | Low-Medium | Low |
| **Scalability** | Depends on existing | High | Medium |
| **Query Performance** | Fast | Fast | Medium (for large text) |
| **Maintainability** | Medium | High | Medium |
| **Flexibility** | Medium | High | Low-Medium |
| **Best For** | Quick fix | Production system | Consolidated stack |

---

## 🎯 My Recommendation

### **Option B: Build New Document Store MCP Server**

**Rationale:**

1. **Clean Architecture**: Document storage is a distinct concern from downloading or graph processing
2. **Reusability**: Can be used by other projects, not tied to RAG/GraphRAG
3. **Follows Your Pattern**: You already have 5+ MCP servers using the same skeleton
4. **Scalability**: Can evolve independently (add caching, CDN, auth, etc.)
5. **Debugging**: Easy to inspect files directly, backup, migrate

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Document Store MCP Server (Port 3070)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Storage Backend: File System                          │  │
│  │ /var/documents/ingested/                              │  │
│  │ ├── {job_id}/                                         │  │
│  │ │   ├── documents/                                    │  │
│  │ │   │   ├── {doc_id}.pdf                             │  │
│  │ │   │   ├── {doc_id}.txt                             │  │
│  │ │   │   └── {doc_id}.metadata.json                   │  │
│  │ │   └── index.json                                    │  │
│  │  └── ...                                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  MCP Tools:                                                 │
│  - list_ingestion_jobs()                                    │
│  - list_documents(job_id)                                   │
│  - get_document(job_id, doc_id, format="txt|pdf|md")        │
│  - get_document_batch(job_id, [doc_ids])                    │
│  - search_documents(job_id, query)                          │
│  - delete_job_documents(job_id)                             │
└─────────────────────────────────────────────────────────────┘
                         ↑
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌─────▼────┐
    │GraphRAG │    │IT Lead  │    │Existing  │
    │Service  │    │Agents   │    │RAG       │
    │(port    │    │(port    │    │Service   │
    │8000)    │    │3061)    │    │          │
    └─────────┘    └─────────┘    └──────────┘
```

---

## 📝 Implementation Plan (Option B)

### Phase 1: Foundation (2-3 hours)

```bash
# 1. Create server directory structure
mkdir -p /root/qwen/base/document-store-mcp-server
cd /root/qwen/base/document-store-mcp-server

# 2. Copy skeleton from existing server
cp -r ../mcp-std-coder/mcp-vibe-coding-agent/mcp_std_server ./

# 3. Create main server file
cat > server.py << 'EOF'
# Document Store MCP Server
# Port: 3070
# Storage: /var/documents/ingested/
EOF

# 4. Create document storage utilities
mkdir -p utils
cat > utils/document_storage.py << 'EOF'
# File system document storage
# - save_document(job_id, doc_id, content, metadata)
# - get_document(job_id, doc_id, format="txt|pdf|md")
# - list_documents(job_id)
# - delete_job_documents(job_id)
EOF
```

### Phase 2: MCP Tools Implementation (2-3 hours)

```python
# In handlers/server_handlers.py
tools = [
    {
        "name": "list_ingestion_jobs",
        "description": "List all document ingestion jobs",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "list_documents",
        "description": "List documents in an ingestion job",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_document",
        "description": "Get document content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "doc_id": {"type": "string"},
                "format": {"type": "string", "enum": ["txt", "pdf", "md", "metadata"]}
            },
            "required": ["job_id", "doc_id"]
        }
    },
    {
        "name": "get_document_batch",
        "description": "Get multiple documents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "doc_ids": {"type": "array", "items": {"type": "string"}},
                "format": {"type": "string"}
            },
            "required": ["job_id", "doc_ids"]
        }
    },
    {
        "name": "search_documents",
        "description": "Search within documents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["job_id", "query"]
        }
    }
]
```

### Phase 3: Integration (1-2 hours)

```python
# 1. Update GraphRAG service to call document server
# In graphrag-service/app.py
DOCUMENT_STORE_URL = "http://localhost:3070/mcp"

def get_documents_for_entity_extraction(job_id: str):
    """Fetch documents from document store"""
    # Call MCP server to get documents
    pass

# 2. Test end-to-end flow
# Document download → Store in document server → GraphRAG extracts entities
```

### Phase 4: Deployment (1 hour)

```bash
# Start document store server
cd /root/qwen/base/document-store-mcp-server
python -m mcp_std_server.server --port 3070

# Test
curl -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

---

## 🔄 Alternative: Quick Start with Option C (Neo4j)

If you want to **move fast** and test the concept:

```python
# Add to existing GraphRAG service (graphrag-service/app.py)

@app.post("/documents/{job_id}/store")
async def store_document(job_id: str, doc_id: str, content: str, metadata: dict):
    """Store document in Neo4j"""
    d = get_driver()
    with d.session() as session:
        cypher = """
        MERGE (d:Document {id: $doc_id, job_id: $job_id})
        SET d.content = $content, d.metadata = $metadata, d.updated_at = datetime()
        """
        session.run(cypher, doc_id=doc_id, job_id=job_id, 
                   content=content, metadata=metadata)
    return {"success": True}

@app.get("/documents/{job_id}/{doc_id}")
async def get_document(job_id: str, doc_id: str):
    """Get document from Neo4j"""
    d = get_driver()
    with d.session() as session:
        result = session.run("""
        MATCH (d:Document {id: $doc_id, job_id: $job_id})
        RETURN d.content AS content, d.metadata AS metadata
        """, doc_id=doc_id, job_id=job_id)
        record = result.single()
        return {"content": record["content"], "metadata": record["metadata"]}
```

**Time**: 1-2 hours  
**Trade-off**: Faster, but Neo4j not optimized for large text

---

## 📊 Decision Matrix

| If your priority is... | Choose... |
|------------------------|-----------|
| **Speed** (test today) | Option C (Neo4j) - 2 hours |
| **Clean architecture** | Option B (New Server) - 6-8 hours |
| **Minimal new code** | Option A (Extend Existing) - 2-4 hours |
| **Production-ready** | Option B (New Server) |
| **Unified stack** | Option C (Neo4j) |

---

## 🎯 Next Steps

1. **Choose an option** (A, B, or C)
2. **I'll implement it** with full code
3. **Test integration** with GraphRAG and existing RAG
4. **Deploy** alongside other MCP servers

---

**Recommendation**: **Option B** (New Document Store MCP Server) for production, **Option C** (Neo4j) for quick POC

Would you like me to proceed with implementing one of these options?

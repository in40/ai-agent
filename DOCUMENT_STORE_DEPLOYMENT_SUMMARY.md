# Document Store MCP Server - Deployment Summary

**Date**: 2026-02-24  
**Status**: ✅ Deployed to /root/qwen/ai_agent/  
**Port**: 3070

---

## 📁 Location

```
/root/qwen/ai_agent/document-store-mcp-server/
├── document_store_server/      # Main server package
├── data/ingested/              # Document storage
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── start_document_store.sh     # Startup script
├── stop_document_store.sh      # Shutdown script
├── test_document_store.py      # Test suite
└── README.md                   # Documentation
```

---

## 🚀 Quick Start

### Start Document Store MCP Server
```bash
cd /root/qwen/ai_agent/document-store-mcp-server
./start_document_store.sh
```

### Stop Document Store MCP Server
```bash
./stop_document_store.sh
```

### Start ALL Services (including Document Store)
```bash
cd /root/qwen/ai_agent
./start_all_services.sh
```

---

## ✅ Integration with start_all_services.sh

The Document Store MCP Server has been added to the main startup script:

- **Line 298-311**: Startup code
- **Line 334**: Service list display
- **Port**: 3070
- **Log file**: `document_store_mcp_server.log`

When you run `./start_all_services.sh`, you'll see:
```
Starting Document Store MCP Server on port 3070...
Document Store MCP Server started with PID XXXXX
✓ Document Store MCP Server is responding
...
Document Store MCP:  http://localhost:3070
```

---

## 📋 MCP Tools (Port 3070)

| Tool | Description |
|------|-------------|
| `list_ingestion_jobs` | List all document ingestion jobs |
| `list_documents` | List documents for a job |
| `get_document` | Get document content |
| `get_document_batch` | Get multiple documents |
| `get_document_metadata` | Get document metadata |
| `search_documents` | Search within documents |
| `delete_job_documents` | Delete all documents for a job |
| `store_document` | Store a new document |

---

## 🧪 Testing

```bash
cd /root/qwen/ai_agent/document-store-mcp-server
python test_document_store.py
```

Or test manually:
```bash
curl -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

---

## 🔗 Integration Points

### With RAG Service (port 5003)
The RAG service can store downloaded documents in the Document Store for later retrieval.

### With GraphRAG (if deployed)
GraphRAG can retrieve documents from the Document Store for entity extraction.

### With Download MCP Server (port 8093)
Downloaded documents can be automatically stored in the Document Store.

---

## 📊 Service Status

When all services are running:
- ✅ Registry: port 8080
- ✅ DNS MCP: port 8089
- ✅ Search MCP: port 8090
- ✅ RAG MCP: port 8091
- ✅ SQL MCP: port 8092
- ✅ Download MCP: port 8093
- ✅ **Document Store: port 3070** ← NEW!

---

## 🛠️ Configuration

Edit `config.py` to customize:
```python
DOCUMENT_STORE_PORT = 3070
DOCUMENT_STORAGE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data"
MAX_DOCUMENT_SIZE_MB = 50
MAX_BATCH_SIZE = 100
```

---

## 📝 Next Steps

1. **Start the service**: `./start_document_store.sh`
2. **Run tests**: `python test_document_store.py`
3. **Integrate with RAG**: Update RAG service to store documents here
4. **Load production data**: Import existing ingestion job documents

---

**Deployment Complete!** 🎉

---

## 🔗 Registry Integration

### ai_agent Service Registry (Port 8080)

The Document Store MCP Server has been **modified to use the ai_agent registry protocol**:

**Changes Made:**
1. Created `document_store_server/utils/ai_agent_registry.py` - Wrapper for ai_agent registry client
2. Updated `document_store_server/server.py` - Integrated registry registration
3. Updated `config.py` - Changed registry port from 3031 to **8080**

**Registration Details:**
- **Service ID**: `document-store-127.0.0.1:3070`
- **Registry URL**: `http://127.0.0.1:8080`
- **TTL**: 60 seconds
- **Heartbeat**: Every 30 seconds

**When the server starts, you'll see:**
```
📝 Registering with ai_agent registry at http://127.0.0.1:8080...
✅ Registered as 'document-store-127.0.0.1:3070'
💓 Heartbeat started (interval: 30.0s)
```

**Other ai_agent services can now discover the Document Store** via the registry at port 8080.


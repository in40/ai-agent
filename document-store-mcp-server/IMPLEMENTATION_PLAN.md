# Document Store MCP Server - Implementation Plan

**Date**: 2026-02-24  
**Status**: Ready to Implement  
**Option**: B - Dedicated MCP Server  
**Port**: 3070

---

## 📁 Directory Structure

```
/root/qwen/base/document-store-mcp-server/
├── README.md                          # Server documentation
├── requirements.txt                   # Python dependencies
├── setup.py                          # Package setup
├── config.py                         # Configuration management
├── start_server.sh                   # Startup script
├── stop_server.sh                    # Shutdown script
├── test_document_store.py            # Test suite
│
├── document_store_server/            # Main server package
│   ├── __init__.py
│   ├── server.py                     # MCP server implementation
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── server_handlers.py        # Standard MCP handlers
│   │   ├── client_handlers.py        # Client method handlers
│   │   └── document_handlers.py      # Document operation handlers
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── file_storage.py           # File system storage backend
│   │   ├── document_index.py         # Document indexing & search
│   │   └── metadata_manager.py       # Metadata management
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── json_rpc.py               # JSON-RPC handling
│   │   ├── notifications.py          # MCP notifications
│   │   └── file_utils.py             # File utilities
│   └── transports/
│       ├── __init__.py
│       ├── stdio.py                  # STDIO transport
│       ├── http_sse.py               # HTTP/SSE transport
│       └── streamable_http.py        # Streamable HTTP transport
│
└── data/                             # Document storage (created on first run)
    └── ingested/
        └── {job_id}/
            ├── documents/
            │   ├── {doc_id}.pdf
            │   ├── {doc_id}.txt
            │   └── {doc_id}.metadata.json
            └── index.json
```

---

## 🎯 Implementation Phases

### Phase 1: Project Setup (30 minutes)

**Tasks:**
1. Create directory structure
2. Create requirements.txt
3. Create config.py
4. Create basic server.py skeleton

**Files to Create:**
- `requirements.txt`
- `config.py`
- `document_store_server/__init__.py`
- `document_store_server/server.py` (skeleton)

---

### Phase 2: Storage Backend (1-2 hours)

**Tasks:**
1. Implement file storage backend
2. Implement metadata manager
3. Implement document index
4. Test file operations

**Files to Create:**
- `document_store_server/storage/file_storage.py`
- `document_store_server/storage/metadata_manager.py`
- `document_store_server/storage/document_index.py`

**Key Functions:**
```python
# file_storage.py
- save_document(job_id, doc_id, content, format="txt") → path
- get_document(job_id, doc_id, format="txt") → content
- delete_document(job_id, doc_id) → bool
- list_documents(job_id) → [doc_id, ...]

# metadata_manager.py
- save_metadata(job_id, doc_id, metadata) → bool
- get_metadata(job_id, doc_id) → dict
- update_metadata(job_id, doc_id, updates) → dict

# document_index.py
- create_job_index(job_id, metadata) → bool
- add_document_to_index(job_id, doc_id, metadata) → bool
- get_job_index(job_id) → dict
- search_index(job_id, query) → [results]
```

---

### Phase 3: MCP Handlers (2-3 hours)

**Tasks:**
1. Implement document operation handlers
2. Define MCP tools
3. Implement tool execution
4. Add error handling

**Files to Create:**
- `document_store_server/handlers/document_handlers.py`

**MCP Tools to Implement:**
```python
tools = [
    {
        "name": "list_ingestion_jobs",
        "description": "List all document ingestion jobs",
        "handler": handle_list_ingestion_jobs
    },
    {
        "name": "list_documents",
        "description": "List documents in an ingestion job",
        "handler": handle_list_documents
    },
    {
        "name": "get_document",
        "description": "Get document content by ID",
        "handler": handle_get_document
    },
    {
        "name": "get_document_batch",
        "description": "Get multiple documents in one call",
        "handler": handle_get_document_batch
    },
    {
        "name": "get_document_metadata",
        "description": "Get document metadata",
        "handler": handle_get_document_metadata
    },
    {
        "name": "search_documents",
        "description": "Search within documents for a job",
        "handler": handle_search_documents
    },
    {
        "name": "delete_job_documents",
        "description": "Delete all documents for a job",
        "handler": handle_delete_job_documents
    },
    {
        "name": "store_document",
        "description": "Store a new document",
        "handler": handle_store_document
    }
]
```

---

### Phase 4: Server Integration (1 hour)

**Tasks:**
1. Integrate handlers with server
2. Add startup/shutdown logic
3. Configure storage paths
4. Test server startup

**Files to Modify:**
- `document_store_server/server.py`

---

### Phase 5: Scripts & Testing (1 hour)

**Tasks:**
1. Create startup script
2. Create stop script
3. Create test suite
4. Run tests

**Files to Create:**
- `start_server.sh`
- `stop_server.sh`
- `test_document_store.py`

---

### Phase 6: Integration with GraphRAG (1-2 hours)

**Tasks:**
1. Update GraphRAG service to call document server
2. Test document retrieval for entity extraction
3. Test end-to-end flow

**Files to Modify:**
- `/root/qwen/base/graphrag-service/app.py` (add document store client)

---

## 📋 Detailed File Templates

### requirements.txt
```
fastapi>=0.104.1
uvicorn>=0.24.0
pydantic>=2.0
requests>=2.31.0
python-multipart>=0.0.6
aiofiles>=23.2.1
```

### config.py
```python
"""Document Store MCP Server Configuration"""
import os
from pathlib import Path

# Server Configuration
SERVER_PORT = int(os.getenv("DOCUMENT_STORE_PORT", "3070"))
SERVER_HOST = os.getenv("DOCUMENT_STORE_HOST", "0.0.0.0")
TRANSPORT_TYPE = os.getenv("DOCUMENT_STORE_TRANSPORT", "streamable-http")

# Storage Configuration
STORAGE_BASE = Path(os.getenv("DOCUMENT_STORAGE_PATH", "/root/qwen/base/document-store-mcp-server/data"))
INGESTED_DIR = STORAGE_BASE / "ingested"

# Ensure directories exist
INGESTED_DIR.mkdir(parents=True, exist_ok=True)

# Server Configuration
ENABLE_REGISTRY = os.getenv("DOCUMENT_STORE_ENABLE_REGISTRY", "true").lower() == "true"
REGISTER_WITH_REGISTRY = os.getenv("DOCUMENT_STORE_REGISTER_WITH_REGISTRY", "true").lower() == "true"
REGISTRY_HOST = os.getenv("REGISTRY_HOST", "127.0.0.1")
REGISTRY_PORT = int(os.getenv("REGISTRY_PORT", "3031"))

# Performance
MAX_DOCUMENT_SIZE_MB = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "50"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
SEARCH_RESULTS_LIMIT = int(os.getenv("SEARCH_RESULTS_LIMIT", "50"))
```

### document_store_server/server.py (Skeleton)
```python
"""Document Store MCP Server Implementation"""
import signal
import sys
from typing import Optional
import argparse

from .utils.json_rpc import JsonRpcHandler
from .transports.stdio import StdioTransport
from .transports.http_sse import HttpSseTransport
from .transports.streamable_http import StreamableHttpTransport
from .handlers.server_handlers import DocumentStoreServerHandlers
from .handlers.client_handlers import ClientMethodsHandlers
from .utils.notifications import NotificationManager
from config import (
    SERVER_PORT, SERVER_HOST, TRANSPORT_TYPE,
    ENABLE_REGISTRY, REGISTER_WITH_REGISTRY, REGISTRY_HOST, REGISTRY_PORT
)


class DocumentStoreMcpServer:
    """Document Store MCP Server"""

    def __init__(self, transport_type: str = "streamable-http"):
        self.transport_type = transport_type
        self.host = SERVER_HOST
        self.port = SERVER_PORT
        self.running = False
        
        # Initialize components
        self.rpc_handler = JsonRpcHandler()
        self.notification_manager = NotificationManager(self.rpc_handler)
        
        # Initialize handlers
        self.client_handlers = ClientMethodsHandlers(self.rpc_handler)
        self.server_handlers = DocumentStoreServerHandlers(
            enable_registry=ENABLE_REGISTRY,
            notification_manager=self.notification_manager
        )
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down Document Store Server...")
        self.running = False
        sys.exit(0)

    def start(self):
        """Start the server"""
        print(f"🚀 Starting Document Store MCP Server on port {self.port}...")
        print(f"   Transport: {self.transport_type}")
        print(f"   Storage: {config.STORAGE_BASE}")
        print(f"   Registry: {'Enabled' if ENABLE_REGISTRY else 'Disabled'}")
        
        # Create transport
        if self.transport_type == "stdio":
            transport = StdioTransport(self.rpc_handler)
        elif self.transport_type == "http":
            transport = HttpSseTransport(
                host=self.host, 
                port=self.port,
                rpc_handler=self.rpc_handler
            )
        else:  # streamable-http
            transport = StreamableHttpTransport(
                host=self.host,
                port=self.port,
                rpc_handler=self.rpc_handler
            )
        
        # Start server
        self.running = True
        transport.start()


def main():
    parser = argparse.ArgumentParser(description="Document Store MCP Server")
    parser.add_argument("--transport", default=TRANSPORT_TYPE,
                       choices=["stdio", "http", "streamable-http"])
    parser.add_argument("--port", type=int, default=SERVER_PORT)
    
    args = parser.parse_args()
    
    server = DocumentStoreMcpServer(transport_type=args.transport)
    server.start()


if __name__ == "__main__":
    main()
```

---

## 🚀 Quick Start Commands

```bash
# Create directory structure
mkdir -p /root/qwen/base/document-store-mcp-server/document_store_server/{handlers,storage,utils,transports}
mkdir -p /root/qwen/base/document-store-mcp-server/data/ingested
cd /root/qwen/base/document-store-mcp-server

# Create files
touch requirements.txt config.py setup.py
touch document_store_server/__init__.py
touch document_store_server/server.py
touch document_store_server/handlers/{__init__.py,server_handlers.py,client_handlers.py,document_handlers.py}
touch document_store_server/storage/{__init__.py,file_storage.py,metadata_manager.py,document_index.py}
touch document_store_server/utils/{__init__.py,json_rpc.py,notifications.py,file_utils.py}
touch document_store_server/transports/{__init__.py,stdio.py,http_sse.py,streamable_http.py}

# Install dependencies
pip install -r requirements.txt

# Start server
python -m document_store_server.server --port 3070
```

---

## 🧪 Test Plan

### Unit Tests
```python
# test_document_store.py
def test_save_document():
    """Test saving a document"""
    pass

def test_get_document():
    """Test retrieving a document"""
    pass

def test_list_documents():
    """Test listing documents"""
    pass

def test_search_documents():
    """Test searching documents"""
    pass

def test_delete_job_documents():
    """Test deleting job documents"""
    pass
```

### Integration Tests
```python
# Test MCP tool calls
def test_list_documents_tool():
    """Test list_documents MCP tool"""
    pass

def test_get_document_tool():
    """Test get_document MCP tool"""
    pass

# Test end-to-end with GraphRAG
def test_graphrag_integration():
    """Test GraphRAG retrieves documents"""
    pass
```

---

## 📊 Timeline Summary

| Phase | Task | Duration |
|-------|------|----------|
| **Phase 1** | Project Setup | 30 min |
| **Phase 2** | Storage Backend | 1-2 hours |
| **Phase 3** | MCP Handlers | 2-3 hours |
| **Phase 4** | Server Integration | 1 hour |
| **Phase 5** | Scripts & Testing | 1 hour |
| **Phase 6** | GraphRAG Integration | 1-2 hours |
| **Total** | | **6-10 hours** |

---

## ✅ Deliverables

1. ✅ Working Document Store MCP Server (port 3070)
2. ✅ File system storage backend
3. ✅ 8 MCP tools for document operations
4. ✅ Search functionality
5. ✅ Integration with GraphRAG
6. ✅ Test suite
7. ✅ Startup/shutdown scripts
8. ✅ Documentation

---

**Ready to start implementation?**

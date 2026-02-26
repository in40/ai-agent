# Document Store MCP Server

**Port**: 3070  
**Purpose**: Store and retrieve documents from smart ingestion jobs via MCP protocol

---

## 🚀 Quick Start

### Start Server
```bash
cd /root/qwen/base/document-store-mcp-server
./start_document_store.sh
```

### Or with custom settings
```bash
DOCUMENT_STORE_PORT=3070 DOCUMENT_STORE_TRANSPORT=streamable-http \
  python -m document_store_server.server
```

### Stop Server
```bash
./stop_document_store.sh
```

---

## 📋 Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_ingestion_jobs` | List all document ingestion jobs | None |
| `list_documents` | List documents for a job | `job_id` |
| `get_document` | Get document content | `job_id`, `doc_id`, `format` (optional) |
| `get_document_batch` | Get multiple documents | `job_id`, `doc_ids`, `format` (optional) |
| `get_document_metadata` | Get document metadata | `job_id`, `doc_id` |
| `search_documents` | Search within documents | `job_id`, `query`, `limit` (optional) |
| `delete_job_documents` | Delete all documents for a job | `job_id` |
| `store_document` | Store a new document | `job_id`, `doc_id`, `content`, `format` (optional), `metadata` (optional) |

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCUMENT_STORE_PORT` | 3070 | Server port |
| `DOCUMENT_STORE_HOST` | 0.0.0.0 | Server host |
| `DOCUMENT_STORE_TRANSPORT` | streamable-http | Transport type (stdio, http, streamable-http) |
| `DOCUMENT_STORAGE_PATH` | /root/qwen/base/document-store-mcp-server/data | Storage base path |
| `MAX_DOCUMENT_SIZE_MB` | 50 | Maximum document size in MB |
| `MAX_BATCH_SIZE` | 100 | Maximum documents per batch request |
| `SEARCH_RESULTS_LIMIT` | 50 | Maximum search results |

### Example Configuration
```bash
export DOCUMENT_STORE_PORT=3070
export DOCUMENT_STORAGE_PATH=/var/documents/ingested
export MAX_DOCUMENT_SIZE_MB=100
export DOCUMENT_STORE_TRANSPORT=streamable-http
```

---

## 📁 Storage Structure

```
/data/ingested/
├── {job_id}/
│   ├── documents/
│   │   ├── {doc_id}.txt
│   │   ├── {doc_id}.pdf
│   │   ├── {doc_id}.md
│   │   └── {doc_id}.metadata.json
│   └── index.json
└── {job_id}/
    └── ...
```

---

## 🧪 Usage Examples

### List All Jobs
```bash
curl -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call",
    "params": {
      "name": "list_ingestion_jobs"
    }
  }'
```

### List Documents for a Job
```bash
curl -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "list_documents",
      "arguments": {
        "job_id": "job_db128a16815d"
      }
    }
  }'
```

### Get Document Content
```bash
curl -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "tools/call",
    "params": {
      "name": "get_document",
      "arguments": {
        "job_id": "job_db128a16815d",
        "doc_id": "doc_001",
        "format": "txt"
      }
    }
  }'
```

### Search Documents
```bash
curl -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "4",
    "method": "tools/call",
    "params": {
      "name": "search_documents",
      "arguments": {
        "job_id": "job_db128a16815d",
        "query": "authentication",
        "limit": 10
      }
    }
  }'
```

---

## 🔗 Integration with GraphRAG

The GraphRAG service (port 8000) can retrieve documents from this server:

```python
import requests

DOCUMENT_STORE_URL = "http://localhost:3070/mcp"

def get_documents_for_entity_extraction(job_id: str):
    """Fetch all documents for a job"""
    response = requests.post(
        DOCUMENT_STORE_URL,
        json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": "get_document_batch",
                "arguments": {
                    "job_id": job_id,
                    "doc_ids": [...],  # List of document IDs
                    "format": "txt"
                }
            }
        }
    )
    return response.json()
```

---

## 📊 Monitoring

### Check Server Health
```bash
curl http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### View Logs
```bash
tail -f /root/qwen/base/document-store-mcp-server/document_store.log
```

### Check Storage Usage
```bash
du -sh /root/qwen/base/document-store-mcp-server/data/ingested/*
```

---

## 🛠️ Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Tests
```bash
python test_document_store.py
```

### Project Structure
```
document-store-mcp-server/
├── document_store_server/    # Main package
│   ├── server.py             # Server implementation
│   ├── handlers/             # MCP handlers
│   ├── storage/              # Storage backends
│   ├── utils/                # Utilities
│   └── transports/           # Transport implementations
├── data/                     # Document storage
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── start_server.sh          # Startup script
└── stop_server.sh           # Shutdown script
```

---

## 📝 License

MIT License

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-24

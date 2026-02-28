# Bug Report: Document Store Port Conflict Between MCP Systems

**Date:** February 28, 2026  
**Severity:** Critical  
**Status:** Open  
**Affected Components:** Document Store, start_mcp_master.sh, ai_agent services

---

## Summary

Two separate MCP systems are attempting to run Document Store servers on the same port (3070), causing a port conflict. The base project's Document Store starts first and occupies port 3070, preventing the ai_agent project's Document Store from starting. This results in the ai_agent Web UI serving phantom/stale document data instead of real documents.

---

## Problem Description

### Current State

When `start_mcp_master.sh` is executed, it starts a Document Store server from:
```
/root/qwen/base/document-store-mcp-server/
```

This server:
- Listens on **port 3070**
- Uses storage path: `/root/qwen/base/document-store-mcp-server/data`
- Contains **phantom test data** (298 fake documents)

When the ai_agent project tries to start its Document Store from:
```
/root/qwen/ai_agent/document-store-mcp-server/
```

It **fails silently** because port 3070 is already occupied.

### Impact

| Component | Expected | Actual |
|-----------|----------|--------|
| Document Store Port | 3070 (ai_agent) | 3070 (base project) |
| Storage Path | `/root/qwen/ai_agent/document-store-mcp-server/data` | `/root/qwen/base/document-store-mcp-server/data` |
| Jobs Available | 1 real job (61 docs) | 2 phantom jobs (299 docs) |
| Document Filenames | `gost-r-50922-2006.pdf`, etc. | `doc_000.pdf`, `doc_001.pdf`, etc. |

### User Impact

Users see:
- ❌ Wrong document count (299 instead of 61)
- ❌ Generic filenames (`doc_000.pdf` instead of `gost-r-50922-2006.pdf`)
- ❌ Phantom jobs that don't exist in ai_agent system
- ❌ Cannot import real documents from Document Store

---

## Root Cause Analysis

### Startup Chain

```
start_mcp_master.sh (PID 337070)
├── Starts Registry Server (port 3031)
├── Starts Implementation Engineer (port 3060)
├── Starts Requirements Engineer (port 3062)
├── Starts IT Lead Server (port 3061)
├── Starts Document Store (port 3070) ← CONFLICT HERE
│   └── cd /root/qwen/base/document-store-mcp-server
│   └── nohup bash ./start_document_store.sh
│   └── export DOCUMENT_STORAGE_PATH=/root/qwen/base/document-store-mcp-server/data
├── Starts Team Management (port 3063)
└── Starts Web UI (ports 8000/5173)
```

### Code Analysis

**File:** `/root/qwen/base/start_mcp_master.sh` (Lines 105-120)
```bash
echo "Step 4/6: Starting Document Store Server on port 3070..."
cd /root/qwen/base/document-store-mcp-server
nohup bash ./start_document_store.sh > /tmp/docstore.log 2>&1 &
DOCSTORE_PID=$!
```

**File:** `/root/qwen/base/document-store-mcp-server/start_document_store.sh` (Lines 13-15)
```bash
export DOCUMENT_STORAGE_PATH=${DOCUMENT_STORAGE_PATH:-/root/qwen/base/document-store-mcp-server/data}
export DOCUMENT_STORE_PORT=${DOCUMENT_STORE_PORT:-3070}
```

### Why This Is a Problem

1. **Port Conflict:** Both systems default to port 3070
2. **No Port Availability Check:** Script doesn't verify if port is free
3. **No Error Handling:** Failure to bind port is not detected
4. **Silent Failure:** ai_agent Document Store fails without notification
5. **Data Isolation:** Each system has separate document storage

---

## Proposed Solutions

### Option 1: Disable Base Project Document Store (RECOMMENDED)

**Rationale:** The base project (`/root/qwen/base/`) appears to be an MCP framework/infrastructure project. It likely doesn't need its own Document Store - it should use the ai_agent Document Store as a shared service.

**Changes Required:**

1. **Comment out Document Store startup in `start_mcp_master.sh`:**
```bash
# Step 4/6: Starting Document Store Server on port 3070...
# COMMENTED OUT - Document Store is managed by ai_agent project
# cd /root/qwen/base/document-store-mcp-server
# nohup bash ./start_document_store.sh > /tmp/docstore.log 2>&1 &
# DOCSTORE_PID=$!
```

2. **Update cleanup function:**
```bash
cleanup() {
    echo ""
    echo "Shutting down MCP System..."
    pkill -f "mcp_std_server" 2>/dev/null || true
    pkill -f "it_lead_mcp_server" 2>/dev/null || true
    # pkill -f "document_store" 2>/dev/null || true  # COMMENTED OUT
    pkill -f "team_management" 2>/dev/null || true
    echo "MCP System has been shut down."
    exit 0
}
```

3. **Update status display:**
```bash
# echo "Document Store:            http://localhost:3070/mcp  (Managed by ai_agent)"
```

**Pros:**
- ✅ Single source of truth for documents
- ✅ No port conflicts
- ✅ ai_agent has full control over Document Store lifecycle
- ✅ Simplest solution

**Cons:**
- ❌ Base project components cannot use Document Store independently
- ❌ Requires coordination when restarting services

---

### Option 2: Use Different Ports

**Rationale:** Allow both Document Stores to run simultaneously on different ports.

**Changes Required:**

1. **Modify base project to use port 3071:**
```bash
# In /root/qwen/base/document-store-mcp-server/start_document_store.sh
export DOCUMENT_STORE_PORT=${DOCUMENT_STORE_PORT:-3071}  # Changed from 3070
```

2. **Update ai_agent to use port 3070:**
```bash
# In /root/qwen/ai_agent/document-store-mcp-server/start_document_store.sh
export DOCUMENT_STORE_PORT=${DOCUMENT_STORE_PORT:-3070}
```

3. **Update RAG backend configuration:**
```python
# In /root/qwen/ai_agent/backend/services/rag/document_store_client.py
DOCUMENT_STORE_URL = os.getenv('DOCUMENT_STORE_URL', 'http://127.0.0.1:3070/mcp')
```

**Pros:**
- ✅ Both systems can run independently
- ✅ No service conflicts
- ✅ Clear separation of concerns

**Cons:**
- ❌ Duplicate document storage (wasted disk space)
- ❌ Documents must be ingested twice
- ❌ More complex configuration management
- ❌ Potential confusion about which Document Store to use

---

### Option 3: Shared Document Store with Configuration

**Rationale:** Make Document Store a shared service with configurable storage path.

**Changes Required:**

1. **Create shared configuration:**
```bash
# /root/qwen/shared/document_store.env
DOCUMENT_STORE_PORT=3070
DOCUMENT_STORAGE_PATH=/root/qwen/ai_agent/document-store-mcp-server/data
REGISTRY_HOST=127.0.0.1
REGISTRY_PORT=3031
```

2. **Modify both startup scripts to source shared config:**
```bash
# In both start_mcp_master.sh and ai_agent start scripts
if [ -f "/root/qwen/shared/document_store.env" ]; then
    source /root/qwen/shared/document_store.env
fi
```

3. **Update startup scripts to check if already running:**
```bash
# Check if Document Store is already running
if lsof -i :$DOCUMENT_STORE_PORT > /dev/null 2>&1; then
    echo "✓ Document Store already running on port $DOCUMENT_STORE_PORT"
else
    echo "Starting Document Store on port $DOCUMENT_STORE_PORT..."
    # Start server
fi
```

**Pros:**
- ✅ Single Document Store instance
- ✅ Shared document storage
- ✅ Flexible configuration
- ✅ Proper startup coordination

**Cons:**
- ❌ Requires more complex startup logic
- ❌ Need to manage shared configuration
- ❌ Potential race conditions during startup

---

### Option 4: Systemd Service Management (MOST ROBUST)

**Rationale:** Use systemd to manage Document Store as a proper system service.

**Changes Required:**

1. **Create systemd service:**
```ini
# /etc/systemd/system/document-store.service
[Unit]
Description=Document Store MCP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/qwen/ai_agent/document-store-mcp-server
Environment="DOCUMENT_STORE_PORT=3070"
Environment="DOCUMENT_STORAGE_PATH=/root/qwen/ai_agent/document-store-mcp-server/data"
Environment="REGISTRY_HOST=127.0.0.1"
Environment="REGISTRY_PORT=3031"
ExecStart=/root/qwen/ai_agent/ai_agent_env/bin/python -m document_store_server.server --port 3070
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

2. **Update startup scripts to use systemctl:**
```bash
# Instead of direct startup
systemctl start document-store.service

# Check status
systemctl is-active document-store.service
```

**Pros:**
- ✅ Proper service management
- ✅ Automatic restart on failure
- ✅ System-level logging
- ✅ Clean startup/shutdown
- ✅ Prevents multiple instances

**Cons:**
- ❌ Requires root/sudo access
- ❌ More complex initial setup
- ❌ Systemd-specific (less portable)

---

## Recommendation

### Short-term Fix (Immediate)

**Implement Option 1** - Disable base project Document Store:

1. Edit `/root/qwen/base/start_mcp_master.sh`
2. Comment out Document Store startup (lines 105-120)
3. Comment out Document Store in cleanup function (line 24)
4. Restart services:
   ```bash
   pkill -f "document_store"
   cd /root/qwen/ai_agent/document-store-mcp-server
   source ../ai_agent_env/bin/activate
   python -m document_store_server.server --port 3070 &
   ```

### Long-term Fix (Proper Solution)

**Implement Option 4** - Systemd service management:

1. Create systemd service file
2. Enable and start the service
3. Update all startup scripts to use `systemctl`
4. Add health checks and monitoring

This provides:
- Proper service lifecycle management
- Automatic recovery from failures
- System-level logging and monitoring
- Prevention of multiple instances

---

## Verification Steps

After implementing the fix:

```bash
# 1. Kill all Document Store processes
pkill -f "document_store"

# 2. Start ai_agent Document Store
cd /root/qwen/ai_agent/document-store-mcp-server
source ../ai_agent_env/bin/activate
python -m document_store_server.server --port 3070 &

# 3. Verify correct data
curl -s -X POST http://localhost:3070/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_ingestion_jobs","arguments":{}}}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); jobs=json.loads(d['result']['content'][0]['text']); print(f'Jobs: {len(jobs[\"jobs\"])}'); [print(f'  {j[\"job_id\"]}: {j[\"document_count\"]} docs') for j in jobs['jobs']]"

# Expected output:
# Jobs: 1
#   job_job_90825d5e7b99_rst_gov_ru:8443: 61 docs
```

---

## Files to Modify

| File | Path | Lines | Change |
|------|------|-------|--------|
| `start_mcp_master.sh` | `/root/qwen/base/` | 24, 105-120, 180, 189 | Comment out Document Store |
| `start_document_store.sh` | `/root/qwen/base/document-store-mcp-server/` | 13-15 | Optional: change port |
| `start_all_services.sh` | `/root/qwen/ai_agent/` | N/A | Ensure proper startup |
| `document_store_client.py` | `/root/qwen/ai_agent/backend/services/rag/` | 14 | Verify URL |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Base project components break | Low | Medium | Test all base project MCP servers |
| Document Store fails to start | Low | High | Add health checks and monitoring |
| Port conflict persists | Low | High | Verify with `lsof -i :3070` |
| Data loss | None | N/A | No data modification, only process management |

---

## Timeline

- **Immediate:** Implement Option 1 (disable base Document Store)
- **This Week:** Test and verify ai_agent Document Store works correctly
- **Next Sprint:** Implement Option 4 (systemd service)
- **Future:** Consider containerization (Docker) for better isolation

---

## Related Issues

- Document Store phantom data issue
- Port 3070 conflict
- ai_agent Web UI showing wrong documents
- Multiple MCP system coordination

---

## Contact

For questions or concerns about this bug report, please contact the development team.

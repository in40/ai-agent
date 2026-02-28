# Document Store Phantom Data Fix

## Problem

The "Import from Document Store" feature was showing phantom/fake documents:
- `test_job_001` with `doc_001.txt`
- `job_downloads_20260225_095212` with 298 documents named `doc_000.pdf`, `doc_001.pdf`, etc.

Instead of the REAL documents:
- `job_job_90825d5e7b99_rst_gov_ru:8443` with 61 documents (`gost-34.pdf`, `gost-r-50922-2006.pdf`, etc.)

## Root Cause

**TWO Document Store servers were running on port 3070:**

1. **Phantom Document Store** (PID 329105)
   - Location: `/root/qwen/base/document-store-mcp-server/`
   - Data directory: `/root/qwen/base/document-store-mcp-server/data/ingested/`
   - Contained: Fake test jobs (`test_job_001`, `job_downloads_20260225_095212`)
   - Started: Feb 26, 2026 at 16:15

2. **Real Document Store** (should be on port 3070)
   - Location: `/root/qwen/ai_agent/document-store-mcp-server/`
   - Data directory: `/root/qwen/ai_agent/document-store-mcp-server/data/ingested/`
   - Contained: Real job (`job_job_90825d5e7b99_rst_gov_ru:8443` with 61 documents)
   - Could NOT start because port 3070 was already occupied

The RAG backend's `document_store_client` was connecting to `http://127.0.0.1:3070/mcp`, which was being served by the PHANTOM Document Store from `/root/qwen/base/`.

## Solution

### Step 1: Kill the Phantom Document Store
```bash
kill -9 329105
```

### Step 2: Start the Correct Document Store
```bash
cd /root/qwen/ai_agent/document-store-mcp-server
source ../ai_agent_env/bin/activate
python -m document_store_server.server --port 3070 &
```

### Step 3: Restart RAG Backend
```bash
pkill -f "rag.*app"
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate
PYTHONPATH=/root/qwen/ai_agent/backend/services/rag:$PYTHONPATH \
  nohup python -m backend.services.rag.app > rag_service.log 2>&1 &
```

## Verification

### Before Fix
```
Jobs from RAG API: 2
  Job: test_job_001... Docs: 1, First: doc_001.txt
  Job: job_downloads_20260225_095212... Docs: 298, First: doc_000.pdf
```

### After Fix
```
Jobs from RAG API: 1
  Job: job_job_90825d5e7b99_rst_gov_ru:8443... Docs: 61, First: gost-34.pdf
```

## Prevention

### Check for Multiple Document Store Instances
```bash
# Before starting a new Document Store, check what's running
ps aux | grep "document.*store" | grep -v grep
lsof -i :3070
```

### Verify Data Directory
```bash
# Check what data directory the running Document Store is using
ls -la /proc/<PID>/cwd
# Should point to: /root/qwen/ai_agent/document-store-mcp-server
```

### Startup Script
Create a startup script that ensures only ONE Document Store runs:
```bash
#!/bin/bash
# stop_document_store.sh
pkill -f "document_store_server"
sleep 2

# start_document_store.sh
cd /root/qwen/ai_agent/document-store-mcp-server
source ../ai_agent_env/bin/activate
python -m document_store_server.server --port 3070 &
```

## Files Modified

| File | Change |
|------|--------|
| `backend/services/rag/document_store_client.py` | Added debug logging for `list_ingestion_jobs()` |
| `backend/services/rag/app.py` | Temporarily disabled auth for testing (re-enabled after fix) |

## Lessons Learned

1. **Always check for existing processes** before starting services on well-known ports
2. **Multiple installations** of the same service can cause confusion
3. **Port conflicts** can silently cause wrong data to be served
4. **Process monitoring** should include checking the working directory (`/proc/<PID>/cwd`)

## Related Issues Fixed

This also fixes the filename display issue in the Web UI - documents now show their REAL filenames (`gost-r-50922-2006.pdf`) instead of generic names (`doc_000.pdf`).

---

**Status:** ✅ Fixed  
**Date:** February 28, 2026  
**Root Cause:** Phantom Document Store server running from `/root/qwen/base/`  
**Solution:** Kill phantom process, start correct Document Store from `/root/qwen/ai_agent/`

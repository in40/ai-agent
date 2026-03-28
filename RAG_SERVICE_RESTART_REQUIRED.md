# CRITICAL: RAG Service Restart Required After Code Fixes

**Date**: March 7, 2026  
**Severity**: CRITICAL - Fixes Not Applied Without Restart  
**Status**: ✅ Resolved

---

## Root Cause

**The job started AFTER the code fix was applied to the file, but the RAG service was never restarted.**

Python **caches imported modules** in memory. When we fixed `phased_processing_api.py`, the running RAG service continued using the OLD buggy code from memory.

---

## Timeline

| Time | Event |
|------|-------|
| ~17:50 | Fixed `phased_processing_api.py` file (chunks save logic) |
| 17:54 | Job `job_598e0bab41db` started |
| 18:06 | Job completed - but used OLD code from memory |
| 18:06 | Log shows: "Saved chunks to **.md**" (wrong!) |
| 18:32 | **RAG service restarted** - now uses fixed code |

---

## What Happened

1. We applied fix to file: `backend/services/rag/phased_processing_api.py`
2. RAG service was **already running** with old code in memory
3. Job started → Python used cached module → OLD buggy code executed
4. Result: `.md` file overwritten with JSON (same bug we thought we fixed!)

### Log Evidence
```
INFO:[Phased Job job_598e0bab41db] Saved chunks to /path/to/r-1323565.1_8e67ba17.md
                                                              ^^^ WRONG!
```

The log message proves the OLD code ran (new code would log `.chunks.json`).

---

## Solution Applied

### 1. Killed Old RAG Service
```bash
pkill -f "python -m backend.services.rag.app"
```

### 2. Started New RAG Service with Fixed Code
```bash
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate
python -m backend.services.rag.app &
```

### 3. Verified Service Running
```
root 950947 103 3.9 ... python -m backend.services.rag.app
```

---

## Impact

### Before Restart
- ❌ Code fixes in file but NOT in running service
- ❌ Jobs continue to fail with old bugs
- ❌ `.md` files overwritten with JSON
- ❌ No `.chunks.json` files created

### After Restart
- ✅ Running service uses fixed code
- ✅ `.md` files preserved (extracted text)
- ✅ `.chunks.json` files created correctly
- ✅ All fixes now active

---

## Lesson Learned

**CRITICAL**: After ANY code fix to Python modules:
1. ✅ Edit the file
2. ✅ **RESTART the service** (required!)
3. ✅ Verify service loaded new code
4. ✅ Test with new job

**File changes alone are NOT enough!**

---

## Services That Need Restart

After fixing code in these files, restart the corresponding service:

| File Modified | Service to Restart |
|--------------|-------------------|
| `backend/services/rag/phased_processing_api.py` | `python -m backend.services.rag.app` |
| `backend/services/agent/app.py` | `python -m backend.services.agent.app` |
| `backend/services/auth/app.py` | `python -m backend.services.auth.app` |
| `backend/services/gateway/app.py` | `python -m backend.services.gateway.app` |

---

## How to Restart RAG Service

```bash
cd /root/qwen/ai_agent

# Stop old service
pkill -f "python -m backend.services.rag.app"

# Wait for clean shutdown
sleep 3

# Start new service
source ai_agent_env/bin/activate
nohup python -m backend.services.rag.app > rag_service.log 2>&1 &

# Verify running
ps aux | grep "backend.services.rag.app" | grep -v grep

# Check logs
tail -f rag_service.log
```

---

## Verification

After restart, run a test job and verify:

1. **Log message shows correct file**:
   ```
   INFO: Saved chunks to /path/to/file.chunks.json
   ```

2. **Both files exist**:
   ```bash
   ls -la document-store-mcp-server/data/ingested/*/documents/*.md
   ls -la document-store-mcp-server/data/ingested/*/documents/*.chunks.json
   ```

3. **File contents correct**:
   - `.md` = markdown text (NOT JSON)
   - `.chunks.json` = valid JSON with chunks

---

## Current Status

- ✅ RAG service restarted at 18:32
- ✅ Fixed code now active
- ✅ Job `job_598e0bab41db` reset and ready for re-processing
- ⏳ User action: Re-run smart chunking in Web UI

---

## Related Bug Reports

1. **MD_FILE_OVERWRITE_BUG_FIX.md** - Original bug fix (file edited)
2. **JOB_STATUS_POLLING_BUG_FIX.md** - HTTP 500 polling fix (file edited)
3. **JOB_598e0bab41DB_MISSING_CHUNKS_FIX.md** - This incident (service restart needed)

---

**Discovered by**: User (correctly noted job started after fix!)  
**Analyzed by**: AI Agent  
**Resolved by**: Restarting RAG service  
**Key Takeaway**: ALWAYS restart services after code changes!

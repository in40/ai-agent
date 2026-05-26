# ROOT CAUSE FOUND: Smart Chunking Job Failure

**Date**: March 29, 2026  
**Job**: `job_777c327b39b6`  
**Status**: ✅ Root Cause Identified

---

## THE ACTUAL ROOT CAUSE

The smart chunking is failing because of a **model configuration mismatch**:

### Configuration in `.env`:
```env
FORCE_DEFAULT_MODEL_FOR_ALL=true
DEFAULT_LLM_MODEL=qwen3.5-35b-a3b
RESPONSE_LLM_MODEL=qwen3.5-0.8b
```

### What's Happening:
1. `FORCE_DEFAULT_MODEL_FOR_ALL=true` forces ALL components to use `DEFAULT_LLM_MODEL`
2. This overrides `RESPONSE_LLM_MODEL=qwen3.5-0.8b` 
3. So smart chunking uses `qwen3.5-35b-a3b` instead of `qwen3.5-0.8b`
4. The 35B model has **smaller context window** configured on LM Studio server (4096 tokens)
5. The 50K char prompt (~10K+ tokens) exceeds the 35B model's context
6. LLM server returns: `HTTP 400 - The number of tokens to keep from the initial prompt is greater than the context length (n_keep: 25701 >= n_ctx: 4096)`
7. Smart chunking fails with 0 chunks

### Test Results:
| Model | 50K Char Prompt | Result |
|-------|----------------|--------|
| `qwen3.5-0.8b` | ✅ Works | Returns valid JSON with chunks |
| `qwen3.5-35b-a3b` | ❌ Fails | HTTP 400 context error |

---

## SOLUTIONS

### Solution 1: Disable FORCE_DEFAULT_MODEL_FOR_ALL (RECOMMENDED)

**Change in `.env`**:
```env
FORCE_DEFAULT_MODEL_FOR_ALL=false
```

**Effect**: 
- Smart chunking will use `RESPONSE_LLM_MODEL=qwen3.5-0.8b` (which works)
- Other components can still use their specific model configs
- No need to restart LM Studio server

**Test**: Re-run job `job_777c327b39b6` - should succeed

---

### Solution 2: Change DEFAULT_LLM_MODEL

**Change in `.env`**:
```env
DEFAULT_LLM_MODEL=qwen3.5-0.8b
```

**Effect**:
- All components using default model will use 0.8B
- Keeps `FORCE_DEFAULT_MODEL_FOR_ALL=true`
- May affect other components that rely on 35B model

---

### Solution 3: Increase 35B Model Context (INFRASTRUCTURE)

**Action**: On LM Studio server (192.168.51.105), reload the 35B model with larger context:
```bash
# In LM Studio UI or config:
# Set context length (n_ctx) to 32768 or higher for qwen3.5-35b-a3b
```

**Effect**:
- 35B model can handle large prompts
- No code changes needed
- Requires server access and restart

---

## VERIFICATION

After applying Solution 1, test with:

```bash
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate
python3 << 'EOF'
from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync

text_path = '/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_395de1a8.md'

success, chunks, error = chunk_document_with_llm_sync(
    file_path=text_path,
    prompt="",
    filename="r-1323565.1_395de1a8.pdf",
    timeout=300
)

print(f"success: {success}")
print(f"chunks: {len(chunks)}")
print(f"error: {error}")
EOF
```

**Expected output**:
```
success: True
chunks: > 0
error: None
```

---

## WHY THE CONFUSION?

1. **Error message was misleading**: "Expecting ',' delimiter" was from a secondary JSON parse error after the 400 error
2. **Multiple models available**: Server has both 0.8B and 35B, easy to confuse which is being used
3. **FORCE_DEFAULT_MODEL_FOR_ALL**: This setting silently overrides component-specific model configs
4. **Context window assumption**: Assumed 35B would have larger context, but it's a server configuration issue

---

## FILES TO MODIFY

1. **`.env`** (Solution 1 - Recommended):
   ```env
   FORCE_DEFAULT_MODEL_FOR_ALL=false
   ```

2. **OR `.env`** (Solution 2):
   ```env
   DEFAULT_LLM_MODEL=qwen3.5-0.8b
   ```

After changing `.env`, restart the AI agent backend:
```bash
# Restart backend service
systemctl restart ai-agent-backend
# Or however the service is managed
```

---

## LESSONS LEARNED

1. **Check FORCE_DEFAULT_MODEL_FOR_ALL first** - it overrides all component-specific configs
2. **Test with actual models** - don't assume model capabilities
3. **LM Studio context is server-side** - each model can have different n_ctx settings
4. **Error cascades** - the 400 error led to empty response, which led to JSON parse error

---

**Status**: ✅ Ready to Fix  
**Recommended Action**: Set `FORCE_DEFAULT_MODEL_FOR_ALL=false` in `.env`  
**Time to Fix**: 5 minutes + service restart

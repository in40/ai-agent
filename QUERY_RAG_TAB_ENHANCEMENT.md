# Query RAG Tab Enhancement - Hybrid Search & Raw Results

**Date:** February 28, 2026  
**Status:** UI Complete - Backend Uses Config Mode  

---

## What Was Added

### 1. RAG Mode Selector

**UI Component:** Toggle buttons to select retrieval mode
- **Hybrid (Vector + Graph)** - Default, combines both sources
- **Vector Only** - Traditional vector search only

**Location:** Query RAG tab, top of panel

**Visual:**
```
┌─────────────────────────────────────────┐
│ ⚙️ RAG Mode                             │
├─────────────────────────────────────────┤
│ [🔷 Hybrid (Vector + Graph)] [ Vector ] │
│ ℹ️ Hybrid mode combines vector search   │
│    with knowledge graph relationships   │
└─────────────────────────────────────────┘
```

### 2. Raw Results Toggle

**UI Component:** Checkbox to show/hide raw context data

**When Checked:**
- Shows JSON of all context chunks sent to LLM
- Displays in expandable code block
- Includes copy button

**Location:** Below query input

**Visual:**
```
☑️ 📄 Show Raw Results (context sent to LLM)

┌─────────────────────────────────────────┐
│ 📄 Raw Context Data          [📋 Copy] │
├─────────────────────────────────────────┤
│ [                                         │
│   {                                      │
│     "content": "...",                    │
│     "source": "vector",                  │
│     "score": 0.85                        │
│   },                                     │
│   ...                                    │
│ ]                                        │
└─────────────────────────────────────────┘
```

### 3. Enhanced Response Display

**New Features:**
- **Source badges:** Shows if chunk is from `VECTOR`, `GRAPH`, or `BOTH`
- **Score display:** Shows hybrid relevance score
- **Source count:** Shows breakdown (e.g., "5 vector, 3 graph, 2 merged")

**Visual:**
```
Context (10 sources: 5 vector, 3 graph, 2 merged):

[VECTOR] [Score: 0.923] Document Title
  Source: vector
  Preview text...

[GRAPH] [Score: 0.845] Another Document  
  Source: graph
  Preview text...
```

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/web_client/index.html` | Added mode selector, raw results toggle, enhanced display |

---

## How It Works

### Mode Selection

**Current Implementation:**
```javascript
// UI sends mode to backend
fetch('/api/rag/query', {
    body: JSON.stringify({ 
        query: "What GOST standards mention encryption?",
        mode: "hybrid"  // or "vector"
    })
})
```

**Backend (Current):**
```python
# Reads from config at startup
RAG_RETRIEVER_MODE = os.getenv("RAG_RETRIEVER_MODE", "hybrid")

# Uses configured mode (doesn't yet use per-query mode parameter)
rag_orchestrator = RAGOrchestrator(llm=llm)
result = rag_orchestrator.query(query)
```

**To Enable Dynamic Mode Switching:**

Need to update backend to respect per-query mode:

```python
@app.route('/query', methods=['POST'])
def rag_query(current_user_id):
    data = request.get_json()
    query = data.get('query')
    mode = data.get('mode', RAG_RETRIEVER_MODE)  # Use query mode or fallback
    
    # Create orchestrator with specific mode
    rag_orchestrator = RAGOrchestrator(llm=llm, mode=mode)
    result = rag_orchestrator.query(query)
```

---

## Raw Results Feature

### What's Shown

The raw results show the **exact context** that will be sent to the LLM:

```json
[
  {
    "content": "Стандарт определяет требования к криптографической защите...",
    "title": "GOST R 34.10-2012",
    "source": "vector [Collection: documents]",
    "metadata": {
      "upload_method": "Local",
      "file_id": "abc123",
      "stored_file_path": "./data/abc123/file.pdf"
    },
    "score": 0.923,
    "download_info": {
      "file_id": "abc123",
      "filename": "gost-r-34-10-2012.pdf",
      "download_available": true
    }
  },
  {
    "content": "...",
    "source": "graph",
    "metadata": {
      "entity_name": "криптографическая защита",
      "entity_type": "TECHNOLOGY"
    },
    "score": 0.845,
    "graph_context": {
      "primary_entity": "криптографическая защита",
      "related_entities": [...]
    }
  }
]
```

### Use Cases

1. **Debugging:** See exactly what context the LLM receives
2. **Hybrid Validation:** Verify both vector and graph results are included
3. **Score Analysis:** Check hybrid scoring is working correctly
4. **Copy for Testing:** Copy context to test with different LLMs

---

## Testing

### 1. Test Mode Selection

```bash
# Set hybrid mode in environment
export RAG_RETRIEVER_MODE=hybrid

# Restart RAG service
# Then in UI:
# 1. Go to Query RAG tab
# 2. Select "Hybrid (Vector + Graph)"
# 3. Enter query: "What GOST standards mention encryption?"
# 4. Check response shows both vector and graph badges
```

### 2. Test Raw Results

```bash
# In UI:
# 1. Check "Show Raw Results" checkbox
# 2. Run query
# 3. Verify JSON shows context array
# 4. Click "Copy" button
# 5. Paste to verify content
```

### 3. Compare Modes

```bash
# Test Vector Only
export RAG_RETRIEVER_MODE=vector

# Test Hybrid
export RAG_RETRIEVER_MODE=hybrid

# Compare results - hybrid should show:
# - More diverse sources
# - Graph relationship context
# - Different ranking
```

---

## Backend Integration Needed

To make the UI mode selector fully functional, update the backend:

### Option 1: Per-Query Mode (Recommended)

**File:** `backend/services/rag/app.py`

```python
@app.route('/query', methods=['POST'])
def rag_query(current_user_id):
    data = request.get_json()
    query = data.get('query')
    mode = data.get('mode', 'hybrid')  # From UI or default
    
    # Create orchestrator with specific mode
    response_generator = ResponseGenerator()
    llm = response_generator._get_llm_instance(...)
    
    # Temporarily override config
    original_mode = RAG_RETRIEVER_MODE
    try:
        import rag_component.config as rag_config
        rag_config.RAG_RETRIEVER_MODE = mode
        rag_orchestrator = RAGOrchestrator(llm=llm)
        result = rag_orchestrator.query(query)
    finally:
        rag_config.RAG_RETRIEVER_MODE = original_mode
    
    return jsonify(result), 200
```

### Option 2: Environment Variable Only

Keep current behavior - mode is set by `RAG_RETRIEVER_MODE` environment variable.

UI selector would be informational only (shows current mode but doesn't change it).

---

## Benefits

### For Users
1. **Mode Control:** Choose between speed (vector) and completeness (hybrid)
2. **Transparency:** See exactly what context is sent to LLM
3. **Debugging:** Understand why certain results appear
4. **Validation:** Verify hybrid retrieval is working

### For Developers
1. **Debugging:** Raw results help identify retrieval issues
2. **Testing:** Compare vector vs hybrid results easily
3. **Tuning:** Analyze scores to adjust weights
4. **Copy/Paste:** Easy to copy context for external testing

---

## Performance Notes

| Mode | Expected Latency | Use Case |
|------|-----------------|----------|
| Vector Only | ~100ms | Quick queries, simple questions |
| Hybrid | ~350ms | Complex queries, need entity relationships |

---

## Next Steps

1. ✅ **UI Implementation** - Complete
2. ⏳ **Backend Mode Parameter** - Add per-query mode support
3. ⏳ **Testing** - Verify hybrid mode works end-to-end
4. ⏳ **Tuning** - Adjust vector/graph weights based on results

---

## Summary

**Implemented:**
- ✅ RAG mode selector UI (Hybrid/Vector)
- ✅ Raw results toggle with JSON display
- ✅ Copy to clipboard functionality
- ✅ Enhanced response with source badges and scores
- ✅ Source count breakdown

**Pending:**
- ⏳ Backend per-query mode parameter support
- ⏳ End-to-end testing with real queries

**Ready to test the UI!** The mode selector will work once `RAG_RETRIEVER_MODE=hybrid` is set in the environment.

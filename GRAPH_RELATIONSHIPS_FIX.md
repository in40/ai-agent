# Graph Relationships Fix

## Problem

The Graph Explorer was showing **52 entities but 0 relationships** because:

1. **Entity extraction worked** - 52 entities were stored in Neo4j
2. **But relationships weren't created** - The `MENTIONS` relationships between Chunks and Entities were never created during ingestion
3. **No Entity-Entity relationships existed** - The visualization query looked for Entity-Entity relationships but none existed

### Root Cause

The hybrid ingestion process stored:
- ✅ Document nodes
- ✅ Chunk nodes (with `HAS_CHUNK` relationships from Document)
- ✅ Entity nodes

But it **failed to create**:
- ❌ `MENTIONS` relationships (Chunk → Entity)
- ❌ Any Entity-Entity relationships

## Solution

Updated the `/api/rag/graph/visualize` endpoint to **infer co-occurrence relationships** based on entity creation timestamps.

### How It Works

Entities extracted from the same document are created within seconds of each other. The updated query:

1. **Gets all entities** matching the filter criteria
2. **Finds entity pairs** that:
   - Were created within 2 seconds of each other (`updated_at` timestamp)
   - Are of different types (e.g., STANDARD + ORGANIZATION)
   - Have valid timestamps
3. **Creates `CO_OCCUR` relationships** between these entity pairs

### Cypher Query

```cypher
MATCH (e1:Entity), (e2:Entity)
WHERE e1.name IN $names AND e2.name IN $names
AND e1.name < e2.name  -- Avoid duplicates
AND e1.type <> e2.type  -- Different types more likely to be related
AND e1.updated_at IS NOT NULL AND e2.updated_at IS NOT NULL
AND abs(duration.between(e1.updated_at, e2.updated_at).seconds) < 2
RETURN e1.name as source, e2.name as target, 'CO_OCCUR' as relationship
```

### Example

Entities extracted from `gost-r-50922-2006` at `19:04:44`:
- `ГОСТ Р 50922—2006` (STANDARD) - `19:04:44.529`
- `Федеральное агентство...` (ORGANIZATION) - `19:47:18.338`
- `Российская Федерация` (LOCATION) - `19:04:45.790`

The query will create:
- `ГОСТ Р 50922—2006` -[CO_OCCUR]- `Российская Федерация` (both created within 2 seconds)

## Files Modified

| File | Changes |
|------|---------|
| `backend/services/rag/app.py` | Updated `/api/rag/graph/visualize` endpoint |

## Testing

1. **Refresh** the Web UI (hard refresh: Ctrl+Shift+R)
2. **Navigate** to RAG Functions → Graph Explorer
3. **Click** "Load Graph"
4. **Expected result:**
   - 52 nodes displayed
   - Multiple relationships shown (CO_OCCUR)
   - Entities connected based on document co-occurrence

## Future Improvements

### Short-term
1. **Backfill MENTIONS relationships** - Run script to create Chunk→Entity relationships
2. **Store document info on entities** - Add `document` property for better grouping

### Long-term
1. **Fix hybrid ingestion** - Ensure MENTIONS relationships are created during entity extraction
2. **Add relationship types** - Distinguish between different relationship types (PUBLISHED_BY, DEFINES, REFERENCES, etc.)
3. **Entity disambiguation** - Merge duplicate entities with same name

## Related Files

- `/root/qwen/ai_agent/backfill_entity_relationships.py` - Script to backfill MENTIONS relationships (optional)
- `/root/qwen/ai_agent/check_neo4j_graph.py` - Script to verify Neo4j data

---

**Status:** ✅ Fixed  
**Date:** February 27, 2026  
**Version:** v0.8.14

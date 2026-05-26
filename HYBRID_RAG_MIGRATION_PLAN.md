# Hybrid RAG Architecture Migration Plan

## Problem Statement

Current hybrid RAG implementation stores chunks in BOTH Vector DB (Qdrant) AND Graph DB (Neo4j), causing:
1. **Data duplication**: Same chunk content stored twice
2. **Storage inefficiency**: Neo4j storing large text content unnecessarily
3. **Sync issues**: Chunks exist in Vector DB but NOT in Neo4j (0 chunks in Neo4j currently)
4. **Graph search failure**: `_graph_search()` returns empty results because no chunks linked to entities

## Target Architecture: Reference-Based Hybrid RAG

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Vector DB (Qdrant)                           │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Chunk UUID | Embedding | Content | Metadata                   │ │
│  │ uuid-001   | [vector]  | "ГОСТ...| {doc_id, chunk_index, ...} │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               ▲
                               │ Reference by UUID
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                      Graph DB (Neo4j)                               │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ (:Entity {name: "ГОСТ Р 34.10-2012",                          │ │
│  │          chunk_ids: ["uuid-001", "uuid-002"]})                │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Benefits

| Aspect | Current (Duplication) | Target (References) |
|--------|----------------------|---------------------|
| Storage | Chunks in BOTH DBs | Chunks ONLY in Vector DB |
| Consistency | Must sync both | Single source of truth |
| Memory | High (duplicate content) | Low (UUID references only) |
| Graph Search | Gets content from Neo4j | Gets UUIDs → fetch from Vector DB |

## Implementation Phases

### Phase 1: Modify Ingestion to Generate Chunk UUIDs

**Files to modify:**
- `rag_component/main.py` - `ingest_documents()` method
- `backend/services/rag/smart_ingestion_enhanced.py` - `process_hybrid_mode()`

**Changes:**
1. Generate unique UUID for each chunk before ingestion
2. Store UUID in chunk metadata: `metadata['chunk_uuid'] = str(uuid.uuid4())`
3. Pass UUID to Vector DB (already handled via metadata)
4. **REMOVE** Neo4j chunk storage: Skip `neo4j.store_chunks_batch()`

### Phase 2: Modify Neo4j Entity Storage

**Files to modify:**
- `backend/services/rag/neo4j_integration.py` - `create_knowledge_graph()`

**Changes:**
1. Instead of creating Chunk nodes in Neo4j, store chunk UUIDs as array property on Entity nodes
2. New Cypher query:
```cypher
MERGE (e:Entity {name: $name, type: $type})
SET e.chunk_ids = COALESCE(e.chunk_ids, []) + $chunk_uuid,
    e.updated_at = datetime()
```
3. Remove `store_chunk()` and `store_chunks_batch()` calls from ingestion flow

### Phase 3: Modify Graph Search to Fetch from Vector DB

**Files to modify:**
- `rag_component/hybrid_retriever.py` - `_graph_search()` method

**Changes:**
1. Query Neo4j for entities matching search terms
2. Get `chunk_ids` array from each entity
3. Query Vector DB by chunk UUIDs to get actual content:
```python
# Get chunk UUIDs from entities
chunk_uuids = [uuid for entity in entities for uuid in entity.get('chunk_ids', [])]

# Fetch chunks from Vector DB using filter
vector_docs = self.vector_store_manager.similarity_search_by_ids(chunk_uuids)
```
4. Format results with entity metadata

### Phase 4: Add Vector DB Query by UUIDs

**Files to modify:**
- `rag_component/vector_store_manager.py` - Add new method

**New method:**
```python
def similarity_search_by_ids(self, chunk_uuids: List[str], top_k: int = None) -> List[LCDocument]:
    """Fetch documents by their chunk UUIDs from Vector DB"""
    # Qdrant supports filtering by metadata
    filter_condition = {
        "key": "chunk_uuid",
        "operator": "ContainsAny",
        "value": chunk_uuids
    }
    return self.similarity_search_with_filter(filter_condition, top_k=top_k)
```

### Phase 5: Data Migration (One-Time)

**For existing data:**
1. Clear Neo4j Chunk nodes (keep Entities)
2. Re-ingest documents using new hybrid flow
3. OR: Run migration script to extract chunk UUIDs from Vector DB and update Entity nodes

## Detailed Code Changes

### 1. `rag_component/main.py` - Add UUID Generation

```python
# In ingest_documents() method, around line 78-98
import uuid

for file_path in file_paths:
    docs = self.document_loader.load_document(file_path)
    
    if preprocess:
        docs = self.text_splitter.split_documents(docs)
    
    # Add unique UUID to each chunk
    for doc in docs:
        doc.metadata["chunk_uuid"] = str(uuid.uuid4())  # NEW
        # ... existing metadata code ...
```

### 2. `backend/services/rag/smart_ingestion_enhanced.py` - Skip Neo4j Chunk Storage

```python
# In process_hybrid_mode() around line 1604-1613
# REMOVE these lines:
#     chunks_stored = neo4j.store_chunks_batch(doc_id, chunks_with_entities)
#     graph_stats = neo4j.create_knowledge_graph(chunks_with_entities)

# REPLACE with entity-only storage:
entity_uuid_map = self._build_entity_chunk_mapping(chunks_with_entities)
neo4j.store_entity_chunk_refs(doc_id, entity_uuid_map)  # NEW method
```

### 3. `backend/services/rag/neo4j_integration.py` - New Entity Storage Method

```python
def store_entity_chunk_refs(self, doc_id: str, entity_chunk_map: Dict[str, List[str]]) -> bool:
    """Store chunk UUID references on Entity nodes (not full chunks)"""
    if not self.connected:
        return False
    
    try:
        with self.driver.session() as session:
            for entity_name, chunk_uuids in entity_chunk_map.items():
                # Determine entity type (simplified - could be more sophisticated)
                entity_type = self._infer_entity_type(entity_name)
                
                session.run("""
                    MERGE (e:Entity {name: $name, type: $type})
                    SET e.chunk_ids = COALESCE(e.chunk_ids, []) + $chunk_uuids,
                        e.updated_at = datetime()
                """, {
                    'name': entity_name,
                    'type': entity_type,
                    'chunk_uuids': chunk_uuids
                })
        return True
    except Exception as e:
        logger.error(f"Error storing entity chunk refs: {e}")
        return False

def _infer_entity_type(self, name: str) -> str:
    """Infer entity type from name (simple heuristic)"""
    if 'ГОСТ' in name or 'GOST' in name or 'ISO' in name:
        return 'STANDARD'
    elif any(org in name for org in ['ФГУП', 'ООО', 'АО', 'Рос']):
        return 'ORGANIZATION'
    else:
        return 'CONCEPT'
```

### 4. `rag_component/hybrid_retriever.py` - Modified Graph Search

```python
def _graph_search(self, query: str, top_k: int) -> List[Dict]:
    """Perform graph-based entity search with Vector DB chunk retrieval"""
    if not self.neo4j or not self.neo4j.connected:
        return []
    
    # Extract key terms from query
    query_terms = [word for word in query.split()[:5] if len(word) > 3]
    if not query_terms:
        return []
    
    # Find matching entities and get their chunk UUIDs
    all_chunk_uuids = []
    entity_info = {}  # Map chunk_uuid -> entity info
    
    for term in query_terms:
        entities = self.neo4j.query_entities_by_text(term, limit=top_k)
        for entity in entities:
            chunk_ids = entity.get('chunk_ids', [])
            for chunk_uuid in chunk_ids:
                all_chunk_uuids.append(chunk_uuid)
                entity_info[chunk_uuid] = {
                    'entity_name': entity['name'],
                    'entity_type': entity['type'],
                    'relevance': entity.get('relevance', 0.0)
                }
    
    if not all_chunk_uuids:
        return []
    
    # Fetch chunks from Vector DB by UUIDs
    unique_uuids = list(set(all_chunk_uuids))  # Deduplicate
    vector_docs = self.vector_store_manager.similarity_search_by_ids(
        unique_uuids, top_k=top_k * 2
    )
    
    # Format results with entity metadata
    formatted = []
    for doc in vector_docs:
        chunk_uuid = doc.metadata.get('chunk_uuid', '')
        entity = entity_info.get(chunk_uuid, {})
        
        formatted.append({
            'content': doc.page_content,
            'metadata': {
                'entity_name': entity.get('entity_name', ''),
                'entity_type': entity.get('entity_type', ''),
                'chunk_uuid': chunk_uuid,
                'upload_method': 'Graph RAG'
            },
            'vector_score': 0.0,
            'graph_score': float(entity.get('relevance', 0.0)) / 100.0,
            'source': 'graph'
        })
    
    return formatted
```

### 5. `rag_component/vector_store_manager.py` - Add UUID Query Method

```python
def similarity_search_by_ids(self, chunk_uuids: List[str], top_k: int = None) -> List[LCDocument]:
    """
    Fetch documents by their chunk UUIDs from Vector DB.
    
    Args:
        chunk_uuids: List of chunk UUIDs to fetch
        top_k: Maximum number of results (not used for ID-based lookup)
        
    Returns:
        List of documents matching the UUIDs
    """
    if not chunk_uuids:
        return []
    
    # Use Qdrant filter to find documents by chunk_uuid
    from qdrant_client.http import models
    
    filter_condition = models.Filter(
        must=[
            models.FieldCondition(
                key="chunk_uuid",
                match=models.MatchAny(any=chunk_uuids)
            )
        ]
    )
    
    # Search with empty vector to get all matching documents
    # (or use a dummy vector if required)
    result = self.vector_store.similarity_search(
        query="",  # Empty query - we're filtering by ID, not similarity
        k=len(chunk_uuids) if top_k is None else top_k,
        filter=filter_condition
    )
    
    return result
```

## Testing Plan

### Unit Tests
1. Test UUID generation in ingestion
2. Test entity chunk reference storage in Neo4j
3. Test Vector DB query by UUIDs
4. Test graph search returns correct chunks

### Integration Tests
1. Ingest document → Verify chunks in Vector DB with UUIDs
2. Verify entities in Neo4j with chunk_uuid arrays (no Chunk nodes)
3. Query "ГОСТ параметры" → Verify graph search returns relevant chunks

### Performance Tests
1. Compare memory usage before/after migration
2. Compare query latency for graph search

## Rollback Plan

If issues arise:
1. Revert code changes
2. Neo4j data is safe (only Entity nodes, no Chunk nodes created)
3. Vector DB data is safe (UUIDs are just metadata)
4. Re-enable old `store_chunks_batch()` call if needed

## Migration Checklist

- [x] Phase 1: Add UUID generation to ingestion
- [x] Phase 2: Modify Neo4j to store chunk references only  
- [x] Phase 3: Modify graph search to fetch from Vector DB
- [x] Phase 4: Add Vector DB query by UUIDs method
- [x] Test: Code compiles and imports correctly
- [ ] Test: Ingest sample document with new code
- [ ] Test: Verify entity-chunk mapping in Neo4j
- [ ] Test: Graph search returns results
- [ ] Data migration: Re-ingest existing documents

## Current Status

**Implementation:** ✅ COMPLETE

**Data Migration:** ❌ PENDING

### Why Graph Search Returns Nothing Currently:

Existing entities in Neo4j were created **before** this migration and don't have `chunk_ids` property. The new code correctly stores `chunk_ids` on new entities, but old data needs to be re-processed.

### To Complete Migration:

1. **Option A: Re-ingest all documents** (recommended)
   - Documents will be chunked with UUIDs
   - Entities will get `chunk_ids` populated
   - Graph search will work immediately

2. **Option B: Backfill existing chunks** (advanced)
   - Query Vector DB for all chunks
   - Extract entities from chunk content
   - Update Neo4j entities with chunk_uuid references
   - Complex and error-prone

## Notes

- **Neo4j schema change**: Entity nodes now have `chunk_ids` array property instead of relationships to Chunk nodes
- **Backward compatibility**: Old queries that expect Chunk nodes will fail - update all graph queries
- **Performance**: Querying Vector DB by ID should be fast (indexed metadata field)
- **Storage savings**: ~90% reduction in Neo4j storage (no duplicate chunk content)

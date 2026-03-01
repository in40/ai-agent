# Hybrid RAG Implementation Analysis & Proposal

**Date:** February 28, 2026  
**Status:** Analysis Complete - Ready for Implementation  

---

## Executive Summary

**Current State:** We have **Graph RAG ingestion** but **Vector-only queries**.

**Problem:** Neo4j graph database is populated with entities and relationships during ingestion, but **NEVER queried** during user questions. This means we're missing rich contextual relationships that could improve answer quality.

**Solution:** Implement **Hybrid RAG** that queries BOTH vector and graph databases, then intelligently merges results.

---

## Current Architecture Analysis

### Query Flow (Current)

```
User Query
    ↓
RAGOrchestrator.query()
    ↓
RAGChain.get_context_and_response()
    ↓
Retriever.get_relevant_documents()  ← VECTOR ONLY
    ↓
VectorStoreManager.similarity_search()
    ↓
ChromaDB (Vector Search)
    ↓
LLM generates response
```

### Ingestion Flow (Current)

```
Document Upload
    ↓
Text Splitting → Chunks
    ↓
Entity Extraction (spaCy/LLM)
    ↓
┌─────────────────────────────────┐
│ Vector DB (ChromaDB)            │ ← ✅ Used in queries
│ - Stores chunk embeddings        │
│ - Similarity search              │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ Graph DB (Neo4j)                │ ← ❌ NOT used in queries
│ - Stores entities                │
│ - Stores relationships           │
│ - Chunk-Entity links             │
└─────────────────────────────────┘
```

### Code Analysis

#### 1. RAGOrchestrator (`rag_component/main.py:206`)
```python
def query(self, user_query: str) -> Dict[str, Any]:
    """Process a user query using the RAG pipeline."""
    return self.rag_chain.get_context_and_response(user_query)
    # ❌ No graph query
```

#### 2. RAGChain (`rag_component/rag_chain.py:76`)
```python
def get_context_and_response(self, query: str) -> Dict[str, Any]:
    # Get relevant documents
    context = self.retriever.get_relevant_documents(query)  # ❌ Vector only
    
    # Generate response
    response = self.rag_chain.invoke(query)
```

#### 3. Retriever (`rag_component/retriever.py:72`)
```python
def get_relevant_documents(self, query: str) -> List[Dict[str, Any]]:
    docs_with_scores = self.retrieve_documents_with_scores(query)
    # ❌ Only uses vector_store_manager
    # ❌ No graph integration
```

#### 4. Neo4j Integration (`backend/services/rag/neo4j_integration.py`)
```python
# Has query methods but they're NEVER called during RAG queries
def query_similar_chunks(self, chunk_text: str, limit: int = 5) -> List[Dict]:
    """Query for similar chunks"""
    # ✅ Exists but unused!

def get_entity_connections(self, entity_name: str, limit: int = 20) -> List[Dict]:
    """Get connections for an entity"""
    # ✅ Exists but unused!
```

---

## Proposed Hybrid RAG Architecture

### New Query Flow

```
User Query
    ↓
┌──────────────────────────────────────────┐
│  Hybrid Retriever (NEW)                  │
│  ┌────────────────────────────────────┐  │
│  │ 1. Vector Search (Parallel)        │  │
│  │    - ChromaDB similarity search    │  │
│  │    - Returns: chunk embeddings     │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ 2. Graph Search (Parallel)         │  │
│  │    - Neo4j entity search           │  │
│  │    - Returns: entities + relations │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Smart Merger (NEW)                      │
│  - Deduplicate overlapping results       │
│  - Re-rank by combined relevance         │
│  - Expand context via graph traversal    │
│  - Weight vector vs graph scores         │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Context Builder (NEW)                   │
│  - Fetch full chunks for entities       │
│  - Add relationship context              │
│  - Format for LLM prompt                 │
└──────────────────────────────────────────┘
    ↓
LLM generates response with richer context
```

---

## Implementation Plan

### Phase 1: Add Graph Query Methods to Neo4jIntegration

**File:** `backend/services/rag/neo4j_integration.py`

```python
class Neo4jIntegration:
    # ... existing code ...
    
    def query_entities_by_text(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for entities matching query text.
        
        Args:
            query: User query text
            limit: Max entities to return
            
        Returns:
            List of entities with relevance scores
        """
        if not self.connected:
            return []
        
        try:
            with self.driver.session() as session:
                # Search entities by name containing query terms
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE e.name CONTAINS $query 
                       OR e.description CONTAINS $query
                    RETURN e.name as name, 
                           e.type as type, 
                           e.relevance as relevance,
                           e.description as description,
                           e.document as document
                    ORDER BY e.relevance DESC
                    LIMIT $limit
                """, {'query': query, 'limit': limit})
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error querying entities: {e}")
            return []
    
    def get_related_entities(self, entity_name: str, max_depth: int = 2, 
                            limit: int = 20) -> List[Dict]:
        """
        Get entities related to a given entity via graph traversal.
        
        Args:
            entity_name: Starting entity name
            max_depth: How many hops to traverse
            limit: Max results
            
        Returns:
            List of related entities with relationship info
        """
        if not self.connected:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (start:Entity {name: $name})
                    MATCH (start)-[*1..$depth]-(related:Entity)
                    RETURN related.name as name,
                           related.type as type,
                           related.relevance as relevance,
                           related.document as document
                    ORDER BY related.relevance DESC
                    LIMIT $limit
                """, {'name': entity_name, 'depth': max_depth, 'limit': limit})
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error getting related entities: {e}")
            return []
    
    def get_chunks_for_entity(self, entity_name: str, limit: int = 5) -> List[Dict]:
        """
        Get document chunks that mention a specific entity.
        
        Args:
            entity_name: Entity to find chunks for
            limit: Max chunks to return
            
        Returns:
            List of chunks with content
        """
        if not self.connected:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity {name: $name})<-[:MENTIONS]-(c:Chunk)
                    RETURN c.chunk_id as chunk_id,
                           c.content as content,
                           c.section as section,
                           c.title as title
                    LIMIT $limit
                """, {'name': entity_name, 'limit': limit})
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error getting chunks for entity: {e}")
            return []
```

---

### Phase 2: Create HybridRetriever Class

**File:** `rag_component/hybrid_retriever.py` (NEW)

```python
"""
Hybrid Retriever - Combines vector and graph-based retrieval
"""
import os
from typing import List, Dict, Any, Tuple
from .config import (
    RAG_TOP_K_RESULTS, 
    RAG_SIMILARITY_THRESHOLD,
    RAG_HYBRID_VECTOR_WEIGHT,  # New config: 0.6
    RAG_HYBRID_GRAPH_WEIGHT    # New config: 0.4
)
from .vector_store_manager import VectorStoreManager
from backend.services.rag.neo4j_integration import get_neo4j_connection


class HybridRetriever:
    """
    Hybrid retriever that combines vector similarity search 
    with graph-based entity retrieval.
    """
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager
        self.neo4j = get_neo4j_connection()
        self.top_k = RAG_TOP_K_RESULTS
        self.similarity_threshold = RAG_SIMILARITY_THRESHOLD
        self.vector_weight = RAG_HYBRID_VECTOR_WEIGHT
        self.graph_weight = RAG_HYBRID_GRAPH_WEIGHT
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve documents using hybrid approach.
        
        Args:
            query: User query
            top_k: Number of results to return
            
        Returns:
            List of documents with merged scores
        """
        if top_k is None:
            top_k = self.top_k
        
        # 1. Vector search
        vector_docs = self._vector_search(query, top_k=top_k * 2)
        
        # 2. Graph search
        graph_docs = self._graph_search(query, top_k=top_k * 2)
        
        # 3. Merge results
        merged_docs = self._merge_results(vector_docs, graph_docs, top_k)
        
        # 4. Apply threshold
        filtered_docs = [
            doc for doc in merged_docs 
            if doc.get('hybrid_score', 0) >= self.similarity_threshold
        ]
        
        return filtered_docs[:top_k]
    
    def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """Perform vector similarity search"""
        docs_with_scores = self.vector_store_manager.similarity_search_with_score(
            query=query, 
            top_k=top_k
        )
        
        formatted = []
        for doc, score in docs_with_scores:
            formatted.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'vector_score': score,
                'graph_score': 0.0,
                'source': 'vector'
            })
        
        return formatted
    
    def _graph_search(self, query: str, top_k: int) -> List[Dict]:
        """Perform graph-based entity search"""
        if not self.neo4j or not self.neo4j.connected:
            return []
        
        # Extract key terms from query (simple approach)
        query_terms = query.split()[:5]  # First 5 words
        
        entities = []
        for term in query_terms:
            if len(term) > 3:  # Skip short words
                results = self.neo4j.query_entities_by_text(term, limit=top_k // len(query_terms))
                entities.extend(results)
        
        # Deduplicate and format
        seen = set()
        formatted = []
        for entity in entities:
            if entity['name'] not in seen:
                seen.add(entity['name'])
                
                # Get chunks for this entity
                chunks = self.neo4j.get_chunks_for_entity(entity['name'], limit=2)
                
                for chunk in chunks:
                    formatted.append({
                        'content': chunk.get('content', ''),
                        'metadata': {
                            'entity_name': entity['name'],
                            'entity_type': entity['type'],
                            'document': entity.get('document', ''),
                            'chunk_id': chunk.get('chunk_id', '')
                        },
                        'vector_score': 0.0,
                        'graph_score': entity.get('relevance', 0.0) / 100.0,  # Normalize
                        'source': 'graph'
                    })
        
        return formatted
    
    def _merge_results(self, vector_docs: List[Dict], graph_docs: List[Dict], 
                      top_k: int) -> List[Dict]:
        """
        Merge vector and graph results with smart scoring.
        
        Uses reciprocal rank fusion with weighted scoring.
        """
        # Create maps for deduplication
        content_map = {}
        
        # Process vector docs
        for i, doc in enumerate(vector_docs):
            content_key = doc['content'][:100]  # Use first 100 chars as key
            rank_score = 1.0 / (i + 1)  # Reciprocal rank
            
            content_map[content_key] = {
                **doc,
                'vector_rank': rank_score,
                'graph_rank': 0.0
            }
        
        # Process graph docs
        for i, doc in enumerate(graph_docs):
            content_key = doc['content'][:100]
            rank_score = 1.0 / (i + 1)
            
            if content_key in content_map:
                # Merge with existing
                content_map[content_key]['graph_rank'] = rank_score
                content_map[content_key]['graph_score'] = max(
                    content_map[content_key]['graph_score'],
                    doc['graph_score']
                )
            else:
                content_map[content_key] = {
                    **doc,
                    'vector_rank': 0.0,
                    'graph_rank': rank_score
                }
        
        # Calculate hybrid scores
        merged = list(content_map.values())
        for doc in merged:
            # Weighted combination
            doc['hybrid_score'] = (
                self.vector_weight * (doc['vector_score'] + doc['vector_rank']) +
                self.graph_weight * (doc['graph_score'] + doc['graph_rank'])
            )
        
        # Sort by hybrid score
        merged.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return merged
```

---

### Phase 3: Update Configuration

**File:** `rag_component/config.py`

```python
# Add hybrid RAG configuration
RAG_RETRIEVER_MODE = os.getenv("RAG_RETRIEVER_MODE", "hybrid").lower()  # "vector", "graph", "hybrid"
RAG_HYBRID_VECTOR_WEIGHT = float(os.getenv("RAG_HYBRID_VECTOR_WEIGHT", "0.6"))
RAG_HYBRID_GRAPH_WEIGHT = float(os.getenv("RAG_HYBRID_GRAPH_WEIGHT", "0.4"))
RAG_GRAPH_EXPANSION_DEPTH = int(os.getenv("RAG_GRAPH_EXPANSION_DEPTH", "2"))
```

---

### Phase 4: Update RAGOrchestrator

**File:** `rag_component/main.py`

```python
class RAGOrchestrator:
    def __init__(self, llm=None):
        self.document_loader = DocumentLoader()
        self.embedding_manager = EmbeddingManager()
        self.vector_store_manager = VectorStoreManager()
        
        # Use HybridRetriever if enabled
        if RAG_RETRIEVER_MODE == "hybrid":
            from .hybrid_retriever import HybridRetriever
            self.retriever = HybridRetriever(self.vector_store_manager)
        else:
            self.retriever = Retriever(self.vector_store_manager)
        
        self.rag_chain = RAGChain(self.retriever, llm)
        self.reranker = Reranker() if RERANKER_ENABLED else None
```

---

### Phase 5: Add Graph Context Enhancement

**File:** `rag_component/context_enhancer.py` (NEW)

```python
"""
Context Enhancer - Adds graph-based context to retrieved documents
"""
from typing import List, Dict, Any
from backend.services.rag.neo4j_integration import get_neo4j_connection


class ContextEnhancer:
    """
    Enhances retrieved context with graph-based relationships.
    """
    
    def __init__(self):
        self.neo4j = get_neo4j_connection()
    
    def enhance_context(self, documents: List[Dict], query: str) -> List[Dict]:
        """
        Add related entities and relationships to documents.
        
        Args:
            documents: Retrieved documents
            query: Original user query
            
        Returns:
            Enhanced documents with graph context
        """
        if not self.neo4j or not self.neo4j.connected:
            return documents
        
        enhanced = []
        
        for doc in documents:
            # Extract entity mentions from metadata
            entity_name = doc['metadata'].get('entity_name')
            
            if entity_name:
                # Get related entities
                related = self.neo4j.get_related_entities(
                    entity_name, 
                    max_depth=2,
                    limit=5
                )
                
                # Add relationship context
                if related:
                    doc['graph_context'] = {
                        'primary_entity': entity_name,
                        'related_entities': [
                            {
                                'name': r['name'],
                                'type': r['type'],
                                'relevance': r['relevance']
                            }
                            for r in related[:5]
                        ]
                    }
            
            enhanced.append(doc)
        
        return enhanced
    
    def format_for_llm(self, documents: List[Dict]) -> str:
        """
        Format enhanced documents for LLM prompt.
        
        Returns:
            Formatted context string
        """
        formatted_sections = []
        
        for i, doc in enumerate(documents, 1):
            section = f"[Context {i}]"
            
            # Add content
            section += f"\n{doc['content']}\n"
            
            # Add source
            section += f"Source: {doc['metadata'].get('title', 'Unknown')}\n"
            
            # Add graph context if available
            if 'graph_context' in doc:
                gc = doc['graph_context']
                section += f"\nRelated Entities:\n"
                for entity in gc['related_entities']:
                    section += f"  - {entity['name']} ({entity['type']})\n"
            
            formatted_sections.append(section)
        
        return "\n\n".join(formatted_sections)
```

---

## Smart Merging Strategy

### Scoring Algorithm

```python
hybrid_score = (
    vector_weight * (vector_similarity_score + reciprocal_rank_vector) +
    graph_weight * (entity_relevance_score + reciprocal_rank_graph)
)

Where:
- vector_weight = 0.6 (default)
- graph_weight = 0.4 (default)
- reciprocal_rank = 1 / (rank_position + 1)
```

### Deduplication Strategy

1. **Content-based:** Use first 100 chars as dedup key
2. **Merge scores:** Take max of vector/graph scores when merging
3. **Preserve source:** Tag each doc with origin (vector/graph/both)

### Context Expansion

For graph-sourced documents:
1. Fetch connected entities (2 hops max)
2. Retrieve chunks mentioning those entities
3. Add as supplementary context (not primary)

---

## Testing Strategy

### Unit Tests

```python
def test_hybrid_retriever_vector_only():
    """Test when graph is unavailable"""
    retriever = HybridRetriever(vector_store_manager)
    # Should fall back to vector-only
    
def test_hybrid_retriever_merge():
    """Test result merging logic"""
    # Verify deduplication works
    # Verify scoring is correct
    
def test_context_enhancer():
    """Test graph context addition"""
    # Verify related entities are added
```

### Integration Tests

```python
def test_end_to_end_hybrid_query():
    """Test full hybrid RAG query"""
    rag = RAGOrchestrator(llm)
    result = rag.query("What GOST standards mention encryption?")
    
    # Should have both vector and graph sources
    assert any(doc['source'] == 'vector' for doc in result['context'])
    assert any(doc['source'] == 'graph' for doc in result['context'])
```

### A/B Testing

Compare:
- **Vector-only RAG** (current)
- **Hybrid RAG** (proposed)

Metrics:
- Answer relevance (user ratings)
- Context coverage (entity mentions)
- Response time (should be < 2x current)

---

## Environment Variables

Add to `.env`:

```bash
# Hybrid RAG Configuration
RAG_RETRIEVER_MODE=hybrid  # vector, graph, or hybrid
RAG_HYBRID_VECTOR_WEIGHT=0.6
RAG_HYBRID_GRAPH_WEIGHT=0.4
RAG_GRAPH_EXPANSION_DEPTH=2
```

---

## Performance Considerations

### Latency Impact

| Component | Current | With Hybrid | Notes |
|-----------|---------|-------------|-------|
| Vector Search | ~100ms | ~100ms | Unchanged |
| Graph Search | N/A | ~200ms | Parallel execution |
| Merging | N/A | ~50ms | In-memory |
| **Total** | **~100ms** | **~350ms** | Acceptable (<500ms) |

### Optimization Strategies

1. **Parallel execution:** Vector + Graph queries run concurrently
2. **Caching:** Cache entity lookups for common queries
3. **Limit graph depth:** Max 2 hops to prevent explosion
4. **Early termination:** Stop if vector results are highly relevant (>0.9)

---

## Rollback Plan

If issues occur:

```bash
# Revert to vector-only
export RAG_RETRIEVER_MODE=vector
# Restart RAG service
```

No data migration needed - purely additive change.

---

## Implementation Priority

### Must Have (MVP)
1. ✅ Neo4j query methods (Phase 1)
2. ✅ HybridRetriever class (Phase 2)
3. ✅ Config updates (Phase 3)
4. ✅ RAGOrchestrator integration (Phase 4)

### Should Have
5. ✅ ContextEnhancer (Phase 5)
6. ✅ Smart merging with reciprocal rank fusion

### Nice to Have
7. ⏸️ Caching layer for graph queries
8. ⏸️ Query rewriting for better entity extraction
9. ⏸️ Analytics on vector vs graph contribution

---

## Next Steps

1. **Review this proposal** - Confirm approach
2. **Implement Phase 1-4** - Core functionality
3. **Test with sample queries** - Verify hybrid works
4. **Tune weights** - Adjust vector/graph balance
5. **Deploy to staging** - A/B test
6. **Monitor & iterate** - Optimize based on usage

---

## Questions?

Key decisions needed:
1. **Weight balance:** 60/40 vector/graph or different?
2. **Graph depth:** 2 hops enough or need 3?
3. **Fallback:** Always use both or conditional?

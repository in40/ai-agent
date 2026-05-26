# GOST Documents Re-processing Strategy for Graph Ingestion

## Executive Summary

Analysis of 112 GOST information security standards stored in Document Store.
All documents have been pre-processed (PDF → TXT/MD → chunks.json) and are ready 
for re-processing with improved entity extraction for Neo4j graph ingestion.

## Current State

### Document Inventory
- **Location**: `document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/`
- **Total Documents**: 112 GOST standards
- **Formats**: PDF, TXT, MD, chunks.json (already chunked)
- **Chunk Structure**: Smart LLM-based chunking with metadata

### Existing Entity Extraction Methods

1. **spaCy + Patterns** (`entity_extractor.py`)
   - Fast, offline, Russian/English support
   - Custom patterns for GOST standards in `custom_entity_types.py`
   
2. **LLM-based** (`llm_entity_extractor.py`, `graphrag_service.py`)
   - Context-aware, uses qwen3-4b via LM Studio
   - Extracts entities + relationships together

3. **Neo4j Integration** (`neo4j_integration.py`)
   - Stores chunks, entities, and MENTIONS relationships
   - Supports graph traversal queries

## Recommended Strategy: Hybrid Approach

### Why Hybrid?
- **80% entities** via fast pattern matching (spaCy + regex)
- **20% high-value relationships** via LLM
- Balanced cost/performance for 112 documents

### Entity Types for GOST Standards

```python
GOST_ENTITY_TYPES = {
    "STANDARD_REFERENCE": "GOST R XXXXX-YYYY formats",
    "REGULATORY_DOCUMENT": "Federal laws, decrees (152-FZ)",
    "ORGANIZATION_RU": "FSTEC, FSB, federal agencies",
    "TECHNICAL_SYSTEM": "Crypto systems, SKZI",
    "CRYPTO_TERM": "Encryption, signatures, hashes",
    "SECURITY_CONCEPT": "Authentication, authorization",
    "TRUST_LEVEL": "Levels 1-5 with criteria",
    "REQUIREMENT": "Mandatory conditions (должен)",
    "DOCUMENT_SECTION": "Раздел, Приложение, Пункт",
    "DATE_RU": "Russian date formats"
}
```

### Processing Pipeline

```
1. Load chunks.json → 2. Pattern extraction (fast) → 
3. LLM enrichment (intelligent) → 4. Merge entities → 
5. Store in Neo4j with relationships
```

## Implementation Steps

### Step 1: Assessment (Immediate)
- Analyze chunk quality across all 112 documents
- Run baseline entity extraction on samples
- Validate Neo4j schema compatibility

### Step 2: Pattern Enhancement (Week 1)
- Update `custom_entity_types.py` with GOST-specific patterns
- Add Russian organization name patterns
- Include security terminology dictionary

### Step 3: Batch Processing (Weeks 2-3)
- Process documents in batches of 10-20
- Use hybrid extraction method
- Monitor LLM token usage and costs

### Step 4: Graph Construction (Week 4)
- Load entities into Neo4j
- Create relationships between entities
- Link chunks to entities via MENTIONS

### Step 5: Validation (Week 5)
- Manual quality review of extracted entities
- Test graph queries for RAG
- Measure precision/recall

## Key Files

### Existing (to modify):
- `backend/services/rag/nlp_tools/custom_entity_types.py`
- `backend/services/rag/nlp_tools/entity_extractor.py`
- `backend/services/rag/graphrag_service.py`
- `backend/services/rag/neo4j_integration.py`

### New to create:
- `reprocess_gost_documents.py` - Main processing script
- `entity_extraction_validation.py` - Quality assessment
- `graph_query_examples.py` - Test queries

## Quick Start Script

See: `reprocess_gost_documents.py` (to be created)

```bash
# Process all documents
python reprocess_gost_documents.py --strategy hybrid --batch-size 10

# Validate results
python entity_extraction_validation.py --graph-stats

# Test queries
python graph_query_examples.py
```

## Expected Outcomes

- **112 documents** fully processed with entities
- **~5,000-10,000 entities** extracted (est. 50-100 per document)
- **~10,000-20,000 relationships** in Neo4j graph
- **Enhanced RAG** with graph-based retrieval
- **Better answers** for security standard queries

## Next Actions

1. Review this strategy document
2. Select extraction strategy (recommended: Hybrid)
3. Create and test reprocessing script on 5 sample documents
4. Validate entity quality manually
5. Scale to all 112 documents

---

Full technical details, code examples, and implementation plans available in the complete strategy document.

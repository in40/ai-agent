# AI Agent - GOST Knowledge Graph Project Summary

## Overview
Built a complete knowledge graph extraction and visualization pipeline for Russian GOST (ГОСТ) cryptographic standards documents, storing entities and relationships in Neo4j graph database.

---

## Phase 1: Data Extraction

### 1.1 Entity Extraction
**Goal**: Extract named entities from 112 GOST documents

**Results**:
- **1,059 raw entities** extracted from 112 documents
- Entity types: ORGANIZATION (357), STANDARD (255), CONCEPT (238), DATE (152), LOCATION (54)

**Method**: Hybrid approach
- Pattern-based extraction (regex for GOST numbers, dates, org names)
- LLM validation for quality assurance

**Key Files**:
- `/root/qwen/ai_agent/extraction_results_final/all_entities.json` (174KB)

### 1.2 Formula Extraction
**Goal**: Extract cryptographic formulas from 63 cryptography-focused documents

**Results**:
- **4,275 formulas** extracted
- Types: VARIABLE_ASSIGNMENT (3,407), KEY_MATERIAL (594), CRYPTO_FUNCTION (161), TRAFFIC_SECRET (113)

**Key Files**:
- `/root/qwen/ai_agent/extraction_results_with_formulas/all_formulas.json` (577KB)

---

## Phase 2: Entity Deduplication

### 2.1 Initial Attempt (WRONG - Aggressive)
**Problem**: Over-merged distinct entities using fuzzy matching with 0.85 threshold

**What Went Wrong**:
- ❌ "Стандартинформ" + "Москва Стандартинформ 2018" → merged (different entities)
- ❌ "ГОСТ Р 34.11-2012" + "ГОСТ Р 34.12-2015" + "ГОСТ Р 34.13-2015" → merged (different standards)
- ❌ "29 июня 2015 г." + "№ 162-ФЗ" → merged (date vs law number)

**Results**: 1,059 → 271 entities (74.4% reduction, but many false positives)

### 2.2 Corrected Approach (Strict)
**Solution**: Conservative deduplication with 0.95 threshold and strict rules

**Rules Applied**:
- ✅ Merge: "ФСТЭК" → "ФСТЭК России" (abbreviation)
- ✅ Merge: Typos like "ФГУ" vs "ФГУП" (same org, different prefix)
- ❌ NO MERGE: Different GOST numbers (34.11 ≠ 34.12)
- ❌ NO MERGE: Different dates/laws
- ❌ NO MERGE: "Стандартинформ" ≠ "Москва Стандартинформ 2018"

**Results**:
- **469 unique entities** (55.7% reduction, correct merges only)
- **590 duplicates merged** into canonical forms

**Key Files**:
- `/root/qwen/ai_agent/deduplicate_entities_strict.py` (deduplication script)
- `/root/qwen/ai_agent/deduplicated_entities_strict/all_entities_strict.json` (deduplicated entities)
- `/root/qwen/ai_agent/deduplicated_entities_strict/deduplication_stats_strict.json` (merge statistics)

### 2.3 Key Entity Merges

| Canonical Entity | Merged From | Count |
|-----------------|-------------|-------|
| ФСТЭК России | "ФСТЭК", "Федеральная служба по техническому и экспортному контролю" | 10 |
| ФГУ «ГНИИПИ ПТСЗИ ФСТЭК России» | Various typos (ФГУП, ФАУ, ГНИИИ) | 5 |
| ФЕДЕРАЛЬНОЕ АГЕНТСТВО ПО ТЕХНИЧЕСКОМУ РЕГУЛИРОВАНИЮ И МЕТОРОЛОГИИ | Case/formatting variants | 89 |
| Технический комитет по стандартизации ТК 362 | "ТК 362", "ТК 026" | 16 |

---

## Phase 3: Neo4j Graph Database Setup

### 3.1 Initial Load
**Goal**: Load deduplicated entities into Neo4j with relationships

**Connection Setup**:
- Neo4j URI: `bolt://localhost:7687` (via SSH tunnel to 192.168.51.187)
- User: `neo4j`
- Password: `GraphRAG2024!`

**Schema**:
```cypher
(:Entity {name, text, normalized_name, type, relevance, aliases, doc_names})
(:Document {name, type})
(:MENTIONS)-relationship between Entity and Document
(:CO_OCCURS_WITH)-relationship between Entity and Entity
```

**Key Files**:
- `/root/qwen/ai_agent/clear_and_load_neo4j.py` (loading script)

### 3.2 First Results
- **469 entities** loaded
- **107 documents** loaded
- **635 MENTIONS relationships** (Entity → Document)

**Problem**: No entity-to-entity connections visible in UI

---

## Phase 4: Fixing Orphaned Entities

### 4.1 Problem Identification
Many entities had no connections because:
1. `doc_names` field lost during deduplication (405+ entities affected)
2. Missing Document nodes for some documents
3. No CO_OCCURS_WITH relationships created

### 4.2 Fixes Applied

#### Fix 1: Recreate MENTIONS from Original Data
- Loaded original extraction data (before deduplication)
- Rebuilt all Entity → Document relationships
- Result: 946 MENTIONS relationships

#### Fix 2: Create Missing Documents
- Identified 3 documents referenced by entities but missing in Neo4j
- Created missing Document nodes
- Total documents: 110

#### Fix 3: Generate CO_OCCURS_WITH Relationships
```cypher
MATCH (e1:Entity)-[:MENTIONS]->(d:Document)<-[:MENTIONS]-(e2:Entity)
WHERE e1.normalized_name < e2.normalized_name
MERGE (e1)-[r:CO_OCCURS_WITH]->(e2)
ON CREATE SET r.count = 1
```
- Result: 4,461 CO_OCCURS_WITH relationships

#### Fix 4: Delete/Correct Bad Entities
**Deleted artifacts** (extraction errors):
- THE, FOR, CHUNK, MANDATORY, EVERY, FIELD IS, BEFORE YOU RESPOND, FINAL REMINDER, ⚠️

**Merged typos**:
- МOSCВА (Latin O) → Москва (Cyrillic)

**Fixed types**:
- ГОСУДАРСТВЕННЫЙ СТАНДАРТ РОССИЙСКОЙ ФЕДЕРАЦИИ: ORGANIZATION → CONCEPT
- ГОСТ Р 50739—95: CONCEPT → STANDARD
- П 50.1.110-2016: DATE → STANDARD

**Split combined entities**:
- СТАНДАРТНИФОРМ 2017 → "Стандартинформ" [ORGANIZATION] + "2017" [DATE]

### 4.3 Final Entity Stats
| Metric | Value |
|--------|-------|
| Total Entities | 458 |
| Total Documents | 110 |
| MENTIONS Relationships | 946 |
| CO_OCCURS_WITH Relationships | 4,461 |
| Orphaned Entities | **0** ✅ |

---

## Phase 5: Graph Visualization Fix

### 5.1 Problem
UI showed "No connections found" for entities that DO have connections in Neo4j.

### 5.2 Root Cause
The `graph_visualize` endpoint had three bugs:

1. **Limited relationship scope**: Only returned relationships where BOTH source AND target were in the initial 500 entity limit
   ```cypher
   // WRONG - only matches if both endpoints in initial set
   WHERE source.name IN $names AND target.name IN $names
   ```

2. **NULL relevance sorting**: All entities had NULL relevance, causing unpredictable ordering
   ```cypher
   // WRONG - NULL values sort unpredictably
   ORDER BY e.relevance DESC
   ```

3. **No connected node inclusion**: Connected entities outside the initial 500 weren't added to node list

### 5.3 Fixes Applied

**File**: `/root/qwen/ai_agent/backend/services/rag/app.py` (lines ~4079-4123)

```python
# Fix 1: Get ALL relationships from selected entities (not just mutual)
entity_rel_query = """
    MATCH (source:Entity)-[r]-(target:Entity)
    WHERE source.name IN $names  # ← Removed target filter
    RETURN source.name as source, target.name as target, 
           target.type as target_type, type(r) as relationship
    LIMIT 5000
"""

# Fix 2: Add connected entities as nodes
if len(connected_node_names) > len(node_names):
    additional_nodes_query = """
        MATCH (e:Entity)
        WHERE e.name IN $names AND NOT e.name IN $original_names
        RETURN e.name as name, e.type as type, e.relevance as relevance
        LIMIT 1000
    """

# Fix 3: Handle NULL relevance
entity_query = """
    MATCH (e:Entity)
    WHERE true {type_filter} {search_filter}
    RETURN e.name as name, e.type as type, e.relevance as relevance
    ORDER BY COALESCE(e.relevance, 0) DESC  # ← Handle NULL
    LIMIT $limit
"""
```

### 5.4 To Apply Fixes
```bash
# Restart RAG service
pkill -f "backend.services.rag.app"
cd /root/qwen/ai_agent && source ai_agent_env/bin/activate && python -m backend.services.rag.app &

# Or restart all services
./start_all_services.sh

# Clear browser cache and refresh
```

---

## Final State

### Data Summary
| Component | Count |
|-----------|-------|
| GOST Documents | 112 |
| Unique Entities | 458 |
| Document Nodes | 110 |
| MENTIONS Relationships | 946 |
| CO_OCCURS_WITH Relationships | 4,461 |
| Total Relationships | 5,407 |

### Entity Types Distribution
| Type | Count |
|------|-------|
| ORGANIZATION | ~108 |
| CONCEPT | ~148 |
| STANDARD | ~106 |
| DATE | ~95 |
| LOCATION | ~9 |

### Key Organizations Merged
- **ФСТЭК России** (Federal Service for Technical and Export Control)
- **Российский институт стандартизации** (Russian Institute for Standardization)
- **Технический комитет по стандартизации ТК 362** (Technical Committee 362)
- **ООО «КРИПТО-ПРО»** (Crypto-Pro LLC)

### Files Created/Modified
1. `/root/qwen/ai_agent/deduplicate_entities_strict.py` - Conservative deduplication
2. `/root/qwen/ai_agent/clear_and_load_neo4j.py` - Neo4j loading script
3. `/root/qwen/ai_agent/backend/services/rag/app.py` - Graph visualization endpoint (FIXED)
4. `/root/qwen/ai_agent/deduplicated_entities_strict/all_entities_strict.json` - Final entity data

---

## Known Issues & Limitations

1. **Entity relevance scores**: All entities have NULL relevance (not calculated yet)
2. **Some extraction artifacts**: Rare edge cases may still slip through
3. **Graph visualization**: Requires service restart after code changes

## Next Steps (Optional)
1. Calculate entity relevance scores based on document importance
2. Add formula-to-entity relationships
3. Implement entity disambiguation for ambiguous names
4. Add semantic search over entity descriptions


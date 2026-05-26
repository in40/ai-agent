# GOST Knowledge Graph

**Russian GOST Cryptographic Standards Knowledge Graph**

A complete knowledge graph extraction and visualization pipeline for Russian GOST (ГОСТ) cryptographic standards documents, built with Neo4j graph database.

---

## 📊 Project Overview

This project extracts entities (organizations, standards, concepts, dates) from 112 GOST documents, deduplicates them using strict rules, and loads them into a Neo4j graph database with relationships showing document mentions and entity co-occurrences.

### Current Status
✅ **Production Ready** - All verifications passing

| Metric | Value |
|--------|-------|
| Documents Processed | 112 |
| Unique Entities | 458 |
| Document Nodes | 110 |
| MENTIONS Relationships | 953 |
| CO_OCCURS_WITH Relationships | 3,714 |
| Orphaned Entities | **0** ✅ |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Neo4j database (accessible via SSH tunnel)
- Virtual environment with dependencies

### Installation

```bash
# Create virtual environment
python -m venv ai_agent_env
source ai_agent_env/bin/activate

# Install dependencies
pip install neo4j

# Setup SSH tunnel (if needed)
ssh -N -f -i ~/.ssh/id_ed25519_graphrag \
    -L 7687:localhost:7687 \
    sorokin@192.168.51.187
```

### Running the Pipeline

```bash
# Run complete pipeline (deduplication + Neo4j loading)
python gost_knowledge_graph_pipeline.py --input extraction_results_final/all_entities.json

# Verify database
python verify_knowledge_graph.py
```

---

## 📁 Project Structure

```
/root/qwen/ai_agent/
├── gost_knowledge_graph_pipeline.py    # Main pipeline script
├── verify_knowledge_graph.py           # Database verification script
├── deduplicate_entities_strict.py      # Standalone deduplication script
├── clear_and_load_neo4j.py            # Neo4j loading script (legacy)
├── KNOWLEDGE_BASE_SUMMARY.md          # Detailed project documentation
├── README.md                          # This file
├── extraction_results_final/
│   └── all_entities.json              # Raw extracted entities (1,059)
├── deduplicated_entities_strict/
│   ├── all_entities_strict.json       # Deduplicated entities (469)
│   └── deduplication_stats_strict.json # Merge statistics
└── knowledge_graph_output/            # Pipeline output directory
    ├── final_entities.json            # Final entity list with corrections
    └── deduplication_stats.json       # Deduplication statistics
```

---

## 🔧 Core Components

### 1. Entity Deduplication (`gost_knowledge_graph_pipeline.py`)

**Strict Deduplication Rules:**

✅ **MERGE** (true variants):
- "ФСТЭК" → "ФСТЭК России" (abbreviation)
- Typos: "ФГУ" vs "ФГУП" (same organization)
- Case/formatting: "ГОСТ Р 34.11—2012" vs "ГОСТ Р 34.11-2012"

❌ **NO MERGE** (different entities):
- Different GOST numbers: 34.11 ≠ 34.12 ≠ 34.13
- Different dates/laws: "29 июня 2015 г." ≠ "№ 162-ФЗ"
- Different organizations: "Стандартинформ" ≠ "Москва Стандартинформ 2018"

**Configuration:**
```python
# Threshold for similarity (0.95 = very strict)
self.dedup_threshold = 0.95

# Abbreviation rules
self.abbreviation_rules = {
    'фстэк': ['фстэк россии', 'федеральная служба...'],
    'ооо': ['общество с ограниченной ответственностью'],
    # ... more rules
}

# Entities to delete (extraction artifacts)
self.artifacts_to_delete = {'THE', 'FOR', 'CHUNK', ...}

# Type corrections
self.type_corrections = {
    'ГОСТ Р 50739—95': 'STANDARD',  # Not CONCEPT
    # ... more corrections
}
```

### 2. Neo4j Loading (`gost_knowledge_graph_pipeline.py`)

**Schema:**
```cypher
// Entity nodes
(:Entity {
    name: string,              // Primary identifier (for UI)
    text: string,              // Original text
    normalized_name: string,   // Lowercase for matching
    type: string,              // ORGANIZATION, STANDARD, CONCEPT, DATE, LOCATION
    merge_count: int,          // How many duplicates were merged
    aliases: list              // Other name variants
})

// Document nodes
(:Document {
    name: string,
    type: 'GOST'
})

// Relationships
(:Entity)-[:MENTIONS]->(:Document)       // Entity mentioned in document
(:Entity)-[:CO_OCCURS_WITH]->(:Entity)   // Entities appear together
```

**Relationship Creation:**
```cypher
// MENTIONS (Entity → Document)
MATCH (e:Entity)
UNWIND e.doc_names AS doc_name
MATCH (d:Document {name: doc_name})
CREATE (e)-[:MENTIONS]->(d)

// CO_OCCURS_WITH (Entity ↔ Entity)
MATCH (e1:Entity)-[:MENTIONS]->(d:Document)<-[:MENTIONS]-(e2:Entity)
WHERE e1.normalized_name < e2.normalized_name
MERGE (e1)-[r:CO_OCCURS_WITH]->(e2)
ON CREATE SET r.count = 1
```

### 3. Graph Visualization Fix (`backend/services/rag/app.py`)

**Fixed Issues:**
1. ✅ Get ALL connected entities (not just mutual connections)
2. ✅ Include connected entities as nodes in visualization
3. ✅ Handle NULL relevance scores with COALESCE

**Key Changes:**
```python
# Before: Only relationships where BOTH endpoints in initial set
WHERE source.name IN $names AND target.name IN $names

# After: Get ALL relationships from selected entities
WHERE source.name IN $names

# Add connected entities to node list
if len(connected_node_names) > len(node_names):
    additional_nodes_query = """
        MATCH (e:Entity)
        WHERE e.name IN $names AND NOT e.name IN $original_names
        RETURN e.name as name, ...
    """
```

---

## 📈 Entity Statistics

### Distribution by Type
| Type | Count | Percentage |
|------|-------|------------|
| CONCEPT | 138 | 30.1% |
| STANDARD | 108 | 23.6% |
| ORGANIZATION | 107 | 23.4% |
| DATE | 94 | 20.5% |
| LOCATION | 8 | 1.7% |
| Mixed Types | 3 | 0.7% |

### Key Organizations (by connections)
| Organization | Connections |
|--------------|-------------|
| Технический комитет по стандартизации ТК 362 | 175 |
| Стандартинформ | 170 |
| Российский институт стандартизации | 107 |
| ФЕДЕРАЛЬНОЕ АГЕНТСТВО ПО ТЕХНИЧЕСКОМУ РЕГУЛИРОВАНИЮ И МЕТРОЛОГИИ | 89 |
| ФСТЭК России | 35 |

---

## 🛠️ Maintenance & Troubleshooting

### Restart Services After Code Changes

```bash
# Restart RAG service (for graph visualization fixes)
pkill -f "backend.services.rag.app"
cd /root/qwen/ai_agent && source ai_agent_env/bin/activate
python -m backend.services.rag.app &

# Or restart all services
./start_all_services.sh
```

### Clear Browser Cache
After service restart, clear browser cache:
- Chrome/Edge: Ctrl+Shift+Delete
- Firefox: Ctrl+Shift+Delete

### Rebuild Database from Scratch

```bash
# Run complete pipeline (clears and reloads Neo4j)
python gost_knowledge_graph_pipeline.py --input extraction_results_final/all_entities.json

# Verify
python verify_knowledge_graph.py
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "No connections found" in UI | Restart RAG service + clear browser cache |
| Orphaned entities | Run pipeline again to rebuild relationships |
| Wrong entity types | Check `type_corrections` in pipeline script |
| Missing documents | Pipeline creates missing docs automatically |

---

## 📝 Data Quality Improvements Applied

### 1. Deleted Extraction Artifacts
Removed noise from extraction:
- THE, FOR, CHUNK, MANDATORY, EVERY, FIELD IS
- BEFORE YOU RESPOND, FINAL REMINDER, ⚠️

### 2. Fixed Entity Types
Corrected misclassified entities:
- ГОСУДАРСТВЕННЫЙ СТАНДАРТ РОССИЙСКОЙ ФЕДЕРАЦИИ: ORGANIZATION → CONCEPT
- ГОСТ Р 50739—95: CONCEPT → STANDARD
- П 50.1.110-2016: DATE → STANDARD

### 3. Split Combined Entities
Separated combined entity names:
- "СТАНДАРТНИФОРМ 2017" → "Стандартинформ" [ORGANIZATION] + "2017" [DATE]

### 4. Merged Typo Variants
Fixed character encoding issues:
- "МOSCВА" (Latin O) → merged into "Москва" (Cyrillic)

---

## 🔐 Configuration

### Neo4j Connection
```python
NEO4J_URI = "bolt://localhost:7687"      # Via SSH tunnel
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "GraphRAG2024!"
NEO4J_SSH_HOST = "192.168.51.187"
NEO4J_SSH_USER = "sorokin"
NEO4J_SSH_KEY = "~/.ssh/id_ed25519_graphrag"
```

### Deduplication Parameters
```python
dedup_threshold = 0.95  # Higher = more conservative
min_length_diff = 3     # Minimum char difference for variants
```

---

## 📚 References

- **KNOWLEDGE_BASE_SUMMARY.md** - Detailed project history and all changes made
- **extraction_results_final/all_entities.json** - Raw extraction data
- **deduplicated_entities_strict/** - Deduplication results and statistics

---

## 🔄 Next Steps (Optional Enhancements)

1. **Entity Relevance Scoring** - Calculate importance based on document frequency
2. **Formula-to-Entity Links** - Connect cryptographic formulas to standards
3. **Semantic Search** - Add vector embeddings for entity similarity search
4. **Entity Disambiguation** - Handle ambiguous names (e.g., multiple "ТК 26")
5. **Version History** - Track changes to entities over time

---

## 📄 License

Internal use only - Russian GOST standards documentation

---

*Last Updated: 2026-05-07*
*Status: ✅ Production Ready*

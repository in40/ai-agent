# GOST Graph Database Loading Strategy

## Current State

### Extracted Data
- **1,059 Entities**: ORGANIZATION, STANDARD, CONCEPT, DATE, LOCATION
- **4,275 Formulas**: CRYPTO_FUNCTION, VARIABLE_ASSIGNMENT, KEY_MATERIAL, TRAFFIC_SECRET
- **110 Documents**: With chunk metadata

---

## 1. Graph Schema Design

### Node Types

```cypher
// Core entities
(:Document {doc_id, filename, standard_number, created_date})
(:Entity {name, type, description, source_doc})
(:Formula {expression, type, formula_category})
(:Chunk {chunk_id, content_preview, doc_id, chunk_index})

// Supporting nodes
(:Standard {standard_number, title, status, year})
(:Organization {name, full_name, country, type})
(:Concept {name, definition, domain})
(:Date {date_value, date_type, context})
(:Location {name, type, country})
```

### Relationship Types

```cypher
// Document structure
(:Document)-[:HAS_CHUNK]->(:Chunk)
(:Chunk)-[:CONTAINS_ENTITY]->(:Entity)
(:Chunk)-[:CONTAINS_FORMULA]->(:Formula)

// Entity relationships (semantic)
(:Entity)-[:MENTIONS]->(:Entity)
(:Entity)-[:RELATED_TO]->(:Entity)
(:Entity)-[:DEFINED_IN]->(:Document)
(:Entity)-[:APPEARS_IN]->(:Chunk)

// Standard-specific relationships
(:Standard)-[:REFERENCES]->(:Standard)
(:Standard)-[:DEVELOPED_BY]->(:Organization)
(:Standard)-[:APPROVED_ON]->(:Date)
(:Standard)-[:LOCATED_IN]->(:Location)
(:Standard)-[:DEFINES]->(:Concept)
(:Standard)-[:CONTAINS_FORMULA]->(:Formula)

// Formula relationships (crypto)
(:Formula)-[:USES_FUNCTION]->(:Formula)
(:Formula)-[:DERIVES_FROM]->(:Formula)
(:Formula)-[:DEFINED_AS]->(:Entity)
```

---

## 2. Loading Strategy - 3 Approaches

### Approach A: Basic Loading (Fastest)
**What**: Load entities as-is, no relationships
**Steps**:
1. Create nodes for all entities and formulas
2. Link to documents via chunk metadata
3. No relationship inference

**Pros**: 
- Fast (minutes)
- Simple implementation
- Good baseline for search

**Cons**:
- No semantic connections
- Limited query capabilities
- Just a collection of facts

**Code Example**:
```python
def load_basic_graph(entities, formulas, output_dir):
    """Load entities as nodes only"""
    import json
    
    # Create node lists
    nodes = []
    
    for ent in entities:
        nodes.append({
            'label': 'Entity',
            'properties': {
                'name': ent['text'],
                'type': ent['type'],
                'source': ent.get('source', 'pattern'),
                'doc_name': ent.get('doc', '')
            }
        })
    
    for formula in formulas:
        nodes.append({
            'label': 'Formula',
            'properties': {
                'expression': formula['text'],
                'type': formula['type'],
                'doc_name': formula.get('doc_name', '')
            }
        })
    
    # Save for bulk import
    with open(f"{output_dir}/nodes.json", 'w') as f:
        json.dump(nodes, f)
```

---

### Approach B: Smart Loading (Recommended)
**What**: Load entities + infer relationships based on co-occurrence
**Steps**:
1. Load all nodes (entities, formulas, documents, chunks)
2. Create MENTIONS relationships (chunk → entity/formula)
3. Infer ENTITY-ENTITY relationships from same chunk
4. Add STANDARD-specific relationships

**Pros**:
- Good query capabilities
- Reasonable accuracy
- Still fast (30-60 min)

**Cons**:
- Some false positive relationships
- Co-occurrence ≠ semantic relationship

**Relationship Inference Rules**:

```python
def infer_relationships(entities, formulas, chunks_info):
    """
    Infer relationships based on co-occurrence patterns
    """
    relationships = []
    
    # Rule 1: Same chunk → MENTIONS relationship
    for chunk_id, chunk_entities in chunks_info.items():
        for i, ent1 in enumerate(chunk_entities):
            for ent2 in chunk_entities[i+1:]:
                # Both entities in same chunk
                relationships.append({
                    'source': ent1['name'],
                    'target': ent2['name'],
                    'type': 'MENTIONS',
                    'confidence': 0.7,
                    'evidence': f'same_chunk:{chunk_id}'
                })
    
    # Rule 2: Standard references other standards
    for entity in entities:
        if entity['type'] == 'STANDARD':
            # Look for other standards mentioned in same doc
            doc_entities = get_entities_in_doc(entity['doc_name'])
            for other in doc_entities:
                if other['type'] == 'STANDARD' and other['name'] != entity['name']:
                    relationships.append({
                        'source': entity['name'],
                        'target': other['name'],
                        'type': 'REFERENCES',
                        'confidence': 0.6,
                        'evidence': f'same_document:{entity["doc_name"]}'
                    })
    
    # Rule 3: Organization developed Standard
    for entity in entities:
        if entity['type'] == 'ORGANIZATION':
            doc_entities = get_entities_in_doc(entity['doc_name'])
            for other in doc_entities:
                if other['type'] == 'STANDARD':
                    relationships.append({
                        'source': other['name'],
                        'target': entity['name'],
                        'type': 'DEVELOPED_BY',
                        'confidence': 0.8,
                        'evidence': f'co_occurrence'
                    })
    
    # Rule 4: Formula uses crypto function
    for formula in formulas:
        if formula['type'] == 'VARIABLE_ASSIGNMENT':
            # Check if formula text contains crypto function name
            for other_formula in formulas:
                if other_formula['type'] == 'CRYPTO_FUNCTION':
                    if other_formula['text'] in formula['expression']:
                        relationships.append({
                            'source': formula['expression'],
                            'target': other_formula['text'],
                            'type': 'USES_FUNCTION',
                            'confidence': 0.9,
                            'evidence': 'text_contains'
                        })
    
    return relationships
```

---

### Approach C: LLM-Enhanced Loading (Best Quality)
**What**: Use LLM to validate and infer semantic relationships
**Steps**:
1. Load all nodes (Approach A)
2. Send entity pairs to LLM for relationship validation
3. Extract explicit relationships from text
4. Create high-confidence relationships only

**Pros**:
- Highest quality relationships
- Semantic accuracy
- Rich relationship types

**Cons**:
- Slow (hours for 112 docs)
- Expensive (LLM calls)
- Complex implementation

**LLM Relationship Extraction Prompt**:

```python
RELATIONSHIP_EXTRACTION_PROMPT = """
Extract relationships between entities in this text.

Entity Types:
- STANDARD: Technical standards (GOST, ISO)
- ORGANIZATION: Companies, agencies
- CONCEPT: Abstract concepts
- FORMULA: Mathematical expressions

Relationship Types:
- REFERENCES: A cites or mentions B
- DEVELOPED_BY: Standard created by Organization
- DEFINES: Standard defines Concept
- USES: Formula uses Function
- RELATED_TO: General association

Text: {chunk_text}

Entities found: {entity_list}

Return JSON ONLY:
{{
  "relationships": [
    {{
      "source": "entity name",
      "target": "entity name", 
      "type": "RELATIONSHIP_TYPE",
      "confidence": 0.0-1.0,
      "evidence": "text snippet"
    }}
  ]
}}
"""
```

---

## 3. Recommended Implementation Plan

### Phase 1: Basic Graph (Week 1)
**Goal**: Get entities into Neo4j quickly
**Steps**:
1. Create Neo4j schema with indexes
2. Load all entities as nodes
3. Link to documents/chunks
4. No relationships yet

**Cypher Schema**:
```cypher
// Create constraints
CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE;
CREATE CONSTRAINT formula_expr IF NOT EXISTS FOR (f:Formula) REQUIRE f.expression IS UNIQUE;
CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE;

// Create indexes
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX formula_type IF NOT EXISTS FOR (f:Formula) ON (f.type);
```

**Loading Script**:
```python
def load_to_neo4j_basic(entities, formulas):
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    
    with driver.session() as session:
        # Load entities
        for ent in entities:
            session.run("""
                MERGE (e:Entity {name: $name})
                SET e.type = $type,
                    e.source = $source,
                    e.doc_name = $doc_name
            """, {
                'name': ent['text'],
                'type': ent['type'],
                'source': ent.get('source', 'pattern'),
                'doc_name': ent.get('doc', '')
            })
        
        # Load formulas
        for formula in formulas:
            session.run("""
                MERGE (f:Formula {expression: $expr})
                SET f.type = $type,
                    f.doc_name = $doc_name
            """, {
                'expr': formula['text'],
                'type': formula['type'],
                'doc_name': formula.get('doc_name', '')
            })
```

---

### Phase 2: Add Relationships (Week 2)
**Goal**: Infer relationships from co-occurrence
**Steps**:
1. Run relationship inference algorithm
2. Create MENTIONS, REFERENCES, DEVELOPED_BY relationships
3. Add confidence scores
4. Validate sample relationships manually

**Loading Script**:
```python
def load_relationships(relationships):
    from neo4j import GraphDatabase
    
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    
    with driver.session() as session:
        for rel in relationships:
            session.run("""
                MATCH (source {name: $source_name})
                MATCH (target {name: $target_name})
                MERGE (source)-[r:MENTIONS]->(target)
                SET r.confidence = $confidence,
                    r.evidence = $evidence
            """, {
                'source_name': rel['source'],
                'target_name': rel['target'],
                'confidence': rel.get('confidence', 0.5),
                'evidence': rel.get('evidence', '')
            })
```

---

### Phase 3: LLM Enhancement (Optional, Week 3-4)
**Goal**: Improve relationship quality with LLM validation
**Steps**:
1. Select high-value entity pairs (top 100 per document)
2. Send to LLM for relationship validation
3. Add validated relationships to graph
4. Remove low-confidence inferred relationships

---

## 4. Query Examples (After Loading)

### Basic Queries
```cypher
// Find all entities by type
MATCH (e:Entity {type: 'STANDARD'}) RETURN e.name, e.type LIMIT 20;

// Find organizations that developed standards
MATCH (s:Standard)-[:DEVELOPED_BY]->(o:Organization) 
RETURN s.name, o.name LIMIT 20;

// Find all formulas in a document
MATCH (f:Formula)-[:APPEARS_IN]->(c:Chunk)-[:HAS_CHUNK]->(d:Document {doc_id: 'r-1323565.1_78b35e61'})
RETURN f.expression, f.type;

// Find related entities
MATCH (e1:Entity {name: 'ФСТЭК России'})-[:MENTIONS]-(e2:Entity)
RETURN e2.name, e2.type LIMIT 20;
```

### Advanced Queries
```cypher
// Graph traversal: Standard → Organization → Other Standards
MATCH path = (s1:Standard)-[:DEVELOPED_BY]->(o:Organization)<-[:DEVELOPED_BY]-(s2:Standard)
WHERE s1.name <> s2.name
RETURN s1.name, o.name, s2.name LIMIT 20;

// Find crypto function usage patterns
MATCH (f1:Formula)-[:USES_FUNCTION]->(f2:Formula {type: 'CRYPTO_FUNCTION'})
WHERE f2.expression = 'HKDF-Expand-Label'
RETURN f1.expression, COUNT(*) as usage_count
ORDER BY usage_count DESC LIMIT 10;

// Entity centrality (most connected entities)
MATCH (e:Entity)-[]-(related)
RETURN e.name, COUNT(related) as connection_count
ORDER BY connection_count DESC LIMIT 20;
```

---

## 5. Additional Steps Needed?

### A. Entity Deduplication (Required)
**Problem**: Same entity may appear multiple times with variations
- "ФСТЭК России" vs "Федеральная служба по техническому и экспортному контролю"
- "ГОСТ Р 52633-2014" vs "ГОСТ Р 52633—2014"

**Solution**:
```python
def deduplicate_entities(entities):
    """Merge entities with same normalized name"""
    merged = {}
    
    for ent in entities:
        # Normalize name (lowercase, remove extra spaces)
        normalized = normalize(ent['name'])
        
        if normalized not in merged:
            merged[normalized] = ent
        else:
            # Merge metadata
            existing = merged[normalized]
            existing['aliases'].append(ent['name'])
            existing['confidence'] = max(existing['confidence'], ent['confidence'])
    
    return list(merged.values())
```

### B. Relationship Validation (Optional but Recommended)
**Problem**: Co-occurrence ≠ semantic relationship
**Solution**: 
- Sample 100 relationships manually
- Calculate precision rate
- Adjust inference rules based on findings

### C. Formula Parsing (Advanced)
**Problem**: Formulas extracted as text, not parsed
**Solution**:
- Parse LaTeX/math notation
- Extract variables and functions separately
- Create sub-nodes for formula components

---

## 6. Recommended Next Steps

### Immediate (Do Now)
1. ✅ Review extracted entities and formulas
2. ✅ Run entity deduplication
3. ⏳ Load basic graph to Neo4j (Approach A)
4. ⏳ Test basic queries

### Short-term (Next Week)
5. ⏳ Implement relationship inference (Approach B)
6. ⏳ Load relationships to graph
7. ⏳ Validate sample relationships manually

### Long-term (Optional)
8. ⏳ LLM relationship validation for top entities
9. ⏳ Formula component parsing
10. ⏳ Graph visualization and exploration

---

## 7. Files to Create

```bash
# Graph loading scripts
load_basic_graph.py              # Approach A: Basic loading
load_relationships.py            # Approach B: Add relationships
graph_schema.cypher              # Neo4j schema definition
validate_relationships.py        # Manual validation tool

# Query examples
graph_queries.cypher             # Sample queries for exploration
graph_analysis.py                # Graph statistics and metrics
```

---

## Recommendation

**Start with Approach B (Smart Loading)**:

1. **Load entities + formulas as nodes** (5 min)
2. **Infer co-occurrence relationships** (30 min)
3. **Validate 50 relationships manually** (1 hour)
4. **Adjust inference rules if needed** (30 min)
5. **Load validated relationships** (10 min)

**Total time**: ~2-3 hours for a functional graph database

**Why not Approach C?**
- LLM validation is slow and expensive
- Co-occurrence gives 60-70% accuracy initially
- Can always add LLM validation later for specific high-value relationships

---

**Ready to proceed with Neo4j loading?** I can create the loading scripts and schema definitions next.

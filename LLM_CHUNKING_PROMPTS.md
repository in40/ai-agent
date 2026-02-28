# LLM Prompts for Smart Chunking

## Overview

The Graph RAG system uses **Qwen3.5-35B** (262k context) for intelligent document chunking. There are **two scenarios** with different prompts:

---

## 1. Single-Call Processing (97% of documents)

**Used when:** Document < 800k chars (~200k tokens)

### Prompt Structure

```python
single_prompt = f"""{custom_prompt}

## Document: {file_info['original_filename']}

{document_content}

## Output Format
Return JSON with these fields:
{{
  "document": "document identifier (e.g., GOST_R_XXXXX-YYYY)",
  "total_chunks": integer,
  "chunks": [
    {{
      "chunk_id": 1,
      "section": "section number or appendix_X",
      "title": "descriptive title in language of document",
      "chunk_type": "one of: header_and_scope | references_and_definitions | formula_with_context | testing_procedure | appendix_example",
      "contains_formula": boolean,
      "contains_table": boolean,
      "formula_id": "1,2,3... or null",
      "formula_reference": "referenced formula number or null",
      "content": "chunk text here",
      "token_count": integer (200-450 tokens per chunk)
    }}
  ],
  "document_summary": "2-3 sentences summarizing document content for graph context",
  "key_entities": ["important entities from document for graph context"],
  "embedding_recommendations": {{
    "model": "text-embedding-3-large or equivalent multilingual",
    "chunk_size_target": "200-450 tokens",
    "overlap_strategy": "Apply overlaps ONLY at procedural boundaries to preserve algorithmic continuity",
    "metadata_indexing": "Index section, chunk_type, contains_formula, document_summary fields for hybrid search"
  }}
}}

## Chunking Guidelines
- Target 200-450 tokens per chunk
- Preserve semantic units (formulas, tables, procedures)
- Include section headers in chunk content
- Extract entities: GOST/ISO standards, organizations, technologies, dates, concepts
"""
```

**Location:** `backend/services/rag/app.py` lines ~1535-1575

---

## 2. Sectioned Processing (Large documents > 800k chars)

**Used when:** Document > 800k chars (~200k tokens)

### Section Prompt Structure

```python
section_prompt = f"""{custom_prompt}

{context_header}  # Only for sections 2+

## Document: {file_info['original_filename']}
## Section {section_idx + 1} of {len(sections)}

{section}

## Output Format
Return JSON with these fields:
{{
  "document": "document identifier",
  "total_chunks": integer,
  "chunks": [
    {{
      "chunk_id": 1,
      "section": "section number",
      "title": "descriptive title",
      "chunk_type": "chunk type",
      "content": "chunk text here",
      "token_count": integer
    }}
  ],
  "document_summary": "2-3 sentences summarizing what this section covers",
  "key_entities": ["important entities from this section for graph context"],
  "embedding_recommendations": {{
    "model": "text-embedding-3-large or equivalent multilingual",
    "chunk_size_target": "200-450 tokens",
    "metadata_indexing": "Index section, chunk_type, contains_formula fields"
  }}
}}
"""
```

### Context Header (Sections 2+)

```python
context_header = f"""
## Context from Previous Section

**Summary:** {previous_summary}

**Key Entities:** {', '.join(previous_entities)}

Continue chunking with this context in mind. Maintain semantic continuity with adjacent sections.
"""
```

**Location:** `backend/services/rag/app.py` lines ~1475-1510

---

## 3. Base Prompt (DEFAULT_SMART_CHUNKING_PROMPT)

**Source:** `backend/services/rag/smart_ingestion_enhanced.py` lines ~62-180

This is the **custom_prompt** that gets prepended to all chunking requests.

### Full Base Prompt

```
# ROLE
You are an expert document engineer specializing in semantic chunking of technical standards (GOST, ISO, IEC, RFC, etc.) for vector database ingestion. Your task is to split the provided document into search-optimized chunks while preserving semantic integrity.

## CORE PRINCIPLES
1. PRESERVE SEMANTIC UNITS: Never split complete concepts (formulas with context, tables, procedural steps, definitions)
2. TARGET SIZE: 200-450 tokens per chunk (prioritize semantic integrity over exact size)
3. MINIMAL OVERLAP: Apply overlap ONLY at procedural boundaries where step N output becomes step N+1 input (max 50 tokens). Zero overlap elsewhere.
4. CONTEXT ANCHORING: Always include section headers/subheaders at chunk start
5. FORMULA PRESERVATION: Keep all formulas WITH their explanatory context and variable definitions
6. TABLE INTEGRITY: Never split tables – keep entire table + caption in single chunk

## CHUNKING RULES (Priority Order)

### ✅ MUST PRESERVE TOGETHER
- Formulas + surrounding explanatory text (min. 2 sentences before/after)
- Complete tables (header + all rows + footnote)
- Algorithmic/procedural sequences (e.g., "Step 1 → Step 2 → Step 3")
- Definition + scope sentences (term + "— " explanation)
- Example + its numerical result/calculation
- Cross-referenced clauses (e.g., "as specified in 5.2.4" → include 5.2.4 context if critical)

### ⚠️ OVERLAP ONLY AT THESE BOUNDARIES
Apply 30-50 token overlap ONLY when:
- Procedural step output directly feeds next step input (e.g., "morphing produces X" → "X is used in selection")
- Observation → formula transition ("min(h) ≤ 3σ" → "evaluate using formula (2)")
- Generation forecasting → numerical example ("exponential decrease" → "Appendix A example")

DO NOT overlap:
- Discrete trust levels/scenarios
- Structural requirement categories
- Appendices (keep self-contained)
- Reference sections (normative references, notations)

### 🚫 NEVER SPLIT
- Mathematical expressions across lines
- "where:" variable definitions from their formula
- Critical constraint ranges (e.g., "n - √n < h < n + √n")
- Multi-sentence definitions
- Complete attack scenarios/methodologies

## METADATA REQUIREMENTS
For each chunk, generate structured metadata:
{
  "chunk_id": integer,
  "section": "X.Y.Z or appendix_X",
  "title": "Descriptive title in language of document",
  "chunk_type": "one of: header_and_scope | references_and_definitions | reference_table | trust_level | structural_requirements | testing_procedure | formula_with_context | security_procedure | appendix_example",
  "contains_formula": boolean,
  "contains_table": boolean,
  "formula_id": "1,2,3... or null",
  "formula_reference": "referenced formula number or null",
  "trust_level": "full | partial_zero | null",
  "testing_scenario": "small_db | medium_db | low_trust | null",
  "overlap_source": "chunk_X_end or null",
  "overlap_tokens": integer,
  "token_count": integer,
  "content": "chunk text with overlaps PREPENDED (not appended to previous chunk)",
  "entities": [/* optional: array of extracted entities for knowledge graph */]
}

## ENTITY EXTRACTION RULES (for Knowledge Graph)
For each chunk, extract key entities to build a knowledge graph:
1. **STANDARDS**: GOST, ISO, IEC, RFC standards (e.g., "GOST R 34.10-2012", "ISO 27001")
2. **ORGANIZATIONS**: Companies, government bodies, agencies (e.g., "FSB Russia", "ISO/IEC")
3. **TECHNOLOGIES**: Technical terms, algorithms, protocols (e.g., "elliptic curve cryptography", "SHA-256")
4. **LOCATIONS**: Geographical entities, countries, regions (e.g., "Russian Federation", "Moscow")
5. **CONCEPTS**: Key domain concepts (e.g., "digital signature", "hash function", "encryption key")
6. **PERSONS**: People mentioned (rare in technical docs)

For each entity, provide:
{
  "name": "exact entity name as appears in text",
  "type": "STANDARD | ORGANIZATION | TECHNOLOGY | LOCATION | CONCEPT | PERSON",
  "relevance": "high | medium | low"  // high if central to chunk, low if mentioned in passing
}

Example entities array:
"entities": [
  {"name": "GOST R 34.10-2012", "type": "STANDARD", "relevance": "high"},
  {"name": "elliptic curve", "type": "TECHNOLOGY", "relevance": "high"},
  {"name": "Russian Federation", "type": "LOCATION", "relevance": "medium"},
  {"name": "digital signature", "type": "CONCEPT", "relevance": "high"}
]

## OUTPUT FORMAT
Return ONLY valid JSON matching this schema:
{
  "document": "extracted document identifier (e.g., GOST_R_XXXXX-YYYY)",
  "total_chunks": integer,
  "total_entities": integer,  // count of all extracted entities
  "entity_types": {  // count by type
    "STANDARD": integer,
    "ORGANIZATION": integer,
    "TECHNOLOGY": integer,
    "LOCATION": integer,
    "CONCEPT": integer,
    "PERSON": integer
  },
  "overlap_strategy": "targeted_procedural_only",
  "chunks": [ /* array of chunk objects per metadata requirements */ ],
  "embedding_recommendations": {
    "model": "text-embedding-3-large or equivalent multilingual",
    "chunk_size_target": "200-450 tokens",
    "overlap_strategy": "Apply overlaps ONLY at procedural boundaries to preserve algorithmic continuity",
    "metadata_indexing": "Index section, chunk_type, contains_formula, entities fields for hybrid search"
  }
}

## SPECIAL HANDLING FOR RUSSIAN TECHNICAL STANDARDS
- Preserve «ёлочки» quotes («Свой», «Чужой») – critical semantic markers
- Keep ГОСТ Р XXXXX references intact with year
- Maintain mathematical notation: σ(h), min(h), ρ(h), E(.), σ(.)
- Preserve footnote markers and "Примечание — " sections with parent content

## PROCESSING INSTRUCTIONS
1. First pass: Identify natural semantic boundaries (section breaks, formula clusters, procedural sequences)
2. Second pass: Apply overlap rules ONLY where procedural continuity requires it
3. Third pass: Generate metadata based on content analysis (detect formulas, tables, trust levels)
4. Final validation: Ensure no formula/table split; verify overlap only at 2-3 procedural boundaries max

## CRITICAL CONSTRAINT
If document contains morphing/generation procedures (e.g., "поколение потомков"), apply overlap between generation steps to preserve causal chain. For all other boundaries: ZERO overlap.

---
TEXT TO CHUNK PROVIDED
```

---

## 4. Entity Extraction Prompt (Per-Chunk)

**Used in:** Hybrid mode for extracting entities from each chunk

**Source:** `backend/services/rag/smart_ingestion_enhanced.py` lines ~925-945

```python
entity_extraction_prompt = """You are an expert entity extractor for Russian technical standards (GOST, ISO, IEC, RFC).
Extract all named entities from the text and return them as JSON.

## Entity Types to Extract:
- STANDARD: GOST, ISO, IEC, RFC standards (e.g., "ГОСТ Р 34.10-2012", "ISO 27001")
- ORGANIZATION: Companies, agencies, institutions (e.g., "ФСБ России", "Росстандарт")
- TECHNOLOGY: Technical terms, algorithms, technologies (e.g., "электронная подпись", "шифрование")
- LOCATION: Geographic locations (e.g., "Москва", "Россия")
- DATE: Dates and time periods (e.g., "2024 год", "1 января 2025")
- PERSON: People names (e.g., "Иванов И.И.")
- CONCEPT: Important concepts and terms (e.g., "информационная безопасность", "криптографическая защита")

## Output Format:
Return ONLY valid JSON:
{
  "entities": [
    {"name": "entity name", "type": "STANDARD|ORGANIZATION|TECHNOLOGY|LOCATION|DATE|PERSON|CONCEPT", "confidence": 0.9}
  ]
}

## Text to Analyze:
{content}
"""
```

---

## Complete Prompt Flow

```
User Uploads Document
    ↓
[Load PDF Text] → document_content
    ↓
[Check Size]
    ├─ < 800k chars → Single-call prompt
    │   └─ prompt = base_prompt + document_header + document_content + output_format + guidelines
    │
    └─ > 800k chars → Section into 700k char sections
        └─ For each section:
            ├─ Section 1: base_prompt + section_header + section_content + output_format
            └─ Sections 2+: base_prompt + context_header + section_header + section_content + output_format
    ↓
[LLM Invocation] → Qwen3.5-35B @ http://192.168.51.237:1234/v1
    ↓
[Parse JSON Response] → Using parse_json_robust()
    ↓
[Extract Chunks] → List of chunk dictionaries
    ↓
[Entity Extraction] → For each chunk, call LLM with entity_extraction_prompt
    ↓
[Store in Vector DB + Neo4j]
```

---

## Example: Actual Prompt Sent to LLM

For a document like `gost-r-34.10-2012.pdf`:

```
# ROLE
You are an expert document engineer specializing in semantic chunking of technical standards...
[full base prompt continues]

## Document: gost-r-34.10-2012.pdf

ГОСТ Р 34.10-2012

Информационная технология. Криптографическая защита информации.
Процессы формирования и проверки электронной цифровой подписи

[... full document text continues ...]

## Output Format
Return JSON with these fields:
{
  "document": "GOST_R_34.10-2012",
  "total_chunks": integer,
  "chunks": [...],
  "document_summary": "...",
  "key_entities": [...],
  "embedding_recommendations": {...}
}

## Chunking Guidelines
- Target 200-450 tokens per chunk
- Preserve semantic units (formulas, tables, procedures)
- Include section headers in chunk content
- Extract entities: GOST/ISO standards, organizations, technologies, dates, concepts
```

---

## Key Prompt Engineering Decisions

| Decision | Rationale |
|----------|-----------|
| **800k char threshold** | Leaves ~20% of 262k context for prompt + output overhead |
| **700k char sections** | Ensures room for context header + output in sectioned processing |
| **Structured JSON output** | Enables reliable parsing and validation |
| **Entity types predefined** | Ensures consistent extraction across documents |
| **Overlap rules explicit** | Prevents LLM from over-using overlap (common failure mode) |
| **Russian standard specifics** | Handles «ёлочки» quotes, ГОСТ references, Cyrillic math notation |

---

## Files Referenced

| File | Lines | Content |
|------|-------|---------|
| `backend/services/rag/smart_ingestion_enhanced.py` | 62-180 | `DEFAULT_SMART_CHUNKING_PROMPT` |
| `backend/services/rag/app.py` | 1535-1575 | Single-call prompt assembly |
| `backend/services/rag/app.py` | 1475-1510 | Sectioned prompt assembly |
| `backend/services/rag/smart_ingestion_enhanced.py` | 925-945 | Entity extraction prompt |

---

**Last Updated:** February 27, 2026  
**Model:** Qwen3.5-35B-Thinking @ iq4_nl  
**Context Window:** 262k tokens

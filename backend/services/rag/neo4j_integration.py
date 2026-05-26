"""
Neo4j Graph Database Integration for Hybrid RAG Ingestion
Handles storage of document chunks and relationships in Neo4j Graph DB
"""
import os
import json
import re
import logging
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import pattern registry for dynamic entity extraction
from backend.services.rag.pattern_registry import pattern_registry, PatternRegistry

logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'neo4j')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

# SSH Tunnel configuration
NEO4J_SSH_HOST = os.getenv('NEO4J_SSH_HOST', '192.168.51.187')
NEO4J_SSH_USER = os.getenv('NEO4J_SSH_USER', 'sorokin')
NEO4J_SSH_KEY = os.getenv('NEO4J_SSH_KEY', '~/.ssh/id_ed25519_graphrag')
NEO4J_SSH_TUNNEL_PORT = int(os.getenv('NEO4J_SSH_TUNNEL_PORT', 7687))


def ensure_ssh_tunnel():
    """Ensure SSH tunnel to Neo4j server is established"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', f'ssh.*-L.*{NEO4J_SSH_TUNNEL_PORT}.*{NEO4J_SSH_HOST}'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            logger.info("SSH tunnel to Neo4j already established")
            return True
        
        ssh_key = os.path.expanduser(NEO4J_SSH_KEY)
        logger.info(f"Establishing SSH tunnel to {NEO4J_SSH_HOST}:{NEO4J_SSH_TUNNEL_PORT}...")
        subprocess.Popen([
            'ssh', '-N', '-f', '-i', ssh_key,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-L', f'{NEO4J_SSH_TUNNEL_PORT}:localhost:{NEO4J_SSH_TUNNEL_PORT}',
            f'{NEO4J_SSH_USER}@{NEO4J_SSH_HOST}'
        ])
        
        import time
        time.sleep(2)
        logger.info("SSH tunnel established successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to establish SSH tunnel: {e}")
        return False


class Neo4jIntegration:
    """Integration with Neo4j Graph Database for hybrid RAG storage"""
    
    def __init__(self, llm=None):
        """
        Initialize Neo4j integration.
        
        Args:
            llm: Optional LLM instance for advanced entity extraction
        """
        self.driver = None
        self.connected = False
        self.last_error = None
        self.llm = llm
        self.pattern_registry = pattern_registry
        self.llm_extraction_failed = False  # Track if LLM failed and we fell back to regex
    
    def connect(self) -> bool:
        """Establish connection to Neo4j"""
        try:
            if NEO4J_SSH_HOST:
                ensure_ssh_tunnel()
            
            from neo4j import GraphDatabase
            
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                database=NEO4J_DATABASE,
                connection_timeout=30
            )
            
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            self.connected = True
            self.last_error = None
            logger.info(f"Connected to Neo4j at {NEO4J_URI}")
            return True
            
        except ImportError:
            self.last_error = "Neo4j driver not installed. Install with: pip install neo4j"
            logger.warning(self.last_error)
            self.connected = False
            return False
        except Exception as e:
            self.last_error = f"Failed to connect to Neo4j: {str(e)}"
            logger.error(self.last_error)
            self.connected = False
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.connected = False
    
    def clear_all(self) -> bool:
        """Clear all data from Neo4j database"""
        if not self.connected:
            return False
        
        try:
            with self.driver.session() as session:
                # Delete all nodes and relationships
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("Neo4j database cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Neo4j: {str(e)}")
            return False
    
    def store_document(self, doc_id: str, filename: str, metadata: Dict[str, Any]) -> bool:
        """Store document metadata in Neo4j"""
        if not self.connected:
            return False

        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (d:Document {doc_id: $doc_id})
                    SET d.filename = $filename,
                        d.uploaded_at = $uploaded_at,
                        d.format = $format,
                        d.job_id = $job_id,
                        d.extraction_method = $extraction_method,
                        d.extraction_time = $extraction_time,
                        d.text_length = $text_length,
                        d.encoding_was_fixed = $encoding_was_fixed
                """, {
                    'doc_id': doc_id,
                    'filename': filename,
                    'uploaded_at': metadata.get('uploaded_at', datetime.utcnow().isoformat()),
                    'format': metadata.get('format', 'pdf'),
                    'job_id': metadata.get('job_id', ''),
                    'extraction_method': metadata.get('extraction_method', 'unknown'),
                    'extraction_time': metadata.get('extraction_time_seconds', 0),
                    'text_length': metadata.get('text_length', 0),
                    'encoding_was_fixed': metadata.get('encoding_was_fixed', False)
                })
            return True
        except Exception as e:
            logger.error(f"Error storing document in Neo4j: {e}")
            return False

    def store_chunk(self, chunk_id: str, doc_id: str, chunk_data: Dict[str, Any]) -> bool:
        """Store a document chunk in Neo4j with relationships"""
        if not self.connected:
            return False
            
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (d:Document {doc_id: $doc_id})
                    CREATE (c:Chunk {
                        chunk_id: $chunk_id,
                        content: $content,
                        section: $section,
                        title: $title,
                        chunk_type: $chunk_type,
                        chunk_index: $chunk_index
                    })
                    CREATE (d)-[:HAS_CHUNK]->(c)
                """, {
                    'chunk_id': chunk_id,
                    'doc_id': doc_id,
                    'content': chunk_data.get('content', ''),
                    'section': chunk_data.get('section', ''),
                    'title': chunk_data.get('title', ''),
                    'chunk_type': chunk_data.get('chunk_type', ''),
                    'chunk_index': chunk_data.get('chunk_id', 0)
                })
            return True
        except Exception as e:
            logger.error(f"Error storing chunk in Neo4j: {e}")
            return False
    
    def store_chunks_batch(self, doc_id: str, chunks: List[Dict[str, Any]]) -> int:
        """Store multiple chunks for a document"""
        if not self.connected:
            return 0
            
        stored_count = 0
        for chunk in chunks:
            chunk_id = f"{doc_id}_chunk_{chunk.get('chunk_id', 0)}"
            if self.store_chunk(chunk_id, doc_id, chunk):
                stored_count += 1
                
        return stored_count
    
    def create_knowledge_graph(self, chunks: List[Dict[str, Any]], use_llm_extraction: bool = False, use_regex_entities: bool = True) -> Dict[str, int]:
        """
        Create knowledge graph from chunks by extracting entities and storing chunk UUID references.
        
        Args:
            chunks: List of chunk data with content and metadata
            use_llm_extraction: If True, use LLM for first-time extraction + pattern discovery
            use_regex_entities: If True, include regex-extracted entities (noisier but more coverage)
        
        Returns:
            Stats dict with entity and chunk reference counts
        """
        if not self.connected:
            return {'entities': 0, 'chunk_refs': 0}

        stats = {'entities': 0, 'chunk_refs': 0, 'relationships': 0}

        try:
            with self.driver.session() as session:
               for chunk in chunks:
                    content = chunk.get('content', '')
                    # Try multiple locations for chunk UUID/ID
                    chunk_uuid = (chunk.get('metadata', {}).get('chunk_uuid', '') or
                                 chunk.get('chunk_id', '') or
                                 chunk.get('metadata', {}).get('chunk_id', ''))

                    # Skip if no chunk UUID (old ingestion without UUIDs)
                    if not chunk_uuid:
                        logger.warning(f"Chunk missing chunk_uuid/chunk_id, skipping graph storage")
                        continue

                    # Extract entities using hybrid approach
                    entities = self._extract_entities(
                        content, 
                        use_llm=use_llm_extraction,
                        doc_metadata=chunk.get('metadata', {}),
                        use_regex_entities=use_regex_entities
                    )

                    # Extract entities from chunk
                    chunk_entities = []
                    for entity in entities:
                        if not isinstance(entity, dict):
                            continue
                        
                        entity_name = entity.get('name', '')
                        entity_type = entity.get('type', 'CONCEPT')
                        relevance = entity.get('relevance', 'medium')

                        if not entity_name:
                            continue

                        # Store chunk-entity relationship using MENTIONS relationship
                        session.run("""
                            MERGE (c:Chunk {chunk_id: $chunk_uuid})
                            MERGE (e:Entity {name: $name, type: $type})
                            ON CREATE SET e.created_at = datetime(),
                                e.relevance = $relevance
                            ON MATCH SET e.updated_at = datetime()
                            MERGE (c)-[:MENTIONS]->(e)
                        """, {
                            'name': entity_name,
                            'type': entity_type,
                            'relevance': relevance,
                            'chunk_uuid': chunk_uuid
                        })
                        chunk_entities.append({
                            'name': entity_name,
                            'type': entity_type
                        })
                        stats['entities'] += 1
                        stats['chunk_refs'] += 1

                    # Extract and store entity-to-entity relationships
                    relationships = self._extract_relationships(chunk_entities, content)
                    for rel in relationships:
                        session.run("""
                            MATCH (e1:Entity {name: $from_name, type: $from_type})
                            MATCH (e2:Entity {name: $to_name, type: $to_type})
                            MERGE (e1)-[r:RELATES_TO]->(e2)
                            ON CREATE SET r.relationship_type = $rel_type,
                                r.created_at = datetime()
                        """, {
                            'from_name': rel['from'],
                            'from_type': rel['from_type'],
                            'to_name': rel['to'],
                            'to_type': rel['to_type'],
                            'rel_type': rel['type']
                        })
                        stats['relationships'] += 1

                    # Co-occurrence-based relationships: entities that share a chunk are related
                    if len(chunk_entities) >= 2:
                        session.run("""
                            MATCH (c:Chunk {chunk_id: $chunk_uuid})-[r:MENTIONS]->(e:Entity)
                            WITH c, collect(e) as entities
                            UNWIND entities as e1
                            UNWIND entities as e2
                            WITH e1, e2 WHERE e1.name < e2.name
                            MERGE (e1)-[rel:RELATES_TO]-(e2)
                            ON CREATE SET rel.relationship_type = 'CO_OCCURS',
                                rel.chunk_id = $chunk_uuid,
                                rel.created_at = datetime(),
                                rel.co_occurrence_count = 1
                            ON MATCH SET rel.co_occurrence_count = COALESCE(rel.co_occurrence_count, 0) + 1
                        """, {'chunk_uuid': chunk_uuid})
                        # Count added relationships: n entities = n*(n-1)/2 pairs
                        n = len(chunk_entities)
                        stats['relationships'] += n * (n - 1) // 2

        except Exception as e:
            logger.error(f"Error creating knowledge graph: {e}")

        return stats
    
    def _extract_relationships(self, entities: List[Dict], text: str) -> List[Dict]:
        """
        Extract relationships between entities based on their types and co-occurrence.
        
        Args:
            entities: List of extracted entities with name and type
            text: Original chunk text for context
            
        Returns:
            List of relationships with from, to, type, from_type, to_type
        """
        relationships = []
        entity_map = {e['name']: e['type'] for e in entities}
        
        # Relationship rules for crypto standard documents
        # Standard references other standards
        std_entities = [e for e in entities if e['type'] == 'STANDARD']
        for std in std_entities:
            for other in entities:
                if other['name'] != std['name'] and other['type'] == 'STANDARD':
                    relationships.append({
                        'from': std['name'],
                        'from_type': 'STANDARD',
                        'to': other['name'],
                        'to_type': 'STANDARD',
                        'type': 'REFERENCES'
                    })
        
        # Organization issued standards
        org_entities = [e for e in entities if e['type'] == 'ORGANIZATION']
        for org in org_entities:
            for std in std_entities:
                relationships.append({
                    'from': org['name'],
                    'from_type': 'ORGANIZATION',
                    'to': std['name'],
                    'to_type': 'STANDARD',
                    'type': 'ISSUED'
                })
        
        # Parameters belong to parameter sets
        param_entities = [e for e in entities if e['type'] in ['PARAMETER', 'TECHNICAL_TERM']]
        param_set_entities = [e for e in entities if e['type'] == 'PARAMETER_SET']
        for param in param_entities:
            for pset in param_set_entities:
                # Check if parameter name appears in parameter set context
                relationships.append({
                    'from': param['name'],
                    'from_type': param['type'],
                    'to': pset['name'],
                    'to_type': 'PARAMETER_SET',
                    'type': 'PART_OF'
                })
        
        # Technical terms defined in document sections
        term_entities = [e for e in entities if e['type'] == 'TECHNICAL_TERM']
        section_entities = [e for e in entities if e['type'] == 'DOCUMENT_SECTION']
        for term in term_entities:
            for section in section_entities:
                relationships.append({
                    'from': term['name'],
                    'from_type': 'TECHNICAL_TERM',
                    'to': section['name'],
                    'to_type': 'DOCUMENT_SECTION',
                    'type': 'DEFINED_IN'
                })
        
        # Remove duplicate relationships
        seen = set()
        unique_relationships = []
        for rel in relationships:
            key = (rel['from'], rel['to'], rel['type'])
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        return unique_relationships
    
    def _extract_entities_regex(self, text: str) -> List[Dict]:
        """
        Fallback regex-based entity extraction if LLM fails.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities using regex patterns
        """
        entities = []
        
        # Extract GOST standards
        gost_pattern = r'(ГОСТ|GOST)\s*[Р]?\s*(\d+\.\d+)'
        for match in re.finditer(gost_pattern, text, re.IGNORECASE):
            prefix = match.group(1).upper()
            normalized_prefix = 'ГОСТ' if prefix in ['ГОСТ', 'GOST'] else prefix
            entities.append({
                'name': f'{normalized_prefix} {match.group(2)}',
                'type': 'STANDARD',
                'relevance': 'high'
            })
        
        # Extract Technical Committees (ТК XX)
        tk_pattern = r'(ТК|Технический комитет)\s*(\d+)'
        for match in re.finditer(tk_pattern, text, re.IGNORECASE):
            prefix = match.group(1).upper()
            if prefix == 'ТК':
                name = f'ТК {match.group(2)}'
                synonyms = [f'Технический комитет {match.group(2)}']
            else:
                name = f'Технический комитет {match.group(2)}'
                synonyms = [f'ТК {match.group(2)}']
            
            entities.append({
                'name': name,
                'type': 'ORGANIZATION',
                'synonyms': synonyms,
                'relevance': 'medium'
            })
        
        # Extract other government agencies
        agencies = ['ФСТЭК', 'ФСБ', 'Минцифры', 'Росстандарт']
        for agency in agencies:
            if agency in text:
                entities.append({
                    'name': agency,
                    'type': 'ORGANIZATION',
                    'relevance': 'medium'
                })
        
        # Extract technical terms (simple patterns)
        tech_terms = ['эллиптическая кривая', 'хеширование', 'электронная подпись', 
                     'криптография', 'открытый ключ', 'закрытый ключ']
        for term in tech_terms:
            if term in text:
                entities.append({
                    'name': term,
                    'type': 'TECHNICAL_TERM',
                    'relevance': 'medium'
                })
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for e in entities:
            key = (e['name'], e['type'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(e)
        
        logger.info(f"Regex fallback extracted {len(unique_entities)} entities")
        return unique_entities
    
    def _extract_entities(self, text: str, use_llm: bool = False, 
                         doc_metadata: Dict[str, Any] = None,
                         use_regex_entities: bool = True) -> List[Dict]:
        """
        Extract entities from text using hybrid approach.
        
        Priority:
        1. Pre-extracted LLM entities (if available in metadata)
        2. Dynamic regex patterns from registry (fast, optional)
        3. LLM extraction + pattern discovery (for new documents)
        
        Args:
            text: Text to extract entities from
            use_llm: If True, run LLM extraction for new documents
            doc_metadata: Document metadata (may contain pre-extracted entities)
            use_regex_entities: If True, include regex-extracted entities
            
        Returns:
            List of extracted entity dicts
        """
        entities = []
        
        # 1. Check if this document already has LLM-extracted entities
        if doc_metadata and doc_metadata.get('entities'):
            logger.debug(f"Using pre-extracted LLM entities for this document")
            return doc_metadata['entities']
        
        # 2. Use dynamic regex patterns from registry (fast, optional)
        if use_regex_entities:
            registry_entities = self.pattern_registry.extract_entities_from_text(text)
            entities.extend(registry_entities)
        
        # 3. If LLM extraction enabled and this is a new document
        if use_llm:
            logger.info("Running LLM entity extraction for new document")
            llm_entities = self._extract_entities_llm(text)
            
            if llm_entities:
                # 4. Discover new patterns from LLM results
                new_patterns = self._discover_patterns_from_llm(llm_entities, text)
                
                # 5. Add discovered patterns to registry
                for pattern in new_patterns:
                    try:
                        self.pattern_registry.add_pattern(
                            category=pattern['category'],
                            pattern=pattern['regex_pattern'],
                            example=pattern['example'],
                            description=pattern['description']
                        )
                    except Exception as e:
                        logger.warning(f"Failed to add pattern: {e}")
                
                # Add LLM entities (avoid duplicates)
                existing_names = {(e['name'], e['type']) for e in entities}
                for entity in llm_entities:
                    key = (entity.get('name', ''), entity.get('type', 'CONCEPT'))
                    if key not in existing_names:
                        entities.append(entity)
                        existing_names.add(key)
        
        return entities
    
    def _extract_entities_llm(self, text: str) -> List[Dict]:
        """
        Use LLM to extract comprehensive entities.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entity dicts
        """
        if not self.llm:
            logger.warning("LLM not available for entity extraction")
            return []
        
        # Reset flag per-chunk so one failure doesn't mark the whole job
        self.llm_extraction_failed = False
        
        # Use full text for better entity extraction (up to 5000 chars)
        text_snippet = text[:5000]
        
        prompt = f"""Ты — ИИ для извлечения сущностей. Извлеки ВСЕ сущности из этого русского технического документа.

ТЕКСТ ДОКУМЕНТА:
{text_snippet}

ИЗВЛЕКИ СУЩНОСТИ ЭТИХ ТИПОВ:
1. STANDARD — Государственные стандарты (ГОСТ, ISO, П, etc.)
2. ORGANIZATION — Комитеты, агентства (ТК, ФСТЭК, Росстандарт, etc.)
3. ABBREVIATION — Аббревиатуры с полными названиями
4. TECHNICAL_TERM — Технические термины (эллиптическая кривая, хеширование, etc.)
5. CONCEPT — Важные понятия

‼️ КРИТИЧЕСКИ ВАЖНО — НЕ ХАЛЛЮЦИНИРУЙ:
- Извлекай ТОЛЬКО те сущности, которые ЯВНО УПОМИНАЮТСЯ в тексте выше
- НЕ придумывай стандарты! Если в тексте ГОСТ 34.10-2012, не извлекай ГОСТ 34.11-2012, ГОСТ 34.12-2012 и т.д.
- НЕ экстраполируй номера стандартов! Каждый стандарт должен быть явно указан в тексте
- Если видишь "ГОСТ Р 34.10-2012", не извлекай "ГОСТ Р 34.11-2012" если его нет в тексте
- НЕ генерируй списки стандартов по шаблону — только то, что реально есть в документе
- Если видишь один стандарт, не делай вывод что есть другие с похожими номерами

‼️ ЧЕГО НЕ НАДО ИЗВЛЕКАТЬ:
- НЕ извлекай отдельные символы: (, ), ,, -, ., /, _, «, » — это пунктуация, не сущности
- НЕ извлекай одиночные буквы: A, B, C, а, б, в, г — они не являются сущностями
- НЕ извлекай HEX-последовательности: f0, f038, f9000, 0x01 и любые строки из hex-цифр (0-9a-f). Это фрагменты криптографических ключей, а не сущности
- НЕ извлекай числовые последовательности: 12345, 0, 1, 2, 3 — это цифры, не сущности
- НЕ извлекай части hex-значений: если в тексте "K_ENC = 239aebeef9", не извлекай "f9", "239", "aebe"
- НЕ извлекай обрывки слов: "информ", "сес", "аут" — это неполные слова
- НЕ классифицируй hex-значения как ORGANIZATION! Если что-то похоже на hex-ключ, это не организация

✅ ПРИМЕРЫ ПРАВИЛЬНЫХ СУЩНОСТЕЙ:
- STANDARD: "ГОСТ Р 34.10-2012", "Р 50.1.113—2016"
- ORGANIZATION: "ТК 26", "ФСТЭК", "Росстандарт", "GlobalPlatform"
- ABBREVIATION: "ЭП" (электронная подпись), "КДБ", "СКЗИ"
- TECHNICAL_TERM: "сессионный ключ", "имитовставка", "эллиптическая кривая"
- CONCEPT: "электронная подпись", "шифрование", "домен безопасности"

❌ ПРИМЕРЫ ЧЕГО НЕ ИЗВЛЕКАТЬ:
- "f0", "f038", "f9000", "0x80" — hex-фрагменты ключей
- "(", ")", ",", "-", "." — пунктуация
- "A", "B", "C", "а", "б", "в" — одиночные буквы
- "0", "1", "2", "3" — цифры
- "информ", "сес" — обрывки слов

‼️ ОБЯЗАТЕЛЬНОЕ ТРЕБОВАНИЕ — ПОЛЕ original_text:
- Для КАЖДОЙ сущности укажи поле 'original_text' с ТОЧНЫМ текстом из документа
- Это должен быть фрагмент текста, где встречается эта сущность (5-15 слов)
- Если не можешь найти точный текст в документе — НЕ включай эту сущность
- Пример: {{ "name": "ГОСТ 34.10", "original_text": "...алгоритмы по ГОСТ Р 34.10-2012 для..." }}

ВАЖНО:
- Извлеки КАЖДУЮ найденную сущность (но только если она есть в тексте!)
- Будь ПОЛНЫМ — не пропускай ничего
- Если находишь аббревиатуры, укажи полные названия в поле 'synonyms'
- Верни минимум 5-10 сущностей, если они есть в тексте

ФОРМАТ ОТВЕТА — ТОЛЬКО JSON массив (без другого текста):
[
    {{
        "name": "ГОСТ 34.10",
        "type": "STANDARD",
        "original_text": "...алгоритмы по ГОСТ Р 34.10-2012 для формирования...",
        "relevance": "high"
    }},
    {{
        "name": "ТК 26",
        "type": "ORGANIZATION",
        "original_text": "...подкомитетом № 1 Технического комитета ТК 26 «Криптографическая...",
        "relevance": "medium"
    }},
    {{
        "name": "эллиптическая кривая",
        "type": "TECHNICAL_TERM",
        "original_text": "...параметры эллиптических кривых для криптографических алгоритмов...",
        "relevance": "high"
    }},
    {{
        "name": "электронная подпись",
        "type": "CONCEPT",
        "original_text": "...схемы электронной подписи в соответствии с ГОСТ Р 34.10...",
        "relevance": "medium"
    }}
]

Если сущности НЕ найдены, верни пустой массив: []

ТЕПЕРЬ ИЗВЛЕКИ СУЩНОСТИ ИЗ ДОКУМЕНТА ВЫШЕ:"""
        try:
            response = self.llm.invoke(prompt)
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Handle empty responses - this is VALID when text has no entities (e.g., TOC)
            if not response_content or response_content.strip() == '[]':
                logger.info(f"LLM found no entities in text snippet of {len(text_snippet)} chars (expected for TOC/formatting chunks)")
                return []
            
            # Strip markdown code fences before JSON parsing (common LLM behavior)
            cleaned = response_content.strip()
            for prefix in ['```json', '```', '```javascript', '```js']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
                    if cleaned.endswith('```'):
                        cleaned = cleaned[:-3].strip()
                    break
            
            # === STAGE 1: Clean + standard JSON parse ===
            entities = self._parse_llm_json_strict(cleaned)
            parse_method = 'strict'
            
            # === STAGE 2: If strict parse fails, try lenient parse ===
            if entities is None:
                entities = self._parse_llm_json_lenient(cleaned)
                parse_method = 'lenient'
            
            # === STAGE 3: If both JSON parses fail, extract entities from raw text ===
            if entities is None:
                entities = self._extract_entities_from_llm_text(cleaned)
                parse_method = 'text_extract'
            
            # Log full response to per-job file for debugging
            from datetime import datetime
            job_id = os.environ.get('CURRENT_JOB_ID', 'unknown')
            log_dir = '/root/qwen/ai_agent/logs/llm_responses'
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'job_{job_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'chunk_length': len(text_snippet),
                    'response': response_content,
                    'parse_method': parse_method,
                    'parsed_entities_count': len(entities) if isinstance(entities, list) else 0
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"LLM response preview: {response_content[:200]}")
            logger.info(f"Full response saved to: {log_file}")
            
            # If all parse methods failed → fall back to regex
            if entities is None or not isinstance(entities, list):
                logger.warning(f"⚠️ All LLM parse methods failed for this chunk")
                self.llm_extraction_failed = True
                return self._extract_entities_regex(text)
            
            # If empty array returned (valid: no entities in this chunk)
            if len(entities) == 0:
                logger.info(f"LLM found no entities (parse: {parse_method})")
                return []
            
            # Validate and normalize entities
            validated_entities = []
            hallucinated_count = 0
            verified_count = 0
            
            # Hallucination detection: Check for abnormal entity counts
            max_expected_entities = max(30, len(text_snippet) // 20)
            if len(entities) > max_expected_entities * 2:
                logger.warning(f"⚠️ Hallucination detected: {len(entities)} entities from {len(text_snippet)} chars (expected max {max_expected_entities})")
            
            seen_names = set()
            duplicate_count = 0
            
            for entity in entities:
                if isinstance(entity, dict) and entity.get('name'):
                    entity_name = entity['name'].strip()
                    
                    # Skip empty or suspicious names
                    if len(entity_name) < 2 or entity_name in ['...', 'data', 'text', None, '']:
                        continue
                    
                    # Detect duplicates within single response
                    if entity_name in seen_names:
                        duplicate_count += 1
                        continue
                    
                    seen_names.add(entity_name)
                    
                    # === ENTITY VERIFICATION ===
                    original_text = entity.get('original_text', '')
                    is_valid, match_type, evidence = self._verify_entity_in_text(
                        entity_name, original_text, text_snippet
                    )
                    
                    if not is_valid:
                        hallucinated_count += 1
                        if hallucinated_count <= 5:
                            logger.warning(f"⚠️ Hallucinated entity: '{entity_name}' - not found in source text")
                        continue
                    
                    verified_count += 1
                    
                    if 'relevance' not in entity:
                        entity['relevance'] = 'medium'
                    
                    validated_entities.append(entity)
            
            if hallucinated_count > 0:
                logger.info(f"✅ Verification: {verified_count} valid, {hallucinated_count} hallucinated (removed)")
            else:
                logger.info(f"✅ Verification: All {verified_count} entities found in source text")
            
            if duplicate_count > 5:
                logger.warning(f"⚠️ {duplicate_count} duplicate entities removed - possible LLM loop/hallucination")
            
            logger.info(f"LLM extracted {len(validated_entities)} entities from {len(text_snippet)} chars (parse: {parse_method})")
            return validated_entities
            
        except Exception as e:
            logger.error(f"Ошибка извлечения сущностей LLM: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Try all three parse methods as fallback before giving up
            try:
                entities = self._parse_llm_json_lenient(cleaned)
                if entities is None:
                    entities = self._extract_entities_from_llm_text(cleaned)
                if entities and isinstance(entities, list) and len(entities) > 0:
                    logger.info(f"Recovered {len(entities)} entities via fallback parse")
                    # Skip verification here (already exception context)
                    # Just return raw valid entities
                    valid = [e for e in entities if isinstance(e, dict) and e.get('name')]
                    if valid:
                        return valid
            except Exception:
                pass
            self.llm_extraction_failed = True
            return []
    
    # ===================== Lenient JSON parsing pipeline =====================
    
    def _clean_json_text(self, text: str) -> str:
        """Clean LLM response text for JSON parsing."""
        t = text.strip()
        # Strip code fences
        for prefix in ['```json', '```', '```javascript', '```js']:
            if t.startswith(prefix):
                t = t[len(prefix):].strip()
                if t.endswith('```'):
                    t = t[:-3].strip()
                break
        # Remove trailing commas before ] or }
        t = re.sub(r',\s*([\]}])', r'\1', t)
        # Escape unescaped control characters ONLY inside JSON string values
        def _escape_inside_strings(s):
            result = []
            in_string = False
            i = 0
            while i < len(s):
                ch = s[i]
                if ch == '"' and (i == 0 or s[i-1] != '\\'):
                    in_string = not in_string
                    result.append(ch)
                elif in_string and ord(ch) < 0x20:
                    result.append(f'\\u{ord(ch):04x}')
                else:
                    result.append(ch)
                i += 1
            return ''.join(result)
        t = _escape_inside_strings(t)
        return t
    
    def _parse_llm_json_strict(self, text: str):
        """Stage 1: Clean + standard json.loads parse."""
        try:
            cleaned = self._clean_json_text(text)
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None
    
    def _parse_llm_json_lenient(self, text: str):
        """Stage 2: Try to recover entities from partially broken JSON.
        
        Handles:
        - Truncated response (missing closing brackets)
        - Array with some broken entries
        - Mixed text + JSON response
        - Multiple JSON objects not wrapped in array
        """
        try:
            cleaned = self._clean_json_text(text)
        except Exception:
            cleaned = text
        
        # Strategy A: Try wrapping bare objects in array (e.g., {...} {...})
        if cleaned.strip().startswith('{'):
            # Maybe multiple objects without array wrapper
            objects = re.findall(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', cleaned)
            if len(objects) > 1:
                return [json.loads(self._clean_json_text(o)) for o in objects]
            return None
        
        # Strategy B: Truncated array - find all complete objects
        objects = re.findall(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', cleaned)
        if objects:
            result = []
            for obj in objects:
                try:
                    item = json.loads(self._clean_json_text(obj))
                    if isinstance(item, dict):
                        result.append(item)
                except (json.JSONDecodeError, ValueError):
                    continue
            if result:
                return result
        
        # Strategy C: Extract "name"/"type" pairs from malformed JSON
        names = re.findall(r'"name"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
        types = re.findall(r'"type"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
        relevances = re.findall(r'"relevance"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
        
        if names:
            result = []
            for i, name in enumerate(names):
                if not name or len(name) < 2:
                    continue
                entity = {'name': name, 'type': 'CONCEPT', 'relevance': 'medium'}
                if i < len(types) and types[i]:
                    entity['type'] = types[i]
                if i < len(relevances) and relevances[i]:
                    entity['relevance'] = relevances[i]
                result.append(entity)
            if result:
                return result
        
        return None
    
    def _extract_entities_from_llm_text(self, text: str):
        """Stage 3: Extract entity-like patterns from raw LLM response text.
        
        Uses regex to find entity indicators even when JSON parsing fails completely.
        """
        entities = []
        seen = set()
        
        # Pattern: "name": "ENTITY_NAME" anywhere in text
        name_pattern = re.findall(r'"name"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        # Pattern: entity mentions like ГОСТ Р 34.10-2012
        gost_pattern = re.findall(r'(ГОСТ\s*(?:Р\s*)?\d+(?:\.\d+)*(?:-\d+)?)', text)
        # Pattern: ТК \d+
        tk_pattern = re.findall(r'(ТК\s*\d+)', text)
        
        all_names = set()
        for name in name_pattern:
            if name and len(name) > 2:
                all_names.add(name.strip())
        for gost in gost_pattern:
            all_names.add(gost.strip())
        for tk in tk_pattern:
            all_names.add(tk.strip())
        
        for name in all_names:
            if name not in seen:
                seen.add(name)
                entities.append({
                    'name': name,
                    'type': 'CONCEPT',
                    'relevance': 'low'
                })
        
        return entities if entities else None
    
    def _verify_entity_in_text(self, entity_name: str, original_text: str, source_text: str) -> tuple:
        """
        Verify that an entity actually exists in the source text.
        
        Args:
            entity_name: Normalized entity name (e.g., "ГОСТ 34.10")
            original_text: Original text from LLM response (if provided)
            source_text: Full source text snippet
            
        Returns:
            Tuple of (is_valid: bool, match_type: str, evidence: str)
        """
        import re
        
        # Case 1: original_text provided → exact substring match
        if original_text and original_text.strip():
            if original_text.lower() in source_text.lower():
                return True, "exact_original", original_text[:50]
            
            # Check if entity_name appears within original_text context
            if entity_name.lower() in original_text.lower():
                # Verify original_text contains key words from source
                source_words = set(source_text.lower().split())
                original_words = set(original_text.lower().split())
                overlap = len(source_words & original_words) / len(original_words)
                
                if overlap > 0.5:  # More than 50% word overlap
                    return True, "partial_original", original_text[:50]
        
        # Case 2: No original_text → verify entity_name directly in source
        normalized_entity = entity_name.lower().strip()
        normalized_source = source_text.lower()
        
        # Direct substring check
        if normalized_entity in normalized_source:
            return True, "direct_match", entity_name
        
        # For GOST standards: check for variations (ГОСТ Р vs ГОСТ, with/without year)
        gost_pattern = r'ГОСТ\s*[Р]?\s*(\d+\.\d+)(?:[—-]\s*\d+)?'
        entity_match = re.search(gost_pattern, entity_name)
        
        if entity_match:
            major, minor = entity_match.groups()
            # Check if this GOST number exists in source (with any year/format)
            for gost_in_source in re.finditer(gost_pattern, normalized_source):
                src_major, src_minor = gost_in_source.groups()
                if src_major == major and src_minor == minor:
                    return True, "gost_match", f"ГОСТ {major}.{minor}"
        
        # For Russian words: simple stem check (remove common endings)
        russian_endings = ['ю', 'ую', 'ую', 'ий', 'ый', 'ого', 'его', 'ом', 'ем', 'ым']
        for ending in russian_endings:
            if entity_name.lower().endswith(ending):
                stem = entity_name[:-len(ending)]
                # Check if stem + any ending exists in source
                for test_ending in ['', 'я', 'е', 'ю', 'ый', 'ий']:
                    test_word = stem + test_ending
                    if test_word.lower() in normalized_source:
                        return True, "stem_match", test_word
        
        return False, "not_found", entity_name
    
    def _discover_patterns_from_llm(self, llm_entities: List[Dict], text: str) -> List[Dict]:
        """
        Analyze LLM results to discover new regex patterns.
        
        Args:
            llm_entities: Entities extracted by LLM
            text: Original text (for context)
            
        Returns:
            List of pattern dicts with category, regex_pattern, example, description
        """
        new_patterns = []
        
        for entity in llm_entities:
            entity_type = entity.get('type')
            entity_name = entity.get('name', '')
            synonyms = entity.get('synonyms', [])
            
            # 1. If abbreviation with synonyms, create bidirectional pattern
            if entity_type == 'ABBREVIATION' and synonyms:
                for synonym in synonyms:
                    # Create pattern that matches both forms
                    escaped_name = re.escape(entity_name)
                    escaped_synonym = re.escape(synonym)
                    
                    pattern_info = {
                        'category': 'abbreviations',
                        'regex_pattern': rf'({escaped_name}|{escaped_synonym})',
                        'example': f"{synonym} → {entity_name}",
                        'description': f"Abbreviation: {entity_name} = {synonym}"
                    }
                    new_patterns.append(pattern_info)
            
            # 2. If organization with numeric identifier (ТК XX, etc.)
            elif entity_type == 'ORGANIZATION':
                # Extract patterns like "ТК 26", "Комитет № 1", etc.
                numeric_match = re.search(r'(\w{1,4})\s*(\d+)', entity_name)
                if numeric_match:
                    prefix = numeric_match.group(1)
                    pattern_info = {
                        'category': 'organizations',
                        'regex_pattern': rf'{re.escape(prefix)}\s*\d+',
                        'example': entity_name,
                        'description': f"Organization with numeric identifier"
                    }
                    new_patterns.append(pattern_info)
            
            # 3. If standard reference (ГОСТ X.X, etc.)
            elif entity_type == 'STANDARD':
                # Extract pattern for this standard type
                gost_match = re.match(r'(ГОСТ|GOST)\s*[Р]?\s*(\d+\.\d+)', entity_name, re.IGNORECASE)
                if gost_match:
                    prefix = gost_match.group(1)
                    normalized_prefix = 'ГОСТ' if prefix.upper() == 'GOST' else prefix
                    
                    pattern_info = {
                        'category': 'standards',
                        'regex_pattern': rf'(ГОСТ|GOST)\s*[Р]?\s*\d+\.\d+',
                        'example': entity_name,
                        'description': f"Government standard reference"
                    }
                    new_patterns.append(pattern_info)
        
        return new_patterns
    
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
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE e.name CONTAINS $query 
                    OPTIONAL MATCH (e)<-[:MENTIONS]-(c:Chunk)
                    RETURN e.name as name, 
                           e.type as type, 
                           e.relevance as relevance,
                           collect(c.chunk_id) as chunk_ids
                    ORDER BY e.relevance DESC
                    LIMIT $limit
                """, {'query': query, 'limit': limit})
                
                entities = []
                for record in result:
                    entity = dict(record)
                    entity['chunk_ids'] = entity.get('chunk_ids') or []
                    entities.append(entity)
                return entities
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
                    MATCH (start)-[r:RELATES_TO*1..$depth]-(related:Entity)
                    RETURN related.name as name,
                           related.type as type,
                           related.relevance as relevance,
                           head(collect(r.relationship_type)) as relationship_type
                    ORDER BY related.relevance DESC
                    LIMIT $limit
                """, {'name': entity_name, 'depth': max_depth, 'limit': limit})
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error getting related entities: {e}")
            return []
    
    def get_entity_relationships(self, entity_name: str, limit: int = 20) -> List[Dict]:
        """
        Get all relationships for a specific entity.
        
        Args:
            entity_name: Entity to find relationships for
            limit: Max relationships to return
            
        Returns:
            List of relationships with from/to entities and relationship type
        """
        if not self.connected:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity {name: $name})-[r:RELATES_TO]-(other:Entity)
                    RETURN 
                        CASE WHEN startNode(r) = e THEN other.name ELSE e.name END as related_entity,
                        CASE WHEN startNode(r) = e THEN endNode(r).type ELSE startNode(r).type END as related_type,
                        r.relationship_type as relationship_type,
                        r.created_at as created_at
                    LIMIT $limit
                """, {'name': entity_name, 'limit': limit})
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error getting entity relationships: {e}")
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

    def query_similar_chunks(self, chunk_text: str, limit: int = 5) -> List[Dict]:
        """Query for similar chunks (requires vector indexing setup)"""
        if not self.connected:
            return []
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Chunk)
                    WHERE c.content CONTAINS $query
                    RETURN c.chunk_id as chunk_id, 
                           c.content as content,
                           c.section as section
                    LIMIT $limit
                """, {'query': chunk_text[:100], 'limit': limit})
                
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error querying similar chunks: {e}")
            return []
    
    def get_document_graph(self, doc_id: str) -> Dict[str, Any]:
        """Get the graph structure for a document"""
        if not self.connected:
            return {'chunks': [], 'entities': [], 'relationships': []}
            
        try:
            with self.driver.session() as session:
                chunks_result = session.run("""
                    MATCH (d:Document {doc_id: $doc_id})-[:HAS_CHUNK]->(c:Chunk)
                    RETURN c.chunk_id as chunk_id,
                           c.section as section,
                           c.title as title,
                           c.chunk_type as chunk_type
                    ORDER BY c.chunk_index
                """, {'doc_id': doc_id})
                
                entities_result = session.run("""
                    MATCH (d:Document {doc_id: $doc_id})-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
                    RETURN DISTINCT e.name as name, e.type as type
                """, {'doc_id': doc_id})
                
                return {
                    'chunks': [r.data() for r in chunks_result],
                    'entities': [r.data() for r in entities_result],
                    'relationships': []
                }
        except Exception as e:
            logger.error(f"Error getting document graph: {e}")
            return {}


# Global instance
neo4j_integration = Neo4jIntegration()


def get_neo4j_connection() -> Neo4jIntegration:
    """Get or create Neo4j connection"""
    if not neo4j_integration.connected:
        neo4j_integration.connect()
    return neo4j_integration

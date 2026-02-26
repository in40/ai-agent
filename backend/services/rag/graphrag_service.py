"""
GraphRAG Entity Extraction Service
Extracts entities and relationships from document chunks using LLM
Stores results in Neo4j graph database
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://192.168.51.187:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
LLM_PROVIDER = os.getenv('GRAPH_LLM_PROVIDER', 'openai')
LLM_MODEL = os.getenv('GRAPH_LLM_MODEL', 'gpt-4')
GRAPHRAG_PORT = int(os.getenv('GRAPHRAG_PORT', 8000))

# Neo4j driver setup
try:
    from neo4j import GraphDatabase
    
    class Neo4jDriver:
        _instance = None
        
        @classmethod
        def get_instance(cls):
            if cls._instance is None:
                cls._instance = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            return cls._instance
        
        @classmethod
        def close(cls):
            if cls._instance:
                cls._instance.close()
                cls._instance = None
    
    neo4j_available = True
    logger.info(f"Neo4j driver initialized for {NEO4J_URI}")
except ImportError:
    neo4j_available = False
    logger.warning("Neo4j driver not available - graph storage disabled")
except Exception as e:
    neo4j_available = False
    logger.warning(f"Neo4j connection failed: {e}")


# Entity extraction prompt
ENTITY_EXTRACTION_PROMPT = """
You are an expert knowledge graph engineer. Your task is to extract entities and relationships from document chunks to build a knowledge graph.

## ENTITY TYPES TO EXTRACT
1. **Concepts**: Abstract ideas, principles, theories
2. **Organizations**: Companies, institutions, government bodies
3. **Persons**: Individual people mentioned
4. **Documents**: Standards, specifications, regulations (e.g., GOST, ISO)
5. **Locations**: Places, geographical entities
6. **Events**: Specific occurrences, processes, procedures
7. **Technical Terms**: Domain-specific terminology
8. **Requirements**: Mandatory conditions, constraints

## RELATIONSHIP TYPES
1. **RELATED_TO**: General association
2. **PART_OF**: Hierarchical containment
3. **REFERENCES**: Citation or mention
4. **REQUIRES**: Dependency
5. **IMPLEMENTS**: Realization of a concept
6. **GOVERNS**: Regulatory control
7. **APPLIES_TO**: Scope of application
8. **CONTRADICTS**: Conflict or opposition
9. **SIMILAR_TO**: Analogy or resemblance

## OUTPUT FORMAT
Return ONLY valid JSON in this exact structure:
{
  "entities": [
    {
      "id": "unique_identifier",
      "name": "Entity name as it appears in text",
      "type": "one of the entity types above",
      "description": "Brief description based on context",
      "metadata": {
        "source_chunk": chunk_id,
        "confidence": 0.0-1.0
      }
    }
  ],
  "relationships": [
    {
      "source": "source_entity_id",
      "target": "target_entity_id",
      "type": "relationship type",
      "description": "Description of the relationship",
      "metadata": {
        "source_chunk": chunk_id,
        "confidence": 0.0-1.0
      }
    }
  ],
  "summary": "Brief summary of the knowledge extracted"
}

## RULES
1. Use consistent entity names (same entity = same ID across chunks)
2. Extract only entities explicitly mentioned in the text
3. Infer relationships from context, but mark lower confidence
4. For Russian technical standards, preserve original terminology
5. Include section/chapter references in metadata

## SPECIAL HANDLING FOR TECHNICAL STANDARDS
- Extract standard identifiers (GOST R 12345-2020)
- Capture trust levels, security scenarios
- Preserve hierarchical structure (sections, subsections)
- Extract formulas and their variables as entities

---
DOCUMENT CHUNKS:
{document_text}
"""


def get_llm_response(prompt: str) -> str:
    """
    Get response from LLM for entity extraction.
    Uses the configured LLM provider.
    """
    try:
        # For now, use a simple OpenAI API call
        # In production, this would use the project's LLM abstraction
        from models.response_generator import ResponseGenerator
        
        response_gen = ResponseGenerator()
        llm = response_gen._get_llm_instance(provider=LLM_PROVIDER, model=LLM_MODEL)
        
        response = llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
        
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise


def parse_extraction_result(llm_response: str) -> Dict[str, Any]:
    """Parse LLM response into structured entities and relationships"""
    import re
    
    try:
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
        else:
            result = json.loads(llm_response)
        
        # Validate structure
        if 'entities' not in result or 'relationships' not in result:
            raise ValueError("Invalid extraction result structure")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {e}")
        logger.error(f"LLM response: {llm_response[:500]}...")
        raise


def store_in_neo4j(entities: List[Dict], relationships: List[Dict], document_id: str):
    """
    Store entities and relationships in Neo4j graph database.
    
    Args:
        entities: List of entity dictionaries
        relationships: List of relationship dictionaries
        document_id: Source document identifier
    """
    if not neo4j_available:
        logger.warning("Neo4j not available, skipping graph storage")
        return {"entities_stored": 0, "relationships_stored": 0}
    
    try:
        driver = Neo4jDriver.get_instance()
        
        with driver.session() as session:
            # Store entities
            entities_stored = 0
            for entity in entities:
                session.run("""
                    MERGE (e:Entity {id: $id, document: $document})
                    SET e.name = $name,
                        e.type = $type,
                        e.description = $description,
                        e.metadata = $metadata,
                        e.updated_at = datetime()
                """, {
                    "id": entity["id"],
                    "document": document_id,
                    "name": entity["name"],
                    "type": entity["type"],
                    "description": entity.get("description", ""),
                    "metadata": entity.get("metadata", {})
                })
                entities_stored += 1
            
            # Store relationships
            relationships_stored = 0
            for rel in relationships:
                session.run("""
                    MATCH (source:Entity {id: $source_id})
                    MATCH (target:Entity {id: $target_id})
                    MERGE (source)-[r:RELATIONSHIP {
                        type: $rel_type,
                        target: $target_id
                    }]->(target)
                    SET r.description = $description,
                        r.metadata = $metadata,
                        r.updated_at = datetime()
                """, {
                    "source_id": rel["source"],
                    "target_id": rel["target"],
                    "rel_type": rel["type"],
                    "description": rel.get("description", ""),
                    "metadata": rel.get("metadata", {})
                })
                relationships_stored += 1
            
            logger.info(f"Stored {entities_stored} entities and {relationships_stored} relationships in Neo4j")
            
            return {
                "entities_stored": entities_stored,
                "relationships_stored": relationships_stored
            }
            
    except Exception as e:
        logger.error(f"Neo4j storage error: {e}")
        return {
            "entities_stored": 0,
            "relationships_stored": 0,
            "error": str(e)
        }


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'graphrag_entity_extraction',
        'timestamp': datetime.utcnow().isoformat(),
        'neo4j_available': neo4j_available,
        'neo4j_uri': NEO4J_URI,
        'llm_provider': LLM_PROVIDER,
        'llm_model': LLM_MODEL
    }), 200


@app.route('/extract_entities', methods=['POST'])
def extract_entities():
    """
    Extract entities and relationships from document chunks.
    
    Request body:
    {
        "document_id": "unique document identifier",
        "chunks": [
            {
                "chunk_id": 1,
                "content": "chunk text content",
                "metadata": {...}
            }
        ],
        "prompt_template": "optional custom prompt"
    }
    
    Response:
    {
        "document_id": "...",
        "entities_count": 10,
        "relationships_count": 5,
        "entities": [...],
        "relationships": [...],
        "neo4j_result": {...}
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        document_id = data.get('document_id')
        chunks = data.get('chunks', [])
        custom_prompt = data.get('prompt_template')
        
        if not document_id:
            return jsonify({'error': 'document_id is required'}), 400
        
        if not chunks:
            return jsonify({'error': 'No chunks provided'}), 400
        
        logger.info(f"Extracting entities from document: {document_id} ({len(chunks)} chunks)")
        
        # Prepare document text
        document_text = ""
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '')
            chunk_id = chunk.get('chunk_id', i)
            document_text += f"\n\n[Chunk {chunk_id}]:\n{content}\n"
        
        # Limit text size to avoid LLM token limits
        max_text_length = 50000  # ~10K tokens
        if len(document_text) > max_text_length:
            document_text = document_text[:max_text_length] + "\n\n[... truncated ...]"
        
        # Build prompt
        prompt_template = custom_prompt or ENTITY_EXTRACTION_PROMPT
        prompt = prompt_template.format(document_text=document_text)
        
        # Call LLM for extraction
        logger.info("Calling LLM for entity extraction...")
        llm_response = get_llm_response(prompt)
        
        # Parse result
        extraction_result = parse_extraction_result(llm_response)
        
        entities = extraction_result.get('entities', [])
        relationships = extraction_result.get('relationships', [])
        
        logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships")
        
        # Store in Neo4j
        neo4j_result = store_in_neo4j(entities, relationships, document_id)
        
        # Build response
        result = {
            'document_id': document_id,
            'entities_count': len(entities),
            'relationships_count': len(relationships),
            'entities': entities,
            'relationships': relationships,
            'neo4j_result': neo4j_result,
            'summary': extraction_result.get('summary', ''),
            'processing_time': extraction_result.get('processing_time', 0)
        }
        
        return jsonify(result), 200
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return jsonify({
            'error': f'Failed to parse LLM response: {str(e)}',
            'llm_response': llm_response[:1000] if 'llm_response' in locals() else ''
        }), 500
        
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Entity extraction failed: {str(e)}'}), 500


@app.route('/search_graph', methods=['POST'])
def search_graph():
    """
    Search the knowledge graph for entities and relationships.
    
    Request body:
    {
        "query": "search query",
        "entity_types": ["optional", "type", "filter"],
        "limit": 20
    }
    
    Response:
    {
        "entities": [...],
        "relationships": [...],
        "total": 10
    }
    """
    if not neo4j_available:
        return jsonify({'error': 'Neo4j not available'}), 503
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        entity_types = data.get('entity_types', [])
        limit = data.get('limit', 20)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        driver = Neo4jDriver.get_instance()
        
        with driver.session() as session:
            # Build search query
            if entity_types:
                type_filter = " AND e.type IN $entity_types"
            else:
                type_filter = ""
            
            cypher_query = f"""
                MATCH (e:Entity)
                WHERE (e.name CONTAINS $query OR e.description CONTAINS $query)
                {type_filter}
                RETURN e
                LIMIT $limit
            """
            
            result = session.run(
                cypher_query,
                query=query,
                entity_types=entity_types,
                limit=limit
            )
            
            entities = [record["e"] for record in result]
            
            # Get relationships for found entities
            entity_ids = [e["id"] for e in entities]
            
            rel_query = """
                MATCH (source:Entity)-[r:RELATIONSHIP]->(target:Entity)
                WHERE source.id IN $entity_ids OR target.id IN $entity_ids
                RETURN source, r, target
                LIMIT $limit
            """
            
            rel_result = session.run(rel_query, entity_ids=entity_ids, limit=limit)
            
            relationships = []
            for record in rel_result:
                relationships.append({
                    'source': record["source"]["id"],
                    'target': record["target"]["id"],
                    'type': record["r"]["type"],
                    'description': record["r"].get("description", "")
                })
            
            return jsonify({
                'entities': entities,
                'relationships': relationships,
                'total': len(entities)
            }), 200
            
    except Exception as e:
        logger.error(f"Graph search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_entity/<entity_id>', methods=['GET'])
def get_entity(entity_id: str):
    """Get a specific entity and its relationships"""
    if not neo4j_available:
        return jsonify({'error': 'Neo4j not available'}), 503
    
    try:
        driver = Neo4jDriver.get_instance()
        
        with driver.session() as session:
            # Get entity
            entity_result = session.run("""
                MATCH (e:Entity {id: $id})
                RETURN e
            """, id=entity_id)
            
            entity_record = entity_result.single()
            if not entity_record:
                return jsonify({'error': f'Entity {entity_id} not found'}), 404
            
            entity = dict(entity_record["e"])
            
            # Get relationships
            rel_result = session.run("""
                MATCH (source:Entity)-[r:RELATIONSHIP]->(target:Entity)
                WHERE source.id = $id OR target.id = $id
                RETURN source, r, target
            """, id=entity_id)
            
            relationships = []
            for record in rel_result:
                relationships.append({
                    'source': record["source"]["id"],
                    'target': record["target"]["id"],
                    'type': record["r"]["type"],
                    'description': record["r"].get("description", "")
                })
            
            return jsonify({
                'entity': entity,
                'relationships': relationships,
                'relationship_count': len(relationships)
            }), 200
            
    except Exception as e:
        logger.error(f"Get entity error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/graph_stats', methods=['GET'])
def graph_statistics():
    """Get statistics about the knowledge graph"""
    if not neo4j_available:
        return jsonify({'error': 'Neo4j not available'}), 503
    
    try:
        driver = Neo4jDriver.get_instance()
        
        with driver.session() as session:
            # Count entities by type
            type_stats = session.run("""
                MATCH (e:Entity)
                RETURN e.type as type, count(e) as count
                ORDER BY count DESC
            """)
            
            entity_types = {record["type"]: record["count"] for record in type_stats}
            
            # Total counts
            total_entities = session.run("MATCH (e:Entity) RETURN count(e) as count").single()["count"]
            total_relationships = session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN count(r) as count").single()["count"]
            
            # Documents in graph
            documents = session.run("""
                MATCH (e:Entity)
                RETURN DISTINCT e.document as document
            """)
            document_list = [record["document"] for record in documents]
            
            return jsonify({
                'total_entities': total_entities,
                'entity_types': entity_types,
                'total_relationships': total_relationships,
                'documents': document_list,
                'document_count': len(document_list)
            }), 200
            
    except Exception as e:
        logger.error(f"Graph stats error: {e}")
        return jsonify({'error': str(e)}), 500


def cleanup():
    """Cleanup resources on shutdown"""
    Neo4jDriver.close()
    logger.info("Neo4j driver closed")


if __name__ == '__main__':
    import atexit
    atexit.register(cleanup)
    
    logger.info(f"Starting GraphRAG Entity Extraction Service on port {GRAPHRAG_PORT}")
    app.run(host='0.0.0.0', port=GRAPHRAG_PORT, debug=False)

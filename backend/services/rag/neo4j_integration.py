"""
Neo4j Graph Database Integration for Hybrid RAG Ingestion
Handles storage of document chunks and relationships in Neo4j Graph DB
"""
import os
import json
import logging
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime

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
        # Check if tunnel is already running
        result = subprocess.run(
            ['pgrep', '-f', f'ssh.*-L.*{NEO4J_SSH_TUNNEL_PORT}.*{NEO4J_SSH_HOST}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            logger.info("SSH tunnel to Neo4j already established")
            return True
        
        # Expand SSH key path
        ssh_key = os.path.expanduser(NEO4J_SSH_KEY)
        
        # Establish SSH tunnel
        logger.info(f"Establishing SSH tunnel to {NEO4J_SSH_HOST}:{NEO4J_SSH_TUNNEL_PORT}...")
        subprocess.Popen([
            'ssh', '-N', '-f',
            '-i', ssh_key,
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
    
    def __init__(self):
        self.driver = None
        self.connected = False
        self.last_error = None
        
    def connect(self) -> bool:
        """Establish connection to Neo4j"""
        try:
            # Ensure SSH tunnel is established
            if NEO4J_SSH_HOST:
                ensure_ssh_tunnel()
            
            from neo4j import GraphDatabase
            
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                database=NEO4J_DATABASE,
                connection_timeout=30
            )
            
            # Test connection
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
                        d.job_id = $job_id
                """, {
                    'doc_id': doc_id,
                    'filename': filename,
                    'uploaded_at': metadata.get('uploaded_at', datetime.utcnow().isoformat()),
                    'format': metadata.get('format', 'pdf'),
                    'job_id': metadata.get('job_id', '')
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
                # Create chunk node
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
                
                # Add metadata relationships if present
                if chunk_data.get('formula_reference'):
                    session.run("""
                        MATCH (c:Chunk {chunk_id: $chunk_id})
                        MATCH (f:Formula {formula_id: $formula_id})
                        CREATE (c)-[:REFERENCES]->(f)
                    """, {
                        'chunk_id': chunk_id,
                        'formula_id': chunk_data.get('formula_reference')
                    })
                
                if chunk_data.get('trust_level'):
                    session.run("""
                        MATCH (c:Chunk {chunk_id: $chunk_id})
                        SET c.trust_level = $trust_level
                    """, {
                        'chunk_id': chunk_id,
                        'trust_level': chunk_data.get('trust_level')
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
    
    def create_knowledge_graph(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Create knowledge graph from chunks by extracting entities and relationships.
        This is an advanced feature that analyzes chunk content to build semantic relationships.
        """
        if not self.connected:
            return {'entities': 0, 'relationships': 0}
            
        stats = {'entities': 0, 'relationships': 0}
        
        try:
            with self.driver.session() as session:
                for chunk in chunks:
                    content = chunk.get('content', '')
                    chunk_id = f"chunk_{chunk.get('chunk_id', 0)}"
                    
                    # Extract and create entities (simplified - in production use NLP)
                    # This is a placeholder for more sophisticated entity extraction
                    entities = self._extract_entities(content)
                    
                    for entity in entities:
                        session.run("""
                            MERGE (e:Entity {name: $name, type: $type})
                            SET e.updated_at = datetime()
                        """, entity)
                        stats['entities'] += 1
                        
                        # Create relationship between chunk and entity
                        session.run("""
                            MATCH (c:Chunk {chunk_id: $chunk_id})
                            MATCH (e:Entity {name: $name, type: $type})
                            MERGE (c)-[:MENTIONS]->(e)
                        """, {
                            'chunk_id': chunk_id,
                            'name': entity['name'],
                            'type': entity['type']
                        })
                        stats['relationships'] += 1
                        
        except Exception as e:
            logger.error(f"Error creating knowledge graph: {e}")
            
        return stats
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract entities from text.
        This is a simplified implementation - in production, use NLP libraries like spaCy.
        """
        entities = []
        
        # Simple pattern-based extraction (placeholder)
        # In production, use proper NLP entity recognition
        
        # Extract GOST standards references
        import re
        gost_pattern = r'ГОСТ\s*[Р]?\s*(\d+\.\d+)'
        for match in re.finditer(gost_pattern, text, re.IGNORECASE):
            entities.append({
                'name': f'GOST {match.group(1)}',
                'type': 'STANDARD'
            })
            
        return entities
    
    def query_similar_chunks(self, chunk_text: str, limit: int = 5) -> List[Dict]:
        """Query for similar chunks (requires vector indexing setup)"""
        if not self.connected:
            return []
            
        try:
            with self.driver.session() as session:
                # This requires Neo4j with vector indexing enabled
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
                # Get chunks
                chunks_result = session.run("""
                    MATCH (d:Document {doc_id: $doc_id})-[:HAS_CHUNK]->(c:Chunk)
                    RETURN c.chunk_id as chunk_id,
                           c.section as section,
                           c.title as title,
                           c.chunk_type as chunk_type
                    ORDER BY c.chunk_index
                """, {'doc_id': doc_id})
                
                # Get entities mentioned in this document
                entities_result = session.run("""
                    MATCH (d:Document {doc_id: $doc_id})-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
                    RETURN DISTINCT e.name as name, e.type as type
                """, {'doc_id': doc_id})
                
                return {
                    'chunks': [r.data() for r in chunks_result],
                    'entities': [r.data() for r in entities_result],
                    'relationships': []  # Could be expanded
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

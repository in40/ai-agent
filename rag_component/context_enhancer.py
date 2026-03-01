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
        """Initialize context enhancer with Neo4j connection."""
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
        
        Args:
            documents: Enhanced documents
            
        Returns:
            Formatted context string for LLM prompt
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

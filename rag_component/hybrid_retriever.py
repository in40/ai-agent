"""
Hybrid Retriever - Combines vector and graph-based retrieval
"""
import os
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document as LCDocument
from .config import (
    RAG_TOP_K_RESULTS, 
    RAG_SIMILARITY_THRESHOLD,
    RAG_HYBRID_VECTOR_WEIGHT,
    RAG_HYBRID_GRAPH_WEIGHT
)
from .vector_store_manager import VectorStoreManager
from backend.services.rag.neo4j_integration import get_neo4j_connection


class HybridRetriever:
    """
    Hybrid retriever that combines vector similarity search 
    with graph-based entity retrieval.
    """
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store_manager: Vector store manager instance
        """
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
    
    def retrieve_with_scores(self, query: str, top_k: int = None) -> List[Tuple[LCDocument, float]]:
        """
        Retrieve documents with hybrid scores.
        
        Args:
            query: User query
            top_k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        docs = self.retrieve(query, top_k)
        
        # Convert to LangChain document format
        result = []
        for doc_data in docs:
            doc = LCDocument(
                page_content=doc_data['content'],
                metadata=doc_data['metadata']
            )
            result.append((doc, doc_data['hybrid_score']))
        
        return result

    def retrieve_documents_with_scores(self, query: str, top_k: int = None) -> List[Tuple[LCDocument, float]]:
        """
        Retrieve documents with scores (alias for retrieve_with_scores).
        This method exists for compatibility with the original Retriever interface.

        Args:
            query: User query
            top_k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        return self.retrieve_with_scores(query, top_k)

    def _vector_search(self, query: str, top_k: int) -> List[Dict]:
        """
        Perform vector similarity search.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of document dicts with vector scores
        """
        docs_with_scores = self.vector_store_manager.similarity_search_with_score(
            query=query, 
            top_k=top_k
        )
        
        formatted = []
        for doc, score in docs_with_scores:
            formatted.append({
                'content': doc.page_content,
                'metadata': dict(doc.metadata),
                'vector_score': float(score),
                'graph_score': 0.0,
                'source': 'vector'
            })
        
        return formatted
    
    def _graph_search(self, query: str, top_k: int) -> List[Dict]:
        """
        Perform graph-based entity search with Vector DB chunk retrieval.
        
        Reference-based architecture:
        1. Query Neo4j for entities matching search terms
        2. Get chunk UUIDs from entity.chunk_ids property
        3. Fetch actual chunks from Vector DB using UUIDs
        
        Args:
            query: User query
            top_k: Number of results
            
        Returns:
            List of document dicts with graph scores
        """
        if not self.neo4j or not self.neo4j.connected:
            return []
        
        # Extract key terms from query (simple approach)
        # Keep short terms that might be abbreviations (ТК, ГОСТ, etc.)
        # Filter very short terms (< 2 chars), strip punctuation, and limit to top terms
        import re
        query_terms = []
        for word in query.split():
            # Strip punctuation from word
            clean_word = re.sub(r'[^\w\s]', '', word)
            if len(clean_word) >= 2:
                query_terms.append(clean_word)
        query_terms = query_terms[:10]
        
        if not query_terms:
            return []
        
        # Collect all chunk UUIDs and entity metadata
        chunk_uuid_map = {}  # chunk_uuid -> entity info
        all_chunk_uuids = set()
        
        for term in query_terms:
            entities = self.neo4j.query_entities_by_text(term, limit=max(1, top_k // len(query_terms)))
            
            for entity in entities:
                chunk_ids = entity.get('chunk_ids', [])
                
                # Handle relevance as string or number
                relevance = entity.get('relevance', 0.0)
                if isinstance(relevance, str):
                    # Convert text relevance to numeric score
                    relevance_map = {'high': 1.0, 'medium': 0.5, 'low': 0.25}
                    relevance = relevance_map.get(relevance.lower(), 0.5)
                else:
                    relevance = float(relevance) / 100.0
                
                entity_info = {
                    'entity_name': entity['name'],
                    'entity_type': entity.get('type', 'CONCEPT'),
                    'relevance': relevance
                }
                
                for chunk_uuid in chunk_ids:
                    all_chunk_uuids.add(chunk_uuid)
                    # Keep first matching entity info (could be enhanced to track multiple)
                    if chunk_uuid not in chunk_uuid_map:
                        chunk_uuid_map[chunk_uuid] = entity_info
        
        if not all_chunk_uuids:
            return []
        
        # Fetch chunks from Vector DB by UUIDs
        try:
            vector_docs = self.vector_store_manager.similarity_search_by_ids(
                list(all_chunk_uuids), top_k=top_k * 2
            )
        except Exception as e:
            logger.warning(f"Vector DB UUID search failed: {e}")
            return []
        
        # Format results with entity metadata
        formatted = []
        for doc in vector_docs:
            # Try both chunk_uuid and chunk_id (for compatibility)
            chunk_uuid = doc.metadata.get('chunk_uuid', doc.metadata.get('chunk_id', ''))
            entity_info = chunk_uuid_map.get(chunk_uuid, {})
            
            formatted.append({
                'content': doc.page_content,
                'metadata': {
                    'entity_name': entity_info.get('entity_name', ''),
                    'entity_type': entity_info.get('entity_type', ''),
                    'chunk_uuid': chunk_uuid,
                    'upload_method': 'Graph RAG'
                },
                'vector_score': 0.0,
                'graph_score': entity_info.get('relevance', 0.0),
                'source': 'graph'
            })
        
        return formatted
    
    def _merge_results(self, vector_docs: List[Dict], graph_docs: List[Dict], 
                      top_k: int) -> List[Dict]:
        """
        Merge vector and graph results with smart scoring.
        
        Uses reciprocal rank fusion with weighted scoring.
        
        Args:
            vector_docs: Documents from vector search
            graph_docs: Documents from graph search
            top_k: Number of results to return
            
        Returns:
            Merged and ranked list of documents
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
                content_map[content_key]['source'] = 'both'
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
    
    def get_relevant_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Get relevant documents formatted for use in the RAG pipeline.
        
        Args:
            query: User query
            
        Returns:
            List of dictionaries containing document content and metadata
        """
        docs = self.retrieve(query)
        
        # Format documents for RAG pipeline
        formatted_docs = []
        for doc in docs:
            if doc.get('hybrid_score', 0) >= self.similarity_threshold:
                # Determine the source label based on upload method
                upload_method = doc['metadata'].get('upload_method', '')
                
                # Update upload method labels to be more specific
                if upload_method == "Web upload":
                    source_label = "Client upload"
                elif upload_method == "Local":
                    source_label = "Local"
                elif upload_method == "Processed JSON Import":
                    source_label = "Processed JSON Upload"
                elif upload_method == "Graph RAG":
                    source_label = "Graph RAG"
                else:
                    source_label = "Unknown"
                
                # Add ChromaDB collection name to the source label
                collection_name = self.vector_store_manager.collection_name if hasattr(self.vector_store_manager, 'collection_name') else "default"
                source_label = f"{source_label} [Collection: {collection_name}]"
                
                # Prepare document info for download if available
                download_info = None
                if doc['metadata'].get('file_id') and doc['metadata'].get('stored_file_path'):
                    download_info = {
                        "file_id": doc['metadata'].get('file_id'),
                        "filename": os.path.basename(doc['metadata'].get('stored_file_path', "")),
                        "download_available": True
                    }
                
                formatted_docs.append({
                    "content": doc['content'],
                    "title": doc['metadata'].get('title', "Untitled Document"),
                    "source": source_label,
                    "metadata": doc['metadata'],
                    "score": doc['hybrid_score'],
                    "download_info": download_info
                })
        
        return formatted_docs

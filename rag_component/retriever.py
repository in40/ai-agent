"""
Retriever module for the RAG component.
Handles retrieval of relevant documents based on user queries.
"""
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document as LCDocument
from .config import RAG_TOP_K_RESULTS, RAG_SIMILARITY_THRESHOLD
from .vector_store_manager import VectorStoreManager


class Retriever:
    """Class responsible for retrieving relevant documents."""
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager
        self.top_k = RAG_TOP_K_RESULTS
        self.similarity_threshold = RAG_SIMILARITY_THRESHOLD
    
    def retrieve_documents(
        self, 
        query: str, 
        top_k: Optional[int] = None,
        use_mmr: bool = False
    ) -> List[LCDocument]:
        """
        Retrieve relevant documents for a given query.
        
        Args:
            query: User query to find relevant documents for
            top_k: Number of top results to return (uses default if not provided)
            use_mmr: Whether to use Maximal Marginal Relevance search
            
        Returns:
            List of relevant documents
        """
        if top_k is None:
            top_k = self.top_k
        
        if use_mmr:
            return self.vector_store_manager.max_marginal_relevance_search(
                query=query,
                top_k=top_k
            )
        else:
            return self.vector_store_manager.similarity_search(
                query=query,
                top_k=top_k
            )
    
    def retrieve_documents_with_scores(
        self, 
        query: str, 
        top_k: Optional[int] = None
    ) -> List[tuple[LCDocument, float]]:
        """
        Retrieve relevant documents with their similarity scores.
        
        Args:
            query: User query to find relevant documents for
            top_k: Number of top results to return (uses default if not provided)
            
        Returns:
            List of tuples (document, score)
        """
        if top_k is None:
            top_k = self.top_k
        
        return self.vector_store_manager.similarity_search_with_score(
            query=query,
            top_k=top_k
        )
    
    def get_relevant_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Get relevant documents formatted for use in the RAG pipeline.
        
        Args:
            query: User query to find relevant documents for
            
        Returns:
            List of dictionaries containing document content and metadata
        """
        docs_with_scores = self.retrieve_documents_with_scores(query)
        
        # Format documents for RAG pipeline
        formatted_docs = []
        for doc, score in docs_with_scores:
            if score >= self.similarity_threshold:
                formatted_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
        
        return formatted_docs
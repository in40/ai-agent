"""
Vector store manager module for the RAG component.
Handles storage and retrieval of document embeddings.
"""
import os
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LCDocument
from .config import (
    RAG_VECTOR_STORE_TYPE, 
    RAG_CHROMA_PERSIST_DIR, 
    RAG_COLLECTION_NAME,
    RAG_TOP_K_RESULTS,
    RAG_SIMILARITY_THRESHOLD
)
from .embedding_manager import EmbeddingManager


class VectorStoreManager:
    """Class responsible for managing the vector store."""
    
    def __init__(self):
        self.store_type = RAG_VECTOR_STORE_TYPE
        self.top_k = RAG_TOP_K_RESULTS
        self.similarity_threshold = RAG_SIMILARITY_THRESHOLD
        self.embedding_manager = EmbeddingManager()
        
        # Initialize the appropriate vector store
        if self.store_type.lower() == "chroma":
            self.persist_dir = RAG_CHROMA_PERSIST_DIR
            self.collection_name = RAG_COLLECTION_NAME
            self.vector_store = self._initialize_chroma()
        elif self.store_type.lower() == "faiss":
            self.vector_store = self._initialize_faiss()
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
    
    def _initialize_chroma(self):
        """Initialize Chroma vector store."""
        # Create directory if it doesn't exist
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize Chroma with persistence
        vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_manager.embeddings,
            persist_directory=self.persist_dir
        )
        
        return vector_store
    
    def _initialize_faiss(self):
        """Initialize FAISS vector store."""
        # FAISS doesn't have built-in persistence, so we'll create an in-memory store
        # In a production environment, you might want to implement custom persistence
        return None  # Placeholder - would need more implementation for FAISS
    
    def add_documents(self, documents: List[LCDocument], ids: Optional[List[str]] = None):
        """Add documents to the vector store."""
        if self.store_type.lower() == "chroma":
            if ids:
                self.vector_store.add_documents(documents=documents, ids=ids)
            else:
                self.vector_store.add_documents(documents=documents)
        elif self.store_type.lower() == "faiss":
            # Implementation for FAISS would go here
            pass
    
    def similarity_search(self, query: str, top_k: Optional[int] = None) -> List[LCDocument]:
        """
        Perform similarity search in the vector store.
        
        Args:
            query: Query string to search for
            top_k: Number of top results to return (uses default if not provided)
            
        Returns:
            List of relevant documents
        """
        if top_k is None:
            top_k = self.top_k
            
        if self.store_type.lower() == "chroma":
            return self.vector_store.similarity_search(
                query=query,
                k=top_k
            )
        elif self.store_type.lower() == "faiss":
            # Implementation for FAISS would go here
            return []
    
    def similarity_search_with_score(
        self, 
        query: str, 
        top_k: Optional[int] = None
    ) -> List[tuple[LCDocument, float]]:
        """
        Perform similarity search with scores in the vector store.
        
        Args:
            query: Query string to search for
            top_k: Number of top results to return (uses default if not provided)
            
        Returns:
            List of tuples (document, score)
        """
        if top_k is None:
            top_k = self.top_k
            
        if self.store_type.lower() == "chroma":
            return self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k
            )
        elif self.store_type.lower() == "faiss":
            # Implementation for FAISS would go here
            return []
    
    def max_marginal_relevance_search(
        self, 
        query: str, 
        top_k: Optional[int] = None,
        fetch_k: Optional[int] = None
    ) -> List[LCDocument]:
        """
        Perform MMR (Maximal Marginal Relevance) search in the vector store.
        
        Args:
            query: Query string to search for
            top_k: Number of top results to return (uses default if not provided)
            fetch_k: Number of documents to initially fetch for MMR algorithm
            
        Returns:
            List of relevant documents
        """
        if top_k is None:
            top_k = self.top_k
        if fetch_k is None:
            fetch_k = min(top_k * 2, 20)
            
        if self.store_type.lower() == "chroma":
            return self.vector_store.max_marginal_relevance_search(
                query=query,
                k=top_k,
                fetch_k=fetch_k
            )
        elif self.store_type.lower() == "faiss":
            # Implementation for FAISS would go here
            return []
    
    def delete_collection(self):
        """Delete the entire collection from the vector store."""
        if self.store_type.lower() == "chroma":
            # Chroma doesn't have a direct way to delete a collection
            # We'll recreate the vector store to clear it
            self.vector_store = self._initialize_chroma()
    
    def persist(self):
        """Persist the vector store to disk (Chroma handles this automatically)."""
        if self.store_type.lower() == "chroma":
            # Chroma persists automatically, but we can force a sync if needed
            pass
        elif self.store_type.lower() == "faiss":
            # Implementation for FAISS would go here
            pass
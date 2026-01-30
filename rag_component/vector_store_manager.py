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
    RAG_SIMILARITY_THRESHOLD,
    RAG_QDRANT_URL,
    RAG_QDRANT_API_KEY
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
        elif self.store_type.lower() == "qdrant":
            # Get Qdrant config directly from environment to ensure latest values
            import os
            self.qdrant_url = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")
            self.qdrant_api_key = os.getenv("RAG_QDRANT_API_KEY", "")
            self.collection_name = os.getenv("RAG_COLLECTION_NAME", "documents")
            self.vector_store = self._initialize_qdrant()
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

    def _initialize_qdrant(self):
        """Initialize Qdrant vector store."""
        try:
            from qdrant_client import QdrantClient
            try:
                # Try to use the newer QdrantVectorStore class
                from langchain_qdrant import QdrantVectorStore
                QdrantClass = QdrantVectorStore
            except ImportError:
                # Fall back to the older Qdrant class if newer one is not available
                from langchain_qdrant import Qdrant
                QdrantClass = Qdrant

            # Initialize Qdrant client
            if self.qdrant_api_key:
                client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key,
                    prefer_grpc=False  # Use HTTP instead of gRPC to avoid auth issues
                )
            else:
                client = QdrantClient(
                    url=self.qdrant_url,
                    prefer_grpc=False  # Use HTTP instead of gRPC to avoid auth issues
                )

            # Create or connect to the collection
            # Check if collection exists, if not create it
            try:
                collection_info = client.get_collection(self.collection_name)
                # If collection exists, we don't need to recreate it
            except Exception as e:
                # Check if the error is specifically about collection not existing
                # Different Qdrant clients may throw different exceptions
                error_msg = str(e).lower()
                if "not found" in error_msg or "not exist" in error_msg or "missing" in error_msg or "404" in str(e):
                    # Collection doesn't exist, create it
                    from qdrant_client.http.models import Distance, VectorParams
                    # Get the embedding dimension from the embedding model
                    # Only do this when we actually need to create the collection
                    test_embedding = self.embedding_manager.embeddings.embed_query("test")
                    embedding_size = len(test_embedding)
                    print(f"Creating Qdrant collection '{self.collection_name}' with embedding size: {embedding_size}")
                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE),
                    )
                else:
                    # Re-raise the exception if it's not about collection not existing
                    raise e

            # Initialize the LangChain Qdrant wrapper
            # The Qdrant wrapper performs validation that may trigger test embeddings
            # To avoid unwanted test embeddings during initialization, we'll let it proceed normally
            # but note that this is expected behavior of the LangChain Qdrant integration
            try:
                if QdrantClass.__name__ == 'QdrantVectorStore':
                    # QdrantVectorStore uses 'embedding' instead of 'embeddings'
                    vector_store = QdrantClass(
                        client=client,
                        collection_name=self.collection_name,
                        embedding=self.embedding_manager.embeddings
                    )
                else:
                    # Older Qdrant class uses 'embeddings'
                    vector_store = QdrantClass(
                        client=client,
                        collection_name=self.collection_name,
                        embeddings=self.embedding_manager.embeddings
                    )
            except Exception as e:
                # Check if the error is due to dimension mismatch
                error_str = str(e).lower()
                if "dimension" in error_str and "mismatch" in error_str or "configured for" in error_str and "dimensions" in error_str:
                    print(f"Dimension mismatch detected: {e}")
                    print(f"Recreating collection '{self.collection_name}' to match new embedding dimensions...")

                    # Delete the existing collection
                    client.delete_collection(collection_name=self.collection_name)

                    # Create a new collection with the correct dimensions
                    from qdrant_client.http.models import Distance, VectorParams
                    # Get the embedding dimension from the new embedding model
                    test_embedding = self.embedding_manager.embeddings.embed_query("test")
                    embedding_size = len(test_embedding)
                    print(f"Creating new Qdrant collection '{self.collection_name}' with embedding size: {embedding_size}")
                    client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE),
                    )

                    # Now try to initialize the vector store again
                    if QdrantClass.__name__ == 'QdrantVectorStore':
                        vector_store = QdrantClass(
                            client=client,
                            collection_name=self.collection_name,
                            embedding=self.embedding_manager.embeddings
                        )
                    else:
                        vector_store = QdrantClass(
                            client=client,
                            collection_name=self.collection_name,
                            embeddings=self.embedding_manager.embeddings
                        )
                else:
                    # Re-raise the exception if it's not a dimension mismatch
                    raise e

            return vector_store
        except ImportError:
            raise ImportError(
                "Please install Qdrant dependencies with: "
                "pip install qdrant-client langchain-qdrant"
            )
    
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
        elif self.store_type.lower() == "qdrant":
            if ids:
                self.vector_store.add_documents(documents=documents, ids=ids)
            else:
                self.vector_store.add_documents(documents=documents)
    
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
        elif self.store_type.lower() == "qdrant":
            return self.vector_store.similarity_search(
                query=query,
                k=top_k
            )
    
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
        elif self.store_type.lower() == "qdrant":
            return self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k
            )
    
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
        elif self.store_type.lower() == "qdrant":
            # Qdrant doesn't have a direct MMR implementation, so we'll use similarity search
            # and potentially implement MMR separately if needed
            return self.vector_store.similarity_search(
                query=query,
                k=top_k
            )
    
    def delete_collection(self):
        """Delete the entire collection from the vector store."""
        if self.store_type.lower() == "chroma":
            # Chroma doesn't have a direct way to delete a collection
            # We'll recreate the vector store to clear it
            self.vector_store = self._initialize_chroma()
        elif self.store_type.lower() == "qdrant":
            # Delete the collection in Qdrant
            from qdrant_client import QdrantClient
            import os

            # Get Qdrant config directly from environment to ensure latest values
            qdrant_url = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")
            qdrant_api_key = os.getenv("RAG_QDRANT_API_KEY", "")

            if qdrant_api_key:
                client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    prefer_grpc=False  # Use HTTP instead of gRPC to avoid auth issues
                )
            else:
                client = QdrantClient(
                    url=qdrant_url,
                    prefer_grpc=False  # Use HTTP instead of gRPC to avoid auth issues
                )

            # Drop the collection
            client.delete_collection(collection_name=self.collection_name)

            # Recreate the vector store
            self.vector_store = self._initialize_qdrant()
    
    def persist(self):
        """Persist the vector store to disk (Chroma handles this automatically)."""
        if self.store_type.lower() == "chroma":
            # Chroma persists automatically, but we can force a sync if needed
            pass
        elif self.store_type.lower() == "faiss":
            # Implementation for FAISS would go here
            pass
        elif self.store_type.lower() == "qdrant":
            # Qdrant persists automatically to its storage
            pass
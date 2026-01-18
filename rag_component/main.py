"""
Main RAG orchestrator module.
Coordinates all RAG components and provides a unified interface.
"""
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document as LCDocument
from .document_loader import DocumentLoader
from .embedding_manager import EmbeddingManager
from .vector_store_manager import VectorStoreManager
from .retriever import Retriever
from .rag_chain import RAGChain
from .config import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP
from langchain.text_splitter import RecursiveCharacterTextSplitter


class RAGOrchestrator:
    """Main class that orchestrates all RAG components."""

    def __init__(self, llm=None):
        """
        Initialize the RAG orchestrator.

        Args:
            llm: Language model to use for generation (will be passed to RAGChain)
        """
        self.document_loader = DocumentLoader()
        self.embedding_manager = EmbeddingManager()
        self.vector_store_manager = VectorStoreManager()
        self.retriever = Retriever(self.vector_store_manager)
        self.rag_chain = RAGChain(self.retriever, llm)

        # Initialize text splitter for document preprocessing
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAG_CHUNK_SIZE,
            chunk_overlap=RAG_CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )

    def ingest_documents(self, file_paths: List[str], preprocess: bool = True) -> bool:
        """
        Ingest documents into the vector store.

        Args:
            file_paths: List of file paths to ingest
            preprocess: Whether to split documents into chunks

        Returns:
            True if ingestion was successful
        """
        try:
            all_docs = []

            for file_path in file_paths:
                docs = self.document_loader.load_document(file_path)

                if preprocess:
                    # Split documents into chunks
                    docs = self.text_splitter.split_documents(docs)

                all_docs.extend(docs)

            # Add documents to vector store
            self.vector_store_manager.add_documents(all_docs)

            return True
        except Exception as e:
            print(f"Error ingesting documents: {str(e)}")
            return False

    def ingest_documents_from_directory(self, directory_path: str, preprocess: bool = True) -> bool:
        """
        Ingest all supported documents from a directory.

        Args:
            directory_path: Path to directory containing documents
            preprocess: Whether to split documents into chunks

        Returns:
            True if ingestion was successful
        """
        try:
            docs = self.document_loader.load_documents_from_directory(directory_path)

            if preprocess:
                # Split documents into chunks
                docs = self.text_splitter.split_documents(docs)

            # Add documents to vector store
            self.vector_store_manager.add_documents(docs)

            return True
        except Exception as e:
            print(f"Error ingesting documents from directory: {str(e)}")
            return False

    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query using the RAG pipeline.

        Args:
            user_query: User's natural language query

        Returns:
            Dictionary containing response and relevant context
        """
        return self.rag_chain.get_context_and_response(user_query)

    def retrieve_documents(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query without generating a response.

        Args:
            query: Query to search for
            top_k: Number of top results to return

        Returns:
            List of relevant documents with metadata and scores
        """
        return self.retriever.get_relevant_documents(query)

    def update_llm(self, llm):
        """
        Update the language model used by the RAG chain.

        Args:
            llm: New language model instance
        """
        self.rag_chain = RAGChain(self.retriever, llm)
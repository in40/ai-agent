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

                # Add source metadata to each document if not already present
                import os
                for doc in docs:
                    if not doc.metadata.get("source"):
                        # Use the original filename as the source, preserving full name with non-Latin characters
                        doc.metadata["source"] = os.path.basename(file_path)
                    if not doc.metadata.get("title"):
                        # Use the original filename as the title
                        doc.metadata["title"] = os.path.basename(file_path)
                    # Label the source as coming from local ingestion
                    if not doc.metadata.get("upload_method"):
                        doc.metadata["upload_method"] = "Local"

                all_docs.extend(docs)

            # Add documents to vector store
            self.vector_store_manager.add_documents(all_docs)

            return True
        except Exception as e:
            print(f"Error ingesting documents: {str(e)}")
            return False

    def ingest_documents_from_upload(self, file_paths: List[str], original_filenames: List[str], preprocess: bool = True) -> bool:
        """
        Ingest documents from web uploads into the vector store, preserving original filenames.

        Args:
            file_paths: List of temporary file paths to ingest
            original_filenames: List of original filenames from the upload
            preprocess: Whether to split documents into chunks

        Returns:
            True if ingestion was successful
        """
        try:
            from .file_storage_manager import FileStorageManager
            import os

            print(f"DEBUG: Starting ingestion for {len(file_paths)} files")
            print(f"DEBUG: File paths: {file_paths}")
            print(f"DEBUG: Original filenames: {original_filenames}")

            # Initialize file storage manager
            file_storage_manager = FileStorageManager()

            # Store the original files with their original filenames preserved
            stored_file_paths = file_storage_manager.store_files(file_paths, original_filenames)
            print(f"DEBUG: Stored file paths: {stored_file_paths}")

            all_docs = []

            for i, (file_path, original_filename, stored_file_path) in enumerate(zip(file_paths, original_filenames, stored_file_paths)):
                print(f"DEBUG: Processing file {i+1}/{len(file_paths)}: {original_filename}")
                print(f"DEBUG: File path: {file_path}")
                print(f"DEBUG: Stored file path: {stored_file_path}")

                docs = self.document_loader.load_document(file_path)
                print(f"DEBUG: Loaded {len(docs)} documents from {original_filename}")

                if preprocess:
                    # Split documents into chunks
                    docs = self.text_splitter.split_documents(docs)
                    print(f"DEBUG: After preprocessing, {len(docs)} documents for {original_filename}")

                # Add source metadata to each document using original filename
                for doc in docs:
                    # Use the original filename as both source and title for web uploads
                    doc.metadata["source"] = original_filename
                    doc.metadata["title"] = original_filename
                    # Label the source as coming from web upload
                    doc.metadata["upload_method"] = "Web upload"
                    # Add the stored file path for download capability
                    doc.metadata["stored_file_path"] = stored_file_path
                    # Extract the unique ID from the stored file path (the directory name)
                    stored_dir = os.path.dirname(stored_file_path)
                    doc.metadata["file_id"] = os.path.basename(stored_dir)

                all_docs.extend(docs)
                print(f"DEBUG: Total docs accumulated: {len(all_docs)}")

            print(f"DEBUG: Adding {len(all_docs)} total documents to vector store")

            # Add documents to vector store
            self.vector_store_manager.add_documents(all_docs)

            # Clean up temporary files after successful storage
            file_storage_manager.cleanup_temp_files(file_paths)
            print(f"DEBUG: Completed ingestion for all {len(file_paths)} files")

            return True
        except Exception as e:
            print(f"Error ingesting uploaded documents: {str(e)}")
            import traceback
            traceback.print_exc()
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

            # Add source metadata to each document if not already present
            import os
            for doc in docs:
                # Update source to use just the filename for consistency
                if doc.metadata.get("source"):
                    # Change source from full path to just the filename, preserving non-Latin characters
                    doc.metadata["source"] = os.path.basename(doc.metadata["source"])

                # If title is not set but source is, use the source as title
                if not doc.metadata.get("title") and doc.metadata.get("source"):
                    doc.metadata["title"] = doc.metadata["source"]

                # Label the source as coming from local ingestion
                if not doc.metadata.get("upload_method"):
                    doc.metadata["upload_method"] = "Local"

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
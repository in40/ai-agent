"""
Main RAG orchestrator module.
Coordinates all RAG components and provides a unified interface.
"""
import os
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document as LCDocument
from .document_loader import DocumentLoader
from .embedding_manager import EmbeddingManager
from .vector_store_manager import VectorStoreManager
from .retriever import Retriever
from .rag_chain import RAGChain
from .reranker import Reranker
from .config import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, RERANKER_ENABLED
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
        self.reranker = Reranker() if RERANKER_ENABLED else None

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
            import traceback
            traceback.print_exc()
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

                # Load the document, which will handle PDF processing with timeouts and fallbacks
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
        # Use retrieve_documents_with_scores to respect the top_k parameter
        docs_with_scores = self.retriever.retrieve_documents_with_scores(query, top_k=top_k)

        # Apply the same formatting as get_relevant_documents but with the specified top_k
        formatted_docs = []
        for doc, score in docs_with_scores:
            if score >= self.retriever.similarity_threshold:
                # Determine the source label based on upload method
                upload_method = doc.metadata.get("upload_method", "")

                # Update upload method labels to be more specific
                if upload_method == "Web upload":
                    source_label = "Client upload"
                elif upload_method == "Local":
                    source_label = "Local"
                elif upload_method == "Processed JSON Import":
                    source_label = "Processed JSON Upload"
                else:
                    # Default to Unknown if no upload method is specified
                    source_label = "Unknown"

                # Add ChromaDB collection name to the source label
                collection_name = self.vector_store_manager.collection_name if hasattr(self.vector_store_manager, 'collection_name') else "default"
                source_label = f"{source_label} [Collection: {collection_name}]"

                # Prepare document info for download if available
                download_info = None
                if doc.metadata.get("file_id") and doc.metadata.get("stored_file_path"):
                    download_info = {
                        "file_id": doc.metadata.get("file_id"),
                        "filename": os.path.basename(doc.metadata.get("stored_file_path", "")),
                        "download_available": True
                    }

                formatted_docs.append({
                    "content": doc.page_content,
                    "title": doc.metadata.get("title", "Untitled Document"),
                    "source": source_label,
                    "metadata": doc.metadata,
                    "score": score,
                    "download_info": download_info
                })

        # If reranker is enabled, re-rank the documents
        # COMMENTED OUT AS REQUESTED: Reranking is now handled separately in the enhancement phase
        # if self.reranker and formatted_docs:
        #     formatted_docs = self.reranker.rerank_documents(query, formatted_docs, top_k=top_k)

        return formatted_docs

    def update_llm(self, llm):
        """
        Update the language model used by the RAG chain.

        Args:
            llm: New language model instance
        """
        self.rag_chain = RAGChain(self.retriever, llm)

    def process_search_results_with_download(self, search_results: List[Dict[str, Any]], user_query: str) -> List[Dict[str, Any]]:
        """
        Process search results by downloading content from each result using MCP download tool,
        summarizing the content taking into account the original user query, and then reranking
        the summaries to return the top results.

        Args:
            search_results: List of search results with title, url, and description
            user_query: Original user query for context

        Returns:
            List of processed and ranked results with summaries
        """
        try:
            # Import required components
            from models.dedicated_mcp_model import DedicatedMCPModel
            from rag_component.config import RERANK_TOP_K_RESULTS
            from config.settings import str_to_bool
            import os
            import concurrent.futures
            from functools import partial

            mcp_model = DedicatedMCPModel()

            # Get available download services
            from registry.registry_client import ServiceRegistryClient
            from config.settings import MCP_REGISTRY_URL
            registry_client = ServiceRegistryClient(MCP_REGISTRY_URL)
            download_services = [s for s in registry_client.discover_services() if s.type == "mcp_download"]

            if not download_services:
                print("[RAG WARNING] No download MCP services available")
                # Return search results as summaries without downloading
                processed_results = []
                for result in search_results:
                    processed_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "summary": result.get("description", ""),
                        "original_description": result.get("description", ""),
                        "relevance_score": 0.5  # Default score
                    })
                # Sort by default score and return top K
                sorted_results = sorted(processed_results, key=lambda x: x['relevance_score'], reverse=True)
                return sorted_results[:RERANK_TOP_K_RESULTS]

            download_service = download_services[0]

            # Get parallelism setting from environment
            parallelism = int(os.getenv('PARRALELISM', 4))

            # Function to download content for a single result
            def download_single_result(result_tuple):
                idx, result = result_tuple
                url = result.get("url", "")
                title = result.get("title", "")
                description = result.get("description", "")

                if not url:
                    print(f"[RAG WARNING] No URL found for result {idx}, skipping")
                    return None

                print(f"[RAG INFO] Processing result {idx+1}/{len(search_results)}: {title}")

                # Download content using MCP download service
                download_params = {"url": url}
                download_result = mcp_model._call_mcp_service(
                    {
                        "id": download_service.id,
                        "host": download_service.host,
                        "port": download_service.port,
                        "type": download_service.type,
                        "metadata": download_service.metadata
                    },
                    "download",
                    download_params
                )

                return {
                    "idx": idx,
                    "result": result,
                    "url": url,
                    "title": title,
                    "description": description,
                    "download_result": download_result
                }

            # Function to summarize downloaded content
            def summarize_content(download_data):
                idx = download_data["idx"]
                result = download_data["result"]
                url = download_data["url"]
                title = download_data["title"]
                description = download_data["description"]
                download_result = download_data["download_result"]

                if download_result.get("status") == "success":
                    # Get the downloaded content
                    downloaded_content = ""
                    file_path = download_result.get("result", {}).get("file_path", "")

                    if file_path and os.path.exists(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                downloaded_content = f.read()
                        except Exception as e:
                            print(f"[RAG WARNING] Error reading downloaded file {file_path}: {str(e)}")
                            # If we can't read the file, try to get content from the description
                            downloaded_content = description

                    # Summarize the content in relation to the original user query
                    from models.response_generator import ResponseGenerator
                    response_generator = ResponseGenerator()

                    # Create a prompt to summarize the content in the context of the user's request
                    summary_prompt = f"""
                    Original user request: {user_query}

                    Content from webpage titled "{title}":
                    {downloaded_content[:4000]}  # Limit content to avoid exceeding token limits

                    Please provide a concise summary of this webpage content that is relevant to the user's original request.
                    Focus on information that directly addresses the user's question or need.
                    """

                    try:
                        summary = response_generator.generate_natural_language_response(summary_prompt)

                        # Return the summary with metadata
                        return {
                            "title": title,
                            "url": url,
                            "summary": summary,
                            "original_description": description,
                            "relevance_score": 0.0  # Will be calculated during reranking
                        }

                    except Exception as e:
                        print(f"[RAG WARNING] Error generating summary for {title}: {str(e)}")
                        # Return the result with the original description as fallback
                        return {
                            "title": title,
                            "url": url,
                            "summary": description,
                            "original_description": description,
                            "relevance_score": 0.0
                        }
                else:
                    print(f"[RAG WARNING] Failed to download content from {url}")
                    # Return the result with the original description as fallback
                    return {
                        "title": title,
                        "url": url,
                        "summary": description,
                        "original_description": description,
                        "relevance_score": 0.0
                    }

            # Prepare tuples of (index, result) for parallel processing
            indexed_results = [(idx, result) for idx, result in enumerate(search_results)]

            # Perform downloads in parallel
            download_results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
                # Submit all download tasks
                future_to_result = {executor.submit(download_single_result, item): item for item in indexed_results}

                # Collect download results as they complete
                for future in concurrent.futures.as_completed(future_to_result):
                    download_data = future.result()
                    if download_data is not None:
                        download_results.append(download_data)

            # Perform summarization in parallel for completed downloads
            processed_summaries = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
                # Submit all summarization tasks
                future_to_download = {executor.submit(summarize_content, download_data): download_data for download_data in download_results}

                # Collect summarization results as they complete
                for future in concurrent.futures.as_completed(future_to_download):
                    summary_result = future.result()
                    if summary_result is not None:
                        processed_summaries.append(summary_result)

            # Use the RAG MCP server for reranking all summaries at once
            try:
                # Discover available RAG services
                rag_services = [s for s in registry_client.discover_services() if s.type == "rag"]

                if not rag_services:
                    print("[RAG WARNING] No RAG MCP services available for reranking.")
                    # Set default scores for all processed summaries
                    for summary_obj in processed_summaries:
                        summary_obj['relevance_score'] = 0.5  # Default score
                else:
                    rag_service = rag_services[0]  # Use the first available RAG service

                    # Prepare documents for reranking - extract the summaries/content to be reranked
                    rerank_documents = []
                    for item in processed_summaries:
                        # Create a document-like structure for reranking
                        doc = {
                            'content': item.get('summary', ''),  # Use the LLM-generated summary
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'original_description': item.get('original_description', '')
                        }
                        rerank_documents.append(doc)

                    # Prepare parameters for the MCP rerank call
                    from rag_component.config import RERANK_TOP_K_RESULTS
                    rerank_params = {
                        "query": user_query,
                        "documents": rerank_documents,
                        "top_k": RERANK_TOP_K_RESULTS
                    }

                    # Call the RAG MCP server for reranking
                    rerank_result = mcp_model._call_mcp_service(
                        {
                            "id": rag_service.id,
                            "host": rag_service.host,
                            "port": rag_service.port,
                            "type": rag_service.type,
                            "metadata": rag_service.metadata
                        },
                        "rerank_documents",  # Action to perform
                        rerank_params
                    )

                    # Process the reranking results
                    if rerank_result.get("status") == "success":
                        reranked_results = rerank_result.get("result", {}).get("results", [])

                        # Update the processed summaries with reranking information
                        # Create a mapping of original results by URL for quick lookup
                        original_results_map = {item.get('url'): item for item in processed_summaries if item.get('url')}

                        reranked_processed_summaries = []
                        for reranked_doc in reranked_results:
                            url = reranked_doc.get('url', '')
                            # Find the original processed result that matches this reranked document
                            original_result = original_results_map.get(url)

                            if original_result:
                                # Update with reranking score and position
                                original_result['relevance_score'] = reranked_doc.get('score', 0.0)
                                original_result['reranked'] = True
                                reranked_processed_summaries.append(original_result)
                            else:
                                # If no original match found, create a new result with the reranked data
                                reranked_processed_summaries.append({
                                    'title': reranked_doc.get('title', ''),
                                    'url': reranked_doc.get('url', ''),
                                    'summary': reranked_doc.get('content', ''),
                                    'original_description': reranked_doc.get('original_description', ''),
                                    'relevance_score': reranked_doc.get('score', 0.0),
                                    'reranked': True
                                })

                        processed_summaries = reranked_processed_summaries
                    else:
                        print(f"[RAG WARNING] RAG MCP reranking failed: {rerank_result.get('error', 'Unknown error')}")
                        # Set default scores for all processed summaries
                        for summary_obj in processed_summaries:
                            summary_obj['relevance_score'] = 0.5  # Default score
            except Exception as e:
                print(f"[RAG WARNING] Error during MCP-based reranking: {str(e)}")
                # Set default scores for all processed summaries
                for summary_obj in processed_summaries:
                    summary_obj['relevance_score'] = 0.5  # Default score

            # Sort by relevance score in descending order and take top K
            sorted_summaries = sorted(processed_summaries, key=lambda x: x['relevance_score'], reverse=True)
            top_summaries = sorted_summaries[:RERANK_TOP_K_RESULTS]

            print(f"[RAG SUCCESS] Processed and reranked {len(processed_summaries)} results to top {len(top_summaries)}")

            return top_summaries

        except Exception as e:
            print(f"[RAG ERROR] Error processing search results with download: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return an empty list on error
            return []
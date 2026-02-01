#!/usr/bin/env python3
"""
RAG MCP Server - An MCP server that provides RAG (Retrieval-Augmented Generation) services
and registers itself with the service registry.
"""

# Load environment variables from .env file FIRST, before any other imports
from dotenv import dotenv_values
import os
import sys
from pathlib import Path

# Load environment variables using dotenv_values and update os.environ
env_vars = dotenv_values()
os.environ.update(env_vars)

# Explicitly set the Qdrant API key from the environment if available
if os.environ.get("RAG_QDRANT_API_KEY"):
    os.environ["QDRANT_API_KEY"] = os.environ["RAG_QDRANT_API_KEY"]

# Add the project root to the path so we can import from rag_component
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Force reload the config module to pick up the new environment variables
import importlib

# Import and reload the config module to ensure it picks up environment variables
import rag_component.config
importlib.reload(rag_component.config)

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path so we can import from rag_component
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag_component.main import RAGOrchestrator
from registry.registry_client import ServiceRegistryClient as RegistryClient, MCPServiceWrapper, ServiceInfo

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MCPServer.RAG')

class RAGRequestHandler:
    """Handler for RAG-related requests from the MCP framework."""
    
    def __init__(self, rag_orchestrator: RAGOrchestrator):
        self.rag_orchestrator = rag_orchestrator
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming RAG requests."""
        try:
            logger.info(f"Received RAG request: {request}")

            action = request.get("action")
            parameters = request.get("parameters", {})

            if action == "query" or action == "query_documents":
                return await self.query_documents(parameters)
            elif action == "ingest" or action == "ingest_documents":
                return await self.ingest_documents(parameters)
            elif action == "list_documents":
                return await self.list_documents(parameters)
            elif action == "rerank_documents":
                return await self.rerank_documents(parameters)
            elif action == "process_search_results_with_download":
                return await self.process_search_results_with_download(parameters)
            else:
                return {
                    "error": f"Unknown action: {action}",
                    "status": "error"
                }

        except Exception as e:
            logger.error(f"Error handling RAG request: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def query_documents(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Query documents using the RAG system."""
        try:
            query_text = parameters.get("query", "")
            # Use RAG_TOP_K_RESULTS from config as default if not provided in parameters
            from rag_component.config import RAG_TOP_K_RESULTS
            top_k = parameters.get("top_k", RAG_TOP_K_RESULTS)

            if not query_text:
                return {
                    "error": "Query text is required",
                    "status": "error"
                }

            # Perform document retrieval
            retrieved_docs = self.rag_orchestrator.retrieve_documents(query_text, top_k=top_k)

            # Format results
            results = []
            for doc in retrieved_docs:
                # Check if doc is a dictionary (returned by get_relevant_documents) or a Document object
                if isinstance(doc, dict):
                    # Handle dictionary format returned by get_relevant_documents
                    results.append({
                        "content": doc.get("content", ""),
                        "metadata": doc.get("metadata", {}),
                        "score": doc.get("score", None)
                    })
                else:
                    # Handle Document object format
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": getattr(doc, 'score', None)  # Some retrievers include scores
                    })

            return {
                "results": results,
                "count": len(results),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def ingest_documents(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest documents into the RAG system."""
        try:
            directory_path = parameters.get("directory_path", "")
            file_paths = parameters.get("file_paths", [])
            
            if directory_path:
                success = self.rag_orchestrator.ingest_documents_from_directory(directory_path)
            elif file_paths:
                success = self.rag_orchestrator.ingest_documents(file_paths)
            else:
                return {
                    "error": "Either directory_path or file_paths must be provided",
                    "status": "error"
                }
            
            if success:
                return {
                    "message": "Documents ingested successfully",
                    "status": "success"
                }
            else:
                return {
                    "error": "Failed to ingest documents",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Error ingesting documents: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def list_documents(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List available documents in the RAG system."""
        try:
            # This would depend on the specific vector store implementation
            # For ChromaDB, we can get the collection's contents
            # Note: This is a simplified implementation - in practice, you might need to store document metadata separately

            # For now, return a placeholder response since ChromaDB doesn't have a direct way to list documents
            # The documents are embedded and stored as vectors, not as raw documents
            # So we'll return a message indicating that documents have been ingested
            # In a real implementation, you'd want to maintain a separate document index

            # For now, we'll return a count of documents in the vector store
            # This requires accessing the vector store directly
            collection_count = self.rag_orchestrator.vector_store_manager.vector_store._collection.count()

            return {
                "documents": [],  # ChromaDB doesn't directly store original documents in an easily listable form
                "count": collection_count,
                "status": "success",
                "info": f"Vector store contains {collection_count} embeddings"
            }
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }

    async def rerank_documents(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Rerank documents using the reranker model."""
        try:
            query = parameters.get("query", "")
            documents = parameters.get("documents", [])
            top_k = parameters.get("top_k", len(documents))

            if not query:
                return {
                    "error": "Query is required for reranking",
                    "status": "error"
                }

            if not documents:
                return {
                    "error": "Documents are required for reranking",
                    "status": "error"
                }

            # Use the configured default top_k if not provided in parameters
            from rag_component.config import RERANK_TOP_K_RESULTS
            if top_k == len(documents):  # If top_k wasn't explicitly provided in parameters
                top_k = RERANK_TOP_K_RESULTS

            # Initialize the reranker with configuration from environment
            from rag_component.reranker import Reranker
            reranker = Reranker()

            # The reranker expects documents in a specific format, so we need to ensure they have the right structure
            # Convert documents to the expected format if needed
            formatted_docs = []
            for doc in documents:
                if isinstance(doc, dict):
                    # Ensure the document has all required fields for the reranker
                    formatted_doc = {
                        "content": doc.get("content", ""),
                        "title": doc.get("title", ""),
                        "source": doc.get("source", ""),
                        "metadata": doc.get("metadata", {}),
                        "score": doc.get("score", 0.0)
                    }
                    formatted_docs.append(formatted_doc)
                else:
                    # If it's not a dict, try to convert it
                    formatted_docs.append({
                        "content": str(doc),
                        "title": "",
                        "source": "",
                        "metadata": {},
                        "score": 0.0
                    })

            # Perform reranking
            reranked_docs = reranker.rerank_documents(query, formatted_docs, top_k=top_k)

            # Format results back to the expected output format
            results = []
            for doc in reranked_docs:
                results.append({
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("score", 0.0),
                    "reranked": doc.get("reranked", False)
                })

            return {
                "results": results,
                "count": len(results),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error reranking documents: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }

    async def process_search_results_with_download(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process search results with download and summarization."""
        try:
            search_results = parameters.get("search_results", [])
            user_query = parameters.get("user_query", "")

            if not search_results:
                return {
                    "error": "Search results are required",
                    "status": "error"
                }

            if not user_query:
                return {
                    "error": "User query is required",
                    "status": "error"
                }

            # Use the new method in the RAG orchestrator
            processed_results = self.rag_orchestrator.process_search_results_with_download(
                search_results=search_results,
                user_query=user_query
            )

            return {
                "results": processed_results,
                "count": len(processed_results),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error processing search results with download: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }


class RAGMCPServer:
    """MCP Server for RAG services."""

    def __init__(self, host="127.0.0.1", port=8091, registry_url="http://127.0.0.1:8080"):
        self.host = host
        self.port = port
        self.registry_url = registry_url
        self.registry_client = RegistryClient(registry_url)
        self.rag_orchestrator = None
        self.request_handler = None
        self.server = None
        self.service_wrapper = None
        self.running = False

    async def start(self):
        """Start the RAG MCP server."""
        try:
            logger.info(f"Initializing RAG MCP Server on {self.host}:{self.port}")

            # Initialize the RAG orchestrator with a dummy LLM initially
            # The actual LLM will be configured based on the application's settings
            from models.response_generator import ResponseGenerator
            try:
                response_gen = ResponseGenerator()
                llm = response_gen.llm
            except Exception:
                # If we can't get an LLM, we'll initialize with None and handle it in RAGOrchestrator
                llm = None

            self.rag_orchestrator = RAGOrchestrator(llm=llm)
            self.request_handler = RAGRequestHandler(self.rag_orchestrator)

            # Create service info for the registry
            # Use 127.0.0.1 instead of 0.0.0.0 for service registration since 0.0.0.0 is not a valid call address
            registration_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
            service_info = ServiceInfo(
                id=f"rag-server-{registration_host.replace('.', '-')}-{self.port}",
                host=registration_host,
                port=self.port,
                type="rag",
                metadata={
                    "name": "rag-service",
                    "description": "RAG (Retrieval-Augmented Generation) service for document retrieval and ingestion",
                    "protocol": "http",
                    "capabilities": [
                        {
                            "name": "query_documents",
                            "description": "Query documents using RAG",
                            "parameters": {
                                "query": {"type": "string", "required": True},
                                "top_k": {"type": "integer", "required": False}
                            }
                        },
                        {
                            "name": "ingest_documents",
                            "description": "Ingest documents into the RAG system",
                            "parameters": {
                                "directory_path": {"type": "string", "required": False},
                                "file_paths": {"type": "array", "items": {"type": "string"}, "required": False}
                            }
                        },
                        {
                            "name": "list_documents",
                            "description": "List available documents in the RAG system",
                            "parameters": {}
                        },
                        {
                            "name": "rerank_documents",
                            "description": "Rerank documents based on relevance to query",
                            "parameters": {
                                "query": {"type": "string", "required": True},
                                "documents": {"type": "array", "items": {"type": "object"}, "required": True},
                                "top_k": {"type": "integer", "required": False}
                            }
                        },
                        {
                            "name": "process_search_results_with_download",
                            "description": "Process search results by downloading content, summarizing, and reranking",
                            "parameters": {
                                "search_results": {"type": "array", "items": {"type": "object"}, "required": True},
                                "user_query": {"type": "string", "required": True}
                            }
                        }
                    ]
                }
            )

            # Create and start the service wrapper which handles registration and heartbeating
            self.service_wrapper = MCPServiceWrapper(
                service_info=service_info,
                registry_url=self.registry_url,
                heartbeat_interval=20,  # Send heartbeat every 20 seconds
                ttl=45  # TTL of 45 seconds (should be greater than heartbeat interval)
            )

            if not self.service_wrapper.start():
                logger.error("Failed to start service wrapper")
                raise Exception("Failed to start service wrapper")

            # Start the server (placeholder - actual implementation depends on your server framework)
            await self._start_server()

            self.running = True
            logger.info(f"RAG MCP Server listening on {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Error starting RAG MCP Server: {str(e)}", exc_info=True)
            raise

    async def _start_server(self):
        """Start the underlying server implementation."""
        # This is a placeholder - in a real implementation, you would use
        # an actual server framework like aiohttp, FastAPI, etc.
        # For now, we'll simulate a basic HTTP server using aiohttp

        from aiohttp import web

        async def handle_request(request):
            if request.method == 'POST':
                try:
                    data = await request.json()
                    response = await self.request_handler.handle_request(data)
                    return web.json_response(response)
                except Exception as e:
                    logger.error(f"Error handling request: {str(e)}", exc_info=True)
                    return web.json_response({
                        "error": str(e),
                        "status": "error"
                    })
            else:
                return web.json_response({
                    "error": "Only POST requests are supported",
                    "status": "error"
                })

        app = web.Application()
        # Add the main endpoint that handles all actions
        app.router.add_post('/', handle_request)

        # Add individual endpoints for each action to support different client approaches
        app.router.add_post('/query_documents', handle_request)
        app.router.add_post('/query', handle_request)
        app.router.add_post('/ingest_documents', handle_request)
        app.router.add_post('/ingest', handle_request)
        app.router.add_post('/list_documents', handle_request)
        app.router.add_post('/list', handle_request)
        app.router.add_post('/rerank_documents', handle_request)
        app.router.add_post('/process_search_results_with_download', handle_request)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        self.runner = runner  # Keep reference to prevent garbage collection

    async def stop(self):
        """Stop the RAG MCP server."""
        try:
            logger.info("Stopping RAG MCP Server...")

            # Stop the service wrapper which handles deregistration
            if self.service_wrapper:
                self.service_wrapper.stop()

            # Stop the server
            if hasattr(self, 'runner'):
                await self.runner.cleanup()

            self.running = False
            logger.info("RAG MCP Server stopped")

        except Exception as e:
            logger.error(f"Error stopping RAG MCP Server: {str(e)}", exc_info=True)
            raise


async def main():
    """Main entry point for the RAG MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG MCP Server - Provides RAG services to the MCP framework')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8091, help='Port to listen on (default: 8091)')
    parser.add_argument('--registry-url', type=str, default='http://127.0.0.1:8080', help='URL of the MCP registry server')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    server = RAGMCPServer(host=args.host, port=args.port, registry_url=args.registry_url)
    
    try:
        await server.start()
        
        # Keep the server running
        while server.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
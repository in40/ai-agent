"""Document Operation Handlers for MCP Server"""
import os
from typing import Dict, Any, List
from pathlib import Path
import config
from document_store_server.storage.file_storage import FileStorage
from document_store_server.storage.metadata_manager import MetadataManager
from document_store_server.storage.document_index import DocumentIndex


class DocumentHandlers:
    """Handlers for document operations"""
    
    def __init__(self):
        self.storage = FileStorage()
        self.metadata_manager = MetadataManager(config.INGESTED_DIR)
        self.index_manager = DocumentIndex(config.INGESTED_DIR)
    
    def handle_list_ingestion_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List all ingestion jobs.
        
        Returns:
            List of job information
        """
        try:
            jobs = self.storage.list_jobs()
            return {
                "success": True,
                "jobs": jobs,
                "total": len(jobs)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_list_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List documents for a job.
        
        Args:
            job_id: Ingestion job ID
            
        Returns:
            List of documents
        """
        try:
            job_id = params.get("job_id")
            
            if not job_id:
                return {
                    "success": False,
                    "error": "job_id is required"
                }
            
            if not self.storage.job_exists(job_id):
                return {
                    "success": False,
                    "error": f"Job {job_id} not found"
                }
            
            documents = self.storage.list_documents(job_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "documents": documents,
                "total": len(documents)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_get_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get document content.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            format: File format (txt, pdf, md, json)
            
        Returns:
            Document content and metadata
        """
        try:
            job_id = params.get("job_id")
            doc_id = params.get("doc_id")
            format = params.get("format", "txt")
            
            if not job_id or not doc_id:
                return {
                    "success": False,
                    "error": "job_id and doc_id are required"
                }
            
            # Get content (now returns dict with content, content_length, encoding for binary)
            content_result = self.storage.get_document(job_id, doc_id, format)

            if content_result is None:
                return {
                    "success": False,
                    "error": f"Document {doc_id} not found in job {job_id}"
                }

            # Get metadata
            metadata = self.metadata_manager.get_metadata(job_id, doc_id)

            # Handle both old format (direct string) and new format (dict)
            if isinstance(content_result, dict):
                # New format from updated storage
                return {
                    "success": True,
                    "job_id": job_id,
                    "doc_id": doc_id,
                    "format": format,
                    "content": content_result,  # Dict with content, content_length, encoding
                    "metadata": metadata,
                    "content_length": content_result.get('content_length', 0)
                }
            else:
                # Old format - direct string content
                return {
                    "success": True,
                    "job_id": job_id,
                    "doc_id": doc_id,
                    "format": format,
                    "content": content_result,
                    "metadata": metadata,
                    "content_length": len(content_result)
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_get_document_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get multiple documents.
        
        Args:
            job_id: Ingestion job ID
            doc_ids: List of document IDs
            format: File format (txt, pdf, md, json)
            
        Returns:
            List of document contents
        """
        try:
            job_id = params.get("job_id")
            doc_ids = params.get("doc_ids", [])
            format = params.get("format", "txt")
            
            if not job_id:
                return {
                    "success": False,
                    "error": "job_id is required"
                }
            
            if not doc_ids:
                return {
                    "success": False,
                    "error": "doc_ids is required"
                }
            
            # Limit batch size
            if len(doc_ids) > config.MAX_BATCH_SIZE:
                return {
                    "success": False,
                    "error": f"Batch size exceeds maximum of {config.MAX_BATCH_SIZE}"
                }
            
            documents = []
            errors = []
            
            for doc_id in doc_ids:
                content = self.storage.get_document(job_id, doc_id, format)
                
                if content is not None:
                    metadata = self.metadata_manager.get_metadata(job_id, doc_id)
                    documents.append({
                        "doc_id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "format": format
                    })
                else:
                    errors.append(f"Document {doc_id} not found")
            
            return {
                "success": True,
                "job_id": job_id,
                "documents": documents,
                "retrieved": len(documents),
                "not_found": len(errors),
                "errors": errors if errors else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_get_document_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get document metadata.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            
        Returns:
            Document metadata
        """
        try:
            job_id = params.get("job_id")
            doc_id = params.get("doc_id")
            
            if not job_id or not doc_id:
                return {
                    "success": False,
                    "error": "job_id and doc_id are required"
                }
            
            metadata = self.metadata_manager.get_metadata(job_id, doc_id)
            
            if metadata is None:
                return {
                    "success": False,
                    "error": f"Metadata not found for document {doc_id}"
                }
            
            return {
                "success": True,
                "job_id": job_id,
                "doc_id": doc_id,
                "metadata": metadata
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_search_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search within documents.
        
        Args:
            job_id: Ingestion job ID
            query: Search query
            limit: Maximum results
            
        Returns:
            Search results
        """
        try:
            job_id = params.get("job_id")
            query = params.get("query")
            limit = params.get("limit", config.SEARCH_RESULTS_LIMIT)
            
            if not job_id:
                return {
                    "success": False,
                    "error": "job_id is required"
                }
            
            if not query:
                return {
                    "success": False,
                    "error": "query is required"
                }
            
            # Search index
            results = self.index_manager.search_index(job_id, query, limit)
            
            # For each result, get a snippet from the content
            enriched_results = []
            for result in results:
                doc_id = result["doc_id"]
                
                # Get content snippet
                content = self.storage.get_document(job_id, doc_id, "txt")
                snippet = None
                if content:
                    # Find query in content and extract snippet
                    query_lower = query.lower()
                    content_lower = content.lower()
                    idx = content_lower.find(query_lower)
                    
                    if idx >= 0:
                        start = max(0, idx - 100)
                        end = min(len(content), idx + len(query) + 100)
                        snippet = content[start:end]
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet = snippet + "..."
                    else:
                        snippet = content[:200] + "..." if len(content) > 200 else content
                
                enriched_results.append({
                    "doc_id": doc_id,
                    "metadata": result.get("metadata", {}),
                    "snippet": snippet
                })
            
            return {
                "success": True,
                "job_id": job_id,
                "query": query,
                "results": enriched_results,
                "total": len(enriched_results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_delete_job_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete all documents for a job.
        
        Args:
            job_id: Ingestion job ID
            
        Returns:
            Deletion result
        """
        try:
            job_id = params.get("job_id")
            
            if not job_id:
                return {
                    "success": False,
                    "error": "job_id is required"
                }
            
            # Count documents before deletion
            documents = self.storage.list_documents(job_id)
            count = len(documents)
            
            if count == 0:
                return {
                    "success": True,
                    "job_id": job_id,
                    "deleted_count": 0,
                    "message": "No documents to delete"
                }
            
            # Delete documents
            deleted = self.storage.delete_job_documents(job_id)
            
            # Delete index
            self.index_manager.delete_job_index(job_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "deleted_count": deleted,
                "message": f"Deleted {deleted} documents for job {job_id}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_store_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a new document.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            content: Document content
            format: File format (txt, pdf, md, json)
            metadata: Optional metadata
            
        Returns:
            Storage result
        """
        try:
            job_id = params.get("job_id")
            doc_id = params.get("doc_id")
            content = params.get("content")
            format = params.get("format", "txt")
            metadata = params.get("metadata", {})
            
            if not job_id or not doc_id or not content:
                return {
                    "success": False,
                    "error": "job_id, doc_id, and content are required"
                }
            
            # Check document size
            content_size_mb = len(content.encode('utf-8')) / (1024 * 1024)
            if content_size_mb > config.MAX_DOCUMENT_SIZE_MB:
                return {
                    "success": False,
                    "error": f"Document size ({content_size_mb:.2f}MB) exceeds maximum ({config.MAX_DOCUMENT_SIZE_MB}MB)"
                }
            
            # Save document
            path = self.storage.save_document(job_id, doc_id, content, format, metadata)
            
            # Add to index
            self.index_manager.add_document_to_index(job_id, doc_id, metadata)
            
            return {
                "success": True,
                "job_id": job_id,
                "doc_id": doc_id,
                "path": path,
                "size_bytes": len(content.encode('utf-8')),
                "format": format,
                "message": f"Document stored successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Create singleton instance
document_handlers = DocumentHandlers()

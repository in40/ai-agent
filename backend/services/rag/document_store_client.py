"""
Document Store MCP Client
Client for interacting with the Document Store MCP Server (port 3070)
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
import requests

logger = logging.getLogger(__name__)

# Document Store configuration
DOCUMENT_STORE_URL = os.getenv('DOCUMENT_STORE_URL', 'http://127.0.0.1:3070/mcp')
DOCUMENT_STORE_ENABLED = os.getenv('DOCUMENT_STORE_ENABLED', 'true').lower() == 'true'


class DocumentStoreClient:
    """Client for Document Store MCP Server operations"""

    def __init__(self, base_url: str = DOCUMENT_STORE_URL):
        self.base_url = base_url
        self.enabled = DOCUMENT_STORE_ENABLED
        self.request_id = 0

    def _call_mcp(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make an MCP JSON-RPC call to the Document Store.

        Args:
            method: MCP method name (e.g., 'tools/call', 'tools/list')
            params: Method parameters

        Returns:
            MCP response as dictionary
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Document Store client is disabled"
            }

        self.request_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }

        if params:
            payload["params"] = params

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                logger.error(f"MCP error: {result['error']}")
                return {
                    "success": False,
                    "error": result["error"].get("message", "Unknown MCP error")
                }

            # MCP returns result with content array containing text
            # Need to parse the inner JSON from the text content
            mcp_result = result.get("result", {})
            content_array = mcp_result.get("content", [])
            
            if content_array and len(content_array) > 0:
                text_content = content_array[0].get("text", "")
                try:
                    parsed_content = json.loads(text_content)
                    return {
                        "success": True,
                        "result": parsed_content
                    }
                except json.JSONDecodeError:
                    # If text is not JSON, return as is
                    return {
                        "success": True,
                        "result": {"text": text_content}
                    }
            else:
                return {
                    "success": True,
                    "result": mcp_result
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Document Store request failed: {str(e)}")
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MCP response: {str(e)}")
            return {
                "success": False,
                "error": f"Response parsing error: {str(e)}"
            }

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        return self._call_mcp("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

    # ==================== Document Store Tools ====================

    def list_ingestion_jobs(self) -> Dict[str, Any]:
        """
        List all ingestion jobs.

        Returns:
            List of jobs with metadata
        """
        logger.info("Listing ingestion jobs from Document Store")
        return self._call_tool("list_ingestion_jobs", {})

    def list_documents(self, job_id: str) -> Dict[str, Any]:
        """
        List documents for a specific job.

        Args:
            job_id: Ingestion job ID

        Returns:
            List of documents with metadata including source website
        """
        logger.info(f"Listing documents for job: {job_id}")
        return self._call_tool("list_documents", {"job_id": job_id})

    def list_documents_with_source(self, job_id: str) -> Dict[str, Any]:
        """
        List documents for a specific job with source website info.

        Args:
            job_id: Ingestion job ID

        Returns:
            List of documents with metadata including source website
        """
        logger.info(f"Listing documents with source for job: {job_id}")
        result = self._call_tool("list_documents", {"job_id": job_id})
        
        # Try to load source metadata if available
        if result.get('success'):
            import os
            import json
            metadata_file = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/{job_id}/documents/.source_metadata.json"
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r') as f:
                        source_meta = json.load(f)
                    # Add source info to result
                    result['source_website'] = source_meta.get('source_urls', ['unknown'])[0] if source_meta.get('source_urls') else 'unknown'
                    result['downloaded_at'] = source_meta.get('downloaded_at', 'unknown')
                except:
                    pass
        
        return result

    def get_document(self, job_id: str, doc_id: str, format: str = "txt") -> Dict[str, Any]:
        """
        Get document content.

        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            format: Document format (txt, pdf, md, json)

        Returns:
            Document content and metadata
        """
        logger.info(f"Getting document: {doc_id} from job: {job_id}")
        return self._call_tool("get_document", {
            "job_id": job_id,
            "doc_id": doc_id,
            "format": format
        })

    def get_document_batch(self, job_id: str, doc_ids: List[str], format: str = "txt") -> Dict[str, Any]:
        """
        Get multiple documents in batch.

        Args:
            job_id: Ingestion job ID
            doc_ids: List of document IDs
            format: Document format

        Returns:
            List of documents with content
        """
        logger.info(f"Getting batch of {len(doc_ids)} documents from job: {job_id}")
        return self._call_tool("get_document_batch", {
            "job_id": job_id,
            "doc_ids": doc_ids,
            "format": format
        })

    def get_document_metadata(self, job_id: str, doc_id: str) -> Dict[str, Any]:
        """
        Get document metadata.

        Args:
            job_id: Ingestion job ID
            doc_id: Document ID

        Returns:
            Document metadata
        """
        logger.info(f"Getting metadata for document: {doc_id} from job: {job_id}")
        return self._call_tool("get_document_metadata", {
            "job_id": job_id,
            "doc_id": doc_id
        })

    def search_documents(self, job_id: str, query: str, limit: int = 50) -> Dict[str, Any]:
        """
        Search within documents for a job.

        Args:
            job_id: Ingestion job ID
            query: Search query
            limit: Maximum results

        Returns:
            Search results with snippets
        """
        logger.info(f"Searching documents in job: {job_id} for query: {query}")
        return self._call_tool("search_documents", {
            "job_id": job_id,
            "query": query,
            "limit": limit
        })

    def store_document(self, job_id: str, doc_id: str, content: str,
                       format: str = "txt", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Store a new document.

        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            content: Document content
            format: Document format
            metadata: Optional metadata

        Returns:
            Storage result
        """
        logger.info(f"Storing document: {doc_id} in job: {job_id}")
        return self._call_tool("store_document", {
            "job_id": job_id,
            "doc_id": doc_id,
            "content": content,
            "format": format,
            "metadata": metadata or {}
        })

    def delete_job_documents(self, job_id: str) -> Dict[str, Any]:
        """
        Delete all documents for a job.

        Args:
            job_id: Ingestion job ID

        Returns:
            Deletion result
        """
        logger.info(f"Deleting all documents for job: {job_id}")
        return self._call_tool("delete_job_documents", {"job_id": job_id})

    # ==================== Helper Methods ====================

    def get_job_documents_with_content(self, job_id: str, format: str = "txt") -> Dict[str, Any]:
        """
        Get all documents for a job with their content.

        Args:
            job_id: Ingestion job ID
            format: Document format

        Returns:
            Documents with content and metadata
        """
        # First, list documents
        list_result = self.list_documents(job_id)
        if not list_result.get("success"):
            return list_result

        documents = list_result.get("documents", [])
        if not documents:
            return {
                "success": True,
                "job_id": job_id,
                "documents": [],
                "total": 0
            }

        # Get all document IDs
        doc_ids = [doc["doc_id"] for doc in documents]

        # Get batch content
        batch_result = self.get_document_batch(job_id, doc_ids, format)
        if not batch_result.get("success"):
            return batch_result

        return {
            "success": True,
            "job_id": job_id,
            "documents": batch_result.get("documents", []),
            "total": len(batch_result.get("documents", [])),
            "not_found": batch_result.get("not_found", 0)
        }

    def search_across_jobs(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """
        Search for documents across all jobs.

        Args:
            query: Search query
            limit: Maximum total results

        Returns:
            Aggregated search results
        """
        logger.info(f"Searching across all jobs for: {query}")

        # Get all jobs
        jobs_result = self.list_ingestion_jobs()
        if not jobs_result.get("success"):
            return jobs_result

        jobs = jobs_result.get("jobs", [])
        all_results = []

        # Search in each job
        for job in jobs:
            job_id = job.get("job_id")
            if job_id:
                search_result = self.search_documents(job_id, query, limit=limit // max(len(jobs), 1))
                if search_result.get("success"):
                    results = search_result.get("results", [])
                    for result in results:
                        result["job_id"] = job_id
                    all_results.extend(results)

        # Sort by relevance and limit
        all_results = all_results[:limit]

        return {
            "success": True,
            "query": query,
            "results": all_results,
            "total": len(all_results),
            "jobs_searched": len(jobs)
        }

    def is_available(self) -> bool:
        """
        Check if Document Store is available.

        Returns:
            True if Document Store is reachable
        """
        if not self.enabled:
            return False

        try:
            result = self._call_mcp("tools/list")
            return result.get("success", False)
        except Exception:
            return False


# Create singleton instance
document_store_client = DocumentStoreClient()

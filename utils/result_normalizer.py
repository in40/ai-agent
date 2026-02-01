"""
Utility functions to normalize results from different MCP services to a unified format.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


def normalize_mcp_result(result: Dict[str, Any], service_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Normalize an MCP service result to a unified format.
    
    Args:
        result: Raw result from an MCP service
        service_type: Type of service (e.g., 'search', 'rag', 'download', etc.)
        
    Returns:
        Normalized result in standard format
    """
    try:
        # Determine service type if not provided
        if service_type is None:
            service_type = infer_service_type(result)
        
        # Create base normalized structure
        normalized = {
            "id": result.get("id", result.get("_id", generate_result_id())),
            "content": "",
            "title": "",
            "url": "",
            "source": "Unknown source",
            "source_type": service_type,
            "relevance_score": result.get("score", result.get("relevance_score", result.get("relevance_score", 0.0))),
            "metadata": {
                "original_source_field": result.get("source", ""),
                "service_used": result.get("service_id", result.get("service", "")),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "raw_result": result  # Preserve original for debugging
            },
            "summary": "",
            "full_content_available": False
        }
        
        # Handle different service types with specific normalization
        if service_type == "search":
            normalized = _normalize_search_result(result, normalized)
        elif service_type == "rag":
            normalized = _normalize_rag_result(result, normalized)
        elif service_type == "download":
            normalized = _normalize_download_result(result, normalized)
        else:
            # Generic normalization for other service types
            normalized = _normalize_generic_result(result, normalized)
            
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing MCP result: {str(e)}")
        # Return a minimal normalized result even on error
        return {
            "id": generate_result_id(),
            "content": str(result) if isinstance(result, (str, int, float)) else repr(result),
            "title": "Error Processing Result",
            "url": "",
            "source": "Error Source",
            "source_type": service_type or "unknown",
            "relevance_score": 0.0,
            "metadata": {
                "original_source_field": "",
                "service_used": result.get("service_id", ""),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "raw_result": result,
                "error": str(e)
            },
            "summary": "Error occurred during result normalization",
            "full_content_available": False
        }


def _normalize_search_result(raw_result: Dict[str, Any], base_normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize search service results to unified format."""
    # Extract content from different possible locations in search results
    content = ""
    if "result" in raw_result and isinstance(raw_result["result"], dict):
        nested_result = raw_result["result"]
        if "result" in nested_result and isinstance(nested_result["result"], dict):
            # Double nested structure from search server
            search_data = nested_result["result"]
            if "results" in search_data and isinstance(search_data["results"], list):
                # Format search results as a summary
                search_results = search_data["results"]
                content_parts = []
                for res in search_results:
                    title = res.get("title", "No Title")
                    description = res.get("description", res.get("summary", res.get("content", "No description")))
                    url = res.get("url", "")
                    content_parts.append(f"Title: {title}\nURL: {url}\nDescription: {description}\n")
                content = "\n".join(content_parts)
        elif "results" in nested_result:
            # Single nested structure
            search_results = nested_result["results"]
            content_parts = []
            for res in search_results:
                title = res.get("title", "No Title")
                description = res.get("description", res.get("summary", res.get("content", "No description")))
                url = res.get("url", "")
                content_parts.append(f"Title: {title}\nURL: {url}\nDescription: {description}\n")
            content = "\n".join(content_parts)
    elif "results" in raw_result:
        # Direct structure
        search_results = raw_result["results"]
        content_parts = []
        for res in search_results:
            title = res.get("title", "No Title")
            description = res.get("description", res.get("summary", res.get("content", "No description")))
            url = res.get("url", "")
            content_parts.append(f"Title: {title}\nURL: {url}\nDescription: {description}\n")
        content = "\n".join(content_parts)
    
    # Extract title and URL from first result if available
    title = ""
    url = ""
    source = "Web Search"
    
    # Try to find the first result to extract title and URL
    if "result" in raw_result and isinstance(raw_result["result"], dict):
        nested_result = raw_result["result"]
        if "result" in nested_result and isinstance(nested_result["result"], dict):
            search_data = nested_result["result"]
            if "results" in search_data and search_data["results"]:
                first_res = search_data["results"][0]
                title = first_res.get("title", "Search Results")
                url = first_res.get("url", "")
        elif "results" in nested_result and nested_result["results"]:
            first_res = nested_result["results"][0]
            title = first_res.get("title", "Search Results")
            url = first_res.get("url", "")
    elif "results" in raw_result and raw_result["results"]:
        first_res = raw_result["results"][0]
        title = first_res.get("title", "Search Results")
        url = first_res.get("url", "")
    
    # Set source - try multiple locations
    # Prioritize meaningful source information from the actual search results over service ID
    source = "Web Search"

    # If we have individual search results, try to extract a more meaningful source
    # The search results may be nested in different structures depending on the service
    search_results = None

    # Try to find search results in the nested structure
    if "result" in raw_result and isinstance(raw_result["result"], dict):
        nested_result = raw_result["result"]
        if "result" in nested_result and isinstance(nested_result["result"], dict):
            # Double nested structure: {"result": {"result": {"results": [...]}}}
            double_nested = nested_result["result"]
            if "results" in double_nested and isinstance(double_nested["results"], list):
                search_results = double_nested["results"]
        elif "results" in nested_result and isinstance(nested_result["results"], list):
            # Single nested structure: {"result": {"results": [...]}}
            search_results = nested_result["results"]
    elif "results" in raw_result and isinstance(raw_result["results"], list):
        # Direct structure: {"results": [...]}
        search_results = raw_result["results"]

    # If we found search results, extract meaningful source information
    if search_results and len(search_results) > 0:
        if len(search_results) == 1:
            # If only one result, use its source information
            first_result = search_results[0]
            if first_result.get("url"):
                import urllib.parse
                parsed_url = urllib.parse.urlparse(first_result["url"])
                if parsed_url.netloc:
                    source = parsed_url.netloc
                else:
                    source = first_result.get("title", "Single Search Result")
            elif first_result.get("title"):
                source = first_result["title"]
            else:
                source = first_result.get("source", "Search Result")
        else:
            # Multiple results - we can create a more descriptive source
            # Extract domains from the URLs to show the sources of the search results
            domains = []
            for result in search_results:
                if result.get("url"):
                    import urllib.parse
                    parsed_url = urllib.parse.urlparse(result["url"])
                    if parsed_url.netloc:
                        domain = parsed_url.netloc
                        if domain not in domains:
                            domains.append(domain)

            if domains:
                if len(domains) == 1:
                    # All results from the same domain
                    source = domains[0]
                else:
                    # Multiple domains - show a representative sample
                    source = f"Search ({len(search_results)} results from {len(domains)} sources: {', '.join(domains[:3])})"
                    if len(domains) > 3:
                        source += "..."
            else:
                # No domains extracted, just indicate number of results
                source = f"Search ({len(search_results)} results)"

    # If still generic, fallback to service information
    if source == "Web Search":
        if raw_result.get("service_id"):
            source = raw_result["service_id"]
        elif raw_result.get("service"):
            source = raw_result["service"]

    base_normalized.update({
        "content": content,
        "title": title or "Search Results",
        "url": url,
        "source": source,
        "source_type": "web_search",
        "full_content_available": bool(content)
    })

    return base_normalized


def _normalize_rag_result(raw_result: Dict[str, Any], base_normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize RAG service results to unified format."""
    # Extract content from different possible locations
    content = raw_result.get("content", raw_result.get("page_content", raw_result.get("text", "")))
    
    # Extract title
    title = raw_result.get("title", "")
    if not title:
        # Try to get title from metadata
        metadata = raw_result.get("metadata", {})
        title = metadata.get("title", metadata.get("source", "RAG Document"))
    
    # Extract URL if available
    url = raw_result.get("url", "")
    if not url:
        metadata = raw_result.get("metadata", {})
        url = metadata.get("url", metadata.get("stored_file_path", metadata.get("file_path", "")))
    
    # Extract source - prioritize metadata.source
    source = "RAG Document"
    metadata = raw_result.get("metadata", {})
    if metadata and metadata.get("source"):
        source = metadata["source"]
    elif raw_result.get("source"):
        source = raw_result["source"]
    elif metadata.get("file_path") or metadata.get("stored_file_path"):
        # Use filename from path as source
        import os
        path = metadata.get("file_path", metadata.get("stored_file_path", ""))
        if path:
            source = os.path.basename(path)
    
    # Extract relevance score
    relevance_score = raw_result.get("score", raw_result.get("relevance_score", raw_result.get("relevance_score", 0.0)))

    normalized_result = {
        **base_normalized,
        "content": content,
        "title": title,
        "url": url,
        "source": source,
        "source_type": "local_document",
        "relevance_score": relevance_score,
        "full_content_available": bool(content)
    }

    return normalized_result


def _normalize_download_result(raw_result: Dict[str, Any], base_normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize download service results to unified format."""
    content = ""
    title = "Download Result"
    url = ""
    source = "Download Service"
    
    # Extract content from result
    if raw_result.get("status") == "success":
        result_data = raw_result.get("result", {})
        if isinstance(result_data, dict):
            # Common structure for download results
            if "result" in result_data:
                download_result = result_data["result"]
                if isinstance(download_result, dict) and "file_path" in download_result:
                    content = f"Successfully downloaded content to: {download_result['file_path']}"
                    source = download_result["file_path"]
                    url = download_result.get("url", "")
            elif "file_path" in result_data:
                content = f"Successfully downloaded content to: {result_data['file_path']}"
                source = result_data["file_path"]
                url = result_data.get("url", "")
        else:
            # If result_data is not a dict, use it as content
            content = str(result_data)
    else:
        # Handle error case
        content = f"Download failed: {raw_result.get('error', 'Unknown error')}"
        source = "Download Service (Error)"
    
    base_normalized.update({
        "content": content,
        "title": title,
        "url": url,
        "source": source,
        "source_type": "download_result",
        "full_content_available": bool(content)
    })
    
    return base_normalized


def _normalize_generic_result(raw_result: Dict[str, Any], base_normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Generic normalization for other service types."""
    # Try to extract meaningful content from the raw result
    content = str(raw_result) if not isinstance(raw_result, (dict, list)) else ""
    
    if isinstance(raw_result, dict):
        # Look for common content fields
        content = raw_result.get("content", "")
        if not content:
            content = raw_result.get("result", "")
            if isinstance(content, dict):
                content = str(content)
            elif content is None:
                content = ""
    
    title = raw_result.get("title", "Generic Result")
    url = raw_result.get("url", "")
    
    # Determine source
    source = "Generic Service"
    if raw_result.get("service_id"):
        source = raw_result["service_id"]
    elif raw_result.get("service"):
        source = raw_result["service"]
    elif raw_result.get("source"):
        source = raw_result["source"]
    
    base_normalized.update({
        "content": content,
        "title": title,
        "url": url,
        "source": source,
        "full_content_available": bool(content)
    })
    
    return base_normalized


def infer_service_type(result: Dict[str, Any]) -> str:
    """Infer service type from result structure."""
    service_id = result.get("service_id", result.get("service", "")).lower()
    
    if "search" in service_id or "web" in service_id or "brave" in service_id:
        return "search"
    elif "rag" in service_id or "vector" in service_id or "query_documents" in result.get("action", ""):
        return "rag"
    elif "download" in service_id or "file" in service_id:
        return "download"
    elif "sql" in service_id or "database" in service_id:
        return "sql"
    elif "dns" in service_id:
        return "dns"
    else:
        return "generic"


def generate_result_id() -> str:
    """Generate a unique ID for a result."""
    return str(uuid.uuid4())


def normalize_mcp_results_list(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of MCP service results to unified format.
    
    Args:
        results: List of raw results from MCP services
        
    Returns:
        List of normalized results
    """
    normalized_results = []
    
    for result in results:
        service_type = infer_service_type(result)
        normalized = normalize_mcp_result(result, service_type)
        normalized_results.append(normalized)
    
    return normalized_results


def normalize_rag_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize a list of RAG documents to unified format.
    
    Args:
        documents: List of raw RAG documents
        
    Returns:
        List of normalized documents
    """
    normalized_docs = []
    
    for doc in documents:
        # For RAG documents, we treat them as RAG type
        normalized = normalize_mcp_result(doc, "rag")
        # Ensure they're properly marked as local documents
        normalized["source_type"] = "local_document"
        normalized_docs.append(normalized)
    
    return normalized_docs
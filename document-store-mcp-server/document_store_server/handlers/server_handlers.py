"""Server Handlers for Document Store MCP Server"""
from typing import Dict, Any, List
from document_store_server.handlers.document_handlers import document_handlers


class DocumentStoreServerHandlers:
    """MCP Server Handlers for Document Store"""
    
    def __init__(
        self,
        enable_registry: bool = True,
        notification_manager = None
    ):
        self.enable_registry = enable_registry
        self.notification_manager = notification_manager
        
        # Define MCP tools
        self.tools = [
            {
                "name": "list_ingestion_jobs",
                "description": "List all document ingestion jobs with their document counts and creation dates",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_documents",
                "description": "List all documents for a specific ingestion job, including metadata",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Ingestion job ID"
                        }
                    },
                    "required": ["job_id"]
                }
            },
            {
                "name": "get_document",
                "description": "Get full content of a specific document in txt, pdf, md, or json format",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Ingestion job ID"
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "Document ID"
                        },
                        "format": {
                            "type": "string",
                            "description": "File format (txt, pdf, md, json)",
                            "default": "txt",
                            "enum": ["txt", "pdf", "md", "json"]
                        }
                    },
                    "required": ["job_id", "doc_id"]
                }
            },
            {
                "name": "get_document_batch",
                "description": "Get multiple documents in a single call (up to 100 documents)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Ingestion job ID"
                        },
                        "doc_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of document IDs to retrieve"
                        },
                        "format": {
                            "type": "string",
                            "description": "File format (txt, pdf, md, json)",
                            "default": "txt"
                        }
                    },
                    "required": ["job_id", "doc_ids"]
                }
            },
            {
                "name": "get_document_metadata",
                "description": "Get metadata for a specific document",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Ingestion job ID"
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "Document ID"
                        }
                    },
                    "required": ["job_id", "doc_id"]
                }
            },
            {
                "name": "search_documents",
                "description": "Search within documents for a job using text search",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Ingestion job ID"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query string"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 50)",
                            "default": 50
                        }
                    },
                    "required": ["job_id", "query"]
                }
            },
            {
                "name": "delete_job_documents",
                "description": "Delete all documents and index for a specific job",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Ingestion job ID"
                        }
                    },
                    "required": ["job_id"]
                }
            },
            {
                "name": "store_document",
                "description": "Store a new document with optional metadata",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Ingestion job ID"
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "Document ID"
                        },
                        "content": {
                            "type": "string",
                            "description": "Document content"
                        },
                        "format": {
                            "type": "string",
                            "description": "File format (txt, pdf, md, json)",
                            "default": "txt"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata dictionary"
                        }
                    },
                    "required": ["job_id", "doc_id", "content"]
                }
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return self.tools
    
    async def handle_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool execution.
        
        Args:
            name: Tool name
            params: Tool parameters
            
        Returns:
            Tool execution result
        """
        handler_map = {
            "list_ingestion_jobs": document_handlers.handle_list_ingestion_jobs,
            "list_documents": document_handlers.handle_list_documents,
            "get_document": document_handlers.handle_get_document,
            "get_document_batch": document_handlers.handle_get_document_batch,
            "get_document_metadata": document_handlers.handle_get_document_metadata,
            "search_documents": document_handlers.handle_search_documents,
            "delete_job_documents": document_handlers.handle_delete_job_documents,
            "store_document": document_handlers.handle_store_document
        }
        
        handler = handler_map.get(name)
        
        if not handler:
            return {
                "success": False,
                "error": f"Unknown tool: {name}"
            }
        
        try:
            return handler(params)
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }

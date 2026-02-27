"""
NLP Server Handlers
Implements MCP tools for entity extraction and NLP analysis
"""
from typing import Dict, Any, List, Optional
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_tools.entity_extractor import EntityExtractor, get_entity_extractor
from nlp_tools.llm_entity_extractor import LLMEntityExtractor, get_llm_entity_extractor


class NlpServerHandlers:
    """Handles all NLP-related MCP methods"""
    
    def __init__(self):
        # Initialize entity extractors
        self.entity_extractor = get_entity_extractor("en_core_web_sm")
        self.llm_extractor = get_llm_entity_extractor(
            base_url="http://192.168.51.237:1234/v1",
            model="qwen3-4b"
        )
        
        # Define NLP tools
        self.tools: List[Dict[str, Any]] = [
            {
                "name": "extract_entities",
                "description": "Extract named entities from text using NLP (spaCy + pattern matching). Returns entities with types, positions, and confidence scores.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze for entities"
                        },
                        "use_spacy": {
                            "type": "boolean",
                            "description": "Use spaCy for NER (default: true)",
                            "default": True
                        },
                        "use_nltk": {
                            "type": "boolean",
                            "description": "Use NLTK for NER (default: false)",
                            "default": False
                        },
                        "use_patterns": {
                            "type": "boolean",
                            "description": "Use regex patterns for standards (default: true)",
                            "default": True
                        },
                        "extract_technologies": {
                            "type": "boolean",
                            "description": "Extract technical terms (default: true)",
                            "default": True
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "extract_entities_llm",
                "description": "Extract named entities using LLM (LM Studio). Better for domain-specific entities and context understanding.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze for entities"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum text length (default: 4000)",
                            "default": 4000
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "analyze_document",
                "description": "Comprehensive document analysis with entity extraction, statistics, and entity grouping by type.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Document text to analyze"
                        },
                        "method": {
                            "type": "string",
                            "description": "Extraction method: 'spacy', 'llm', or 'both'",
                            "enum": ["spacy", "llm", "both"],
                            "default": "spacy"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "filter_entities",
                "description": "Filter extracted entities by type (e.g., keep only STANDARD or ORGANIZATION entities).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entities": {
                            "type": "array",
                            "description": "List of entity dictionaries from extract_entities",
                            "items": {
                                "type": "object"
                            }
                        },
                        "entity_types": {
                            "type": "array",
                            "description": "List of entity types to keep (e.g., ['STANDARD', 'ORGANIZATION'])",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["entities", "entity_types"]
                }
            },
            {
                "name": "get_entity_types",
                "description": "Get list of all available entity types with descriptions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "compare_extraction_methods",
                "description": "Compare entity extraction results between spaCy and LLM methods.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "extract_standards",
                "description": "Extract technical standards (GOST, ISO, IEC, RFC) from text using pattern matching.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to search for standards"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "get_entity_statistics",
                "description": "Get statistics about extracted entities (counts by type, total, etc.).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entities": {
                            "type": "array",
                            "description": "List of entity dictionaries",
                            "items": {
                                "type": "object"
                            }
                        }
                    },
                    "required": ["entities"]
                }
            }
        ]
        
        # Resources (passive data)
        self.resources: List[Dict[str, Any]] = [
            {
                "uri": "nlp://entity-types",
                "name": "Available Entity Types",
                "description": "List of all entity types supported by this server"
            },
            {
                "uri": "nlp://extraction-methods",
                "name": "Entity Extraction Methods",
                "description": "Documentation of available extraction methods (spaCy, NLTK, LLM, patterns)"
            }
        ]
        
        # Prompts (template-based)
        self.prompts: List[Dict[str, Any]] = [
            {
                "name": "entity_extraction_prompt",
                "description": "Prompt template for entity extraction with custom entity types",
                "arguments": [
                    {
                        "name": "text",
                        "type": "string",
                        "description": "Text to analyze"
                    },
                    {
                        "name": "entity_types",
                        "type": "array",
                        "description": "Custom entity types to extract",
                        "items": {"type": "string"}
                    }
                ]
            },
            {
                "name": "document_analysis_prompt",
                "description": "Prompt template for comprehensive document analysis",
                "arguments": [
                    {
                        "name": "document",
                        "type": "string",
                        "description": "Document to analyze"
                    },
                    {
                        "name": "focus",
                        "type": "string",
                        "description": "Analysis focus (e.g., 'standards', 'technologies', 'organizations')"
                    }
                ]
            }
        ]
    
    def register_handlers(self, rpc_handler):
        """Register all NLP handlers with RPC handler"""
        # Tool methods
        rpc_handler.register_request_handler('tools/list', self.handle_tools_list)
        rpc_handler.register_request_handler('tools/call', self.handle_tools_call)
        
        # Resource methods
        rpc_handler.register_request_handler('resources/list', self.handle_resources_list)
        rpc_handler.register_request_handler('resources/read', self.handle_resources_read)
        
        # Prompt methods
        rpc_handler.register_request_handler('prompts/list', self.handle_prompts_list)
        rpc_handler.register_request_handler('prompts/get', self.handle_prompts_get)
    
    # Tool handlers
    def handle_tools_list(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "tools": self.tools
        }
    
    def handle_tools_call(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "extract_entities":
            return self._call_extract_entities(arguments)
        elif tool_name == "extract_entities_llm":
            return self._call_extract_entities_llm(arguments)
        elif tool_name == "analyze_document":
            return self._call_analyze_document(arguments)
        elif tool_name == "filter_entities":
            return self._call_filter_entities(arguments)
        elif tool_name == "get_entity_types":
            return self._call_get_entity_types(arguments)
        elif tool_name == "compare_extraction_methods":
            return self._call_compare_extraction_methods(arguments)
        elif tool_name == "extract_standards":
            return self._call_extract_standards(arguments)
        elif tool_name == "get_entity_statistics":
            return self._call_get_entity_statistics(arguments)
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            }
    
    def _call_extract_entities(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call extract_entities tool"""
        text = arguments.get("text", "")
        use_spacy = arguments.get("use_spacy", True)
        use_nltk = arguments.get("use_nltk", False)
        use_patterns = arguments.get("use_patterns", True)
        extract_techs = arguments.get("extract_technologies", True)
        
        if not text:
            return {
                "content": [{"type": "text", "text": "Error: 'text' argument is required"}],
                "isError": True
            }
        
        entities = self.entity_extractor.extract_all_entities(
            text,
            use_spacy=use_spacy,
            use_nltk=use_nltk,
            use_patterns=use_patterns,
            extract_technologies=extract_techs
        )
        
        stats = self.entity_extractor.get_entity_statistics(entities)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "entities": entities,
                        "statistics": stats,
                        "entity_types_available": list(self.entity_extractor.ENTITY_TYPES.keys())
                    }, indent=2)
                }
            ],
            "isError": False
        }
    
    def _call_extract_entities_llm(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call extract_entities_llm tool"""
        text = arguments.get("text", "")
        max_length = arguments.get("max_length", 4000)
        
        if not text:
            return {
                "content": [{"type": "text", "text": "Error: 'text' argument is required"}],
                "isError": True
            }
        
        result = self.llm_extractor.extract_entities(text, max_length=max_length)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ],
            "isError": "error" in result
        }
    
    def _call_analyze_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call analyze_document tool"""
        text = arguments.get("text", "")
        method = arguments.get("method", "spacy")
        
        if not text:
            return {
                "content": [{"type": "text", "text": "Error: 'text' argument is required"}],
                "isError": True
            }
        
        results = {}
        
        if method in ["spacy", "both"]:
            results["spacy"] = self.entity_extractor.analyze_document(text)
        
        if method in ["llm", "both"]:
            results["llm"] = self.llm_extractor.extract_entities(text)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(results, indent=2)
                }
            ],
            "isError": False
        }
    
    def _call_filter_entities(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call filter_entities tool"""
        entities = arguments.get("entities", [])
        entity_types = arguments.get("entity_types", [])
        
        if not entities:
            return {
                "content": [{"type": "text", "text": "Error: 'entities' argument is required"}],
                "isError": True
            }
        
        if not entity_types:
            return {
                "content": [{"type": "text", "text": "Error: 'entity_types' argument is required"}],
                "isError": True
            }
        
        filtered = self.entity_extractor.filter_entities_by_type(entities, entity_types)
        stats = self.entity_extractor.get_entity_statistics(filtered)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "filtered_entities": filtered,
                        "statistics": stats
                    }, indent=2)
                }
            ],
            "isError": False
        }
    
    def _call_get_entity_types(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call get_entity_types tool"""
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(self.entity_extractor.ENTITY_TYPES, indent=2)
                }
            ],
            "isError": False
        }
    
    def _call_compare_extraction_methods(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call compare_extraction_methods tool"""
        text = arguments.get("text", "")
        
        if not text:
            return {
                "content": [{"type": "text", "text": "Error: 'text' argument is required"}],
                "isError": True
            }
        
        spacy_entities = self.entity_extractor.extract_all_entities(text)
        comparison = self.llm_extractor.compare_extraction_methods(text, spacy_entities)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(comparison, indent=2)
                }
            ],
            "isError": False
        }
    
    def _call_extract_standards(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call extract_standards tool"""
        text = arguments.get("text", "")
        
        if not text:
            return {
                "content": [{"type": "text", "text": "Error: 'text' argument is required"}],
                "isError": True
            }
        
        standards = self.entity_extractor.extract_standards_pattern(text)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "standards": standards,
                        "count": len(standards)
                    }, indent=2)
                }
            ],
            "isError": False
        }
    
    def _call_get_entity_statistics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call get_entity_statistics tool"""
        entities = arguments.get("entities", [])
        
        if not entities:
            return {
                "content": [{"type": "text", "text": "Error: 'entities' argument is required"}],
                "isError": True
            }
        
        stats = self.entity_extractor.get_entity_statistics(entities)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(stats, indent=2)
                }
            ],
            "isError": False
        }
    
    # Resource handlers
    def handle_resources_list(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle resources/list request"""
        return {
            "resources": self.resources
        }
    
    def handle_resources_read(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri", "")
        
        if uri == "nlp://entity-types":
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(self.entity_extractor.ENTITY_TYPES, indent=2)
                    }
                ]
            }
        elif uri == "nlp://extraction-methods":
            methods = {
                "spacy": "Industrial-strength NLP with pre-trained models. Fast and accurate for generic entities.",
                "nltk": "Classic NLP library with rule-based NER. Good for educational purposes.",
                "llm": "LLM-based extraction using LM Studio. Best for domain-specific entities and context.",
                "patterns": "Regex-based extraction for technical standards (GOST, ISO, etc.). Very accurate for known patterns."
            }
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(methods, indent=2)
                    }
                ]
            }
        else:
            return {
                "contents": [],
                "isError": True
            }
    
    # Prompt handlers
    def handle_prompts_list(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle prompts/list request"""
        return {
            "prompts": self.prompts
        }
    
    def handle_prompts_get(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle prompts/get request"""
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if name == "entity_extraction_prompt":
            text = arguments.get("text", "")
            entity_types = arguments.get("entity_types", list(self.entity_extractor.ENTITY_TYPES.keys()))
            
            prompt = f"""Extract the following entity types from this text: {', '.join(entity_types)}

Text:
{text}

Return entities in JSON format with: text, label, start, end, confidence."""
            
            return {
                "description": "Entity extraction prompt",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        elif name == "document_analysis_prompt":
            document = arguments.get("document", "")
            focus = arguments.get("focus", "all entities")
            
            prompt = f"""Analyze this document focusing on {focus}:

{document}

Provide:
1. List of key entities found
2. Relationships between entities
3. Summary of main topics"""
            
            return {
                "description": "Document analysis prompt",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        else:
            return {
                "isError": True,
                "error": f"Unknown prompt: {name}"
            }

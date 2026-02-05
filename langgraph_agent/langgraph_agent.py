"""
Simplified LangGraph implementation of the AI Agent focused on MCP service orchestration.
All nodes have been removed for reconstruction.
"""

from typing import TypedDict, List, Dict, Any, Literal, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from typing import Annotated
from functools import reduce
import json
import operator
from database.utils.multi_database_manager import multi_db_manager as DatabaseManager, reload_database_config
from models.sql_generator import SQLGenerator
from models.sql_executor import SQLExecutor
from sql_mcp_server.client import SQLMCPClient
from models.prompt_generator import PromptGenerator
from models.response_generator import ResponseGenerator
from models.security_sql_detector import SecuritySQLDetector
from config.settings import TERMINATE_ON_POTENTIALLY_HARMFUL_SQL
import os
from config.settings import str_to_bool
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


# Define the state using the proper LangGraph approach with annotations and reducers
class AgentState(TypedDict):
    """
    State definition for the MCP-focused LangGraph agent.
    """
    user_request: Annotated[str, lambda x, y: y]          # Original user request - always replace with new value
    mcp_queries: Annotated[List[Dict[str, Any]], lambda x, y: y]           # Planned MCP queries to execute - use new value
    mcp_results: Annotated[List[Dict[str, Any]], operator.add]           # Results from executed MCP queries - append
    rag_results: Annotated[List[Dict[str, Any]], lambda x, y: y]          # RAG results from RAG services
    other_results: Annotated[List[Dict[str, Any]], lambda x, y: y]        # Results from other MCP services
    synthesized_result: Annotated[str, lambda x, y: y]                     # Synthesized result - use new
    can_answer: Annotated[bool, lambda x, y: y]                           # Flag indicating if we can answer - use new value
    iteration_count: Annotated[int, operator.add]                       # Number of iterations performed - add
    max_iterations: Annotated[int, lambda x, y: x]                        # Maximum allowed iterations - keep original
    final_answer: Annotated[str, lambda x, y: y]                          # Final answer - use new
    error_message: Annotated[Optional[str], lambda x, y: y]               # Any error messages - use new
    mcp_servers: Annotated[List[Dict[str, str]], lambda x, y: y]          # Available MCP servers - use new
    refined_queries: Annotated[List[Dict[str, Any]], lambda x, y: y]      # Refined queries - use new value
    failure_reason: Annotated[Optional[str], lambda x, y: y]              # Reason for failure - use new
    # Fields retained for compatibility
    schema_dump: Annotated[Dict[str, Any], lambda x, y: y]    # Always replace with new value
    sql_query: Annotated[str, lambda x, y: y]
    db_results: Annotated[List[Dict[str, Any]], operator.add]
    all_db_results: Annotated[Dict[str, List[Dict[str, Any]]], lambda x, y: y]  # Always replace with new value
    table_to_db_mapping: Annotated[Dict[str, str], lambda x, y: y]  # Always replace with new value
    table_to_real_db_mapping: Annotated[Dict[str, str], lambda x, y: y]  # Always replace with new value
    response_prompt: Annotated[str, lambda x, y: y]
    messages: Annotated[List[BaseMessage], operator.add]  # Append messages
    validation_error: Annotated[str, lambda x, y: y]
    retry_count: Annotated[int, operator.add]
    execution_error: Annotated[str, lambda x, y: y]
    sql_generation_error: Annotated[str, lambda x, y: y]
    mcp_execution_errors: Annotated[List[Dict[str, Any]], operator.add]  # MCP execution errors - append
    disable_sql_blocking: Annotated[bool, lambda x, y: y]
    disable_databases: Annotated[bool, lambda x, y: y]
    query_type: Annotated[str, lambda x, y: y]
    database_name: Annotated[str, lambda x, y: y]
    previous_sql_queries: Annotated[List[str], operator.add]
    registry_url: Annotated[Optional[str], lambda x, y: y]
    discovered_services: Annotated[List[Dict[str, Any]], operator.add]
    mcp_service_results: Annotated[List[Dict[str, Any]], operator.add]
    use_mcp_results: Annotated[bool, lambda x, y: y]
    mcp_tool_calls: Annotated[List[Dict[str, Any]], lambda x, y: y]
    mcp_capable_response: Annotated[str, lambda x, y: y]
    return_mcp_results_to_llm: Annotated[bool, lambda x, y: y]
    is_final_answer: Annotated[bool, lambda x, y: y]  # Use new value

    enhancement_errors: Annotated[List[Dict[str, Any]], operator.add]  # Errors from enhancement process - append
    # RAG-specific fields
    rag_documents: Annotated[List[Dict[str, Any]], operator.add]
    rag_context: Annotated[str, lambda x, y: y]
    use_rag_flag: Annotated[bool, lambda x, y: y]
    rag_relevance_score: Annotated[float, lambda x, y: y]
    rag_query: Annotated[str, lambda x, y: y]
    rag_response: Annotated[str, lambda x, y: y]


def input_reception_node(state: AgentState) -> AgentState:
    """
    Node to receive and store the user query in the state.
    This is the first step in the workflow.
    """

    # The user_request is already in the state from initialization
    # This node simply ensures it's properly stored and logs the reception
    user_request = state.get("user_request", "")

    logger.info(f"[INPUT_RECEPTION] Received user request: '{user_request}' (length: {len(user_request) if user_request else 0})")

    # Return the state with the user_request (which is already there)
    result_state = {
        **state
    }

    return result_state


def mcp_registry_call_node(state: AgentState) -> AgentState:
    """
    Node to call the MCP registry and discover available services.
    This is the second step in the workflow.
    """
    import time


    start_time = time.time()

    logger.info("[MCP_REGISTRY_CALL] Starting MCP registry call to discover services")

    try:
        # Get the registry URL from the state
        registry_url = state.get("registry_url")

        if not registry_url:
            logger.warning("[MCP_REGISTRY_CALL] No registry URL provided, skipping service discovery")
            result_state = {
                **state,
                "mcp_servers": [],
                "discovered_services": []
            }


            return result_state

        # Import the registry client
        from registry.registry_client import ServiceRegistryClient

        # Create registry client and discover services
        client = ServiceRegistryClient(registry_url)

        # Discover all services from the registry
        services = client.discover_services()

        # Convert ServiceInfo objects to dictionaries for compatibility with the rest of the system
        services_as_dicts = []
        for service in services:
            service_dict = {
                "id": service.id,
                "host": service.host,
                "port": service.port,
                "type": service.type,
                "metadata": service.metadata
            }
            services_as_dicts.append(service_dict)

        elapsed_time = time.time() - start_time
        logger.info(f"[MCP_REGISTRY_CALL] Discovered {len(services_as_dicts)} services in {elapsed_time:.2f}s")

        # Update the state with discovered services
        result_state = {
            **state,
            "mcp_servers": services_as_dicts,
            "discovered_services": services_as_dicts
        }


        return result_state
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"MCP registry call failed: {str(e)}"
        logger.error(f"[MCP_REGISTRY_CALL] {error_msg} after {elapsed_time:.2f}s")

        # Return state with empty service lists in case of error
        return {
            **state,
            "mcp_servers": [],
            "discovered_services": [],
            "error_message": error_msg
        }


def mcp_model_query_node(state: AgentState) -> AgentState:
    """
    Node to send request to MCP capable model using the prompt template
    and populate both {user_request} and {mcp_services_json} variables with actual values.
    This is the third step in the workflow.
    """
    import time
    import json


    start_time = time.time()

    logger.info("[MCP_MODEL_QUERY] Starting MCP model query with user request and discovered services")

    try:
        # Extract the user request and MCP services from the state
        user_request = state.get("user_request", "")
        mcp_services = state.get("mcp_servers", [])

        logger.info(f"[MCP_MODEL_QUERY] Processing user request: '{user_request}' (length: {len(user_request)})")
        logger.info(f"[MCP_MODEL_QUERY] Available MCP services count: {len(mcp_services)}")

        # Import and call the MCP capable model
        from models.dedicated_mcp_model import DedicatedMCPModel
        mcp_model = DedicatedMCPModel()

        # Call the model with the user request and available services
        # The model internally handles the prompt template and extraction
        result = mcp_model.analyze_request_for_mcp_services(user_request, mcp_services)

        # Extract tool calls from the result according to the expected format in the prompt
        # Check if result is a dict before calling .get() on it
        if isinstance(result, dict):
            tool_calls = result.get("tool_calls", [])
        else:
            # If result is not a dict (e.g., it's a list), set tool_calls to an empty list
            logger.warning(f"[MCP_MODEL_QUERY] Expected dict but got {type(result)}: {result}")
            tool_calls = []

        # Validate and clean the tool calls to ensure they match the expected format
        validated_tool_calls = []
        if tool_calls and isinstance(tool_calls, list):
            for call in tool_calls:
                if isinstance(call, dict):
                    # Ensure the tool call has the required structure as defined in the prompt
                    validated_call = {
                        "service_id": call.get("service_id", ""),
                        "method": call.get("method", ""),
                        "params": call.get("params", {})
                    }
                    validated_tool_calls.append(validated_call)

        elapsed_time = time.time() - start_time
        logger.info(f"[MCP_MODEL_QUERY] MCP model query completed in {elapsed_time:.2f}s")
        logger.info(f"[MCP_MODEL_QUERY] Extracted {len(validated_tool_calls)} tool calls from LLM response")

        # Store the model response in the state
        try:
            mcp_capable_response = json.dumps(result, ensure_ascii=False)
        except TypeError:
            # If result is not JSON serializable, convert it to a string representation
            mcp_capable_response = json.dumps(str(result), ensure_ascii=False)

        result_state = {
            **state,
            "mcp_tool_calls": validated_tool_calls,
            "mcp_capable_response": mcp_capable_response,
            "is_final_answer": result.get("is_final_answer", False) if isinstance(result, dict) else False,
            "has_sufficient_info": result.get("has_sufficient_info", False) if isinstance(result, dict) else False,
            "confidence_level": result.get("confidence_level", 0.0) if isinstance(result, dict) else 0.0
        }

        return result_state
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"MCP model query failed: {str(e)}"
        logger.error(f"[MCP_MODEL_QUERY] {error_msg} after {elapsed_time:.2f}s")

        # Return state with error information
        result_state = {
            **state,
            "error_message": error_msg,
            "mcp_tool_calls": [],
            "mcp_capable_response": "",
            "is_final_answer": False,
            "has_sufficient_info": False,
            "confidence_level": 0.0
        }

        return result_state


def planning_and_filtering_node(state: AgentState) -> AgentState:
    """
    Node to plan MCP tool calls and filter based on environment variables.
    This is the fourth step in the workflow.
    """
    import time
    import os
    from config.settings import str_to_bool


    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()  # Load .env file into environment variables
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file loading")
    except Exception as e:
        logger.warning(f"Could not load .env file: {str(e)}")

    start_time = time.time()
    logger.info("[PLANNING_AND_FILTERING] Starting planning and filtering of MCP tool calls")

    try:
        # Get the tool calls from the state
        tool_calls = state.get("mcp_tool_calls", [])

        logger.info(f"[PLANNING_AND_FILTERING] Total tool calls to process: {len(tool_calls)}")

        # Load environment variables and check which services are enabled
        sql_enabled = str_to_bool(os.getenv("SQL_ENABLE", "true"))
        web_search_enabled = str_to_bool(os.getenv("WEB_SEARCH_ENABLE", "true"))
        dns_enabled = str_to_bool(os.getenv("DNS_ENABLE", "true"))
        download_enabled = str_to_bool(os.getenv("DOWNLOAD_ENABLE", "true"))

        logger.info(f"[PLANNING_AND_FILTERING] Service enablement - SQL: {sql_enabled}, Web Search: {web_search_enabled}, DNS: {dns_enabled}, Download: {download_enabled}")

        # Filter the tool calls based on enabled services
        filtered_tool_calls = []

        for call in tool_calls:
            service_id = call.get("service_id", "").lower()

            # Determine if this service type is enabled
            is_enabled = True

            if 'sql' in service_id or 'database' in service_id:
                is_enabled = sql_enabled
            elif 'search' in service_id or 'web' in service_id:
                is_enabled = web_search_enabled
            elif 'dns' in service_id:
                is_enabled = dns_enabled
            elif 'download' in service_id:
                is_enabled = download_enabled

            if is_enabled:
                filtered_tool_calls.append(call)
            else:
                logger.info(f"[PLANNING_AND_FILTERING] Skipping disabled service: {service_id}")

        elapsed_time = time.time() - start_time
        logger.info(f"[PLANNING_AND_FILTERING] Planning and filtering completed in {elapsed_time:.2f}s")
        logger.info(f"[PLANNING_AND_FILTERING] Filtered {len(tool_calls)} calls down to {len(filtered_tool_calls)} based on environment settings")

        # Store the filtered tool calls in the state
        result_state = {
            **state,
            "mcp_tool_calls": filtered_tool_calls,
            "filtered_mcp_tool_calls": filtered_tool_calls  # Keep original for reference too
        }

        return result_state
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Planning and filtering failed: {str(e)}"
        logger.error(f"[PLANNING_AND_FILTERING] {error_msg} after {elapsed_time:.2f}s")

        # Return state with error information but keep original tool calls
        result_state = {
            **state,
            "error_message": error_msg,
            "filtered_mcp_tool_calls": []
        }

        return result_state


def parallel_execution_node(state: AgentState) -> AgentState:
    """
    Node to execute all requested MCP tool calls simultaneously in parallel and enhance them immediately.
    This is the fifth step in the workflow.
    """
    import time
    import concurrent.futures
    from models.dedicated_mcp_model import DedicatedMCPModel


    start_time = time.time()
    logger.info("[PARALLEL_EXECUTION] Starting parallel execution of MCP tool calls with immediate enhancement")

    try:
        # Get the filtered tool calls and MCP servers from the state
        tool_calls = state.get("mcp_tool_calls", [])
        mcp_servers = state.get("mcp_servers", [])

        logger.info(f"[PARALLEL_EXECUTION] Executing {len(tool_calls)} tool calls in parallel")

        if not tool_calls:
            logger.info("[PARALLEL_EXECUTION] No tool calls to execute, returning original state")
            return state

        # Define enhancement functions for different MCP tool types
        def enhance_sql_result(result):
            """Enhance SQL-type results"""
            if result and isinstance(result, dict):
                enhanced = result.copy()
                # Add any SQL-specific enhancements
                enhanced['enhanced_at'] = time.time()
                enhanced['type'] = 'sql_enhanced'
                return enhanced
            else:
                # Log the error when enhancement is not possible
                logger.warning(f"[PARALLEL_EXECUTION] Cannot enhance SQL result: {result}")
                # Return an error indication when enhancement is not possible
                return {
                    "error": "Cannot enhance: result is not a valid dictionary",
                    "enhanced_at": time.time(),
                    "type": "enhancement_error"
                }

        def enhance_search_result(result):
            """Enhance search-type results by downloading content from URLs and summarizing with LLM"""
            # Log the full raw result coming into the function
            logger.info(f"[SEARCH_ENHANCEMENT] Raw search result coming into function: {result}")

            if result and isinstance(result, dict):
                try:
                    # Import required components
                    from rag_component.main import RAGOrchestrator
                    from registry.registry_client import ServiceRegistryClient
                    from config.settings import MCP_REGISTRY_URL

                    # Initialize the RAG orchestrator
                    rag_orchestrator = RAGOrchestrator()

                    # Extract search results from the result dictionary
                    # The search results are nested in result['result']['result']['results']
                    search_results = result.get('result', {}).get('result', {}).get('results', [])

                    # Extract the user query from the state or result
                    # Try to get from the nested result structure
                    user_query = (result.get('user_query') or
                                  result.get('result', {}).get('result', {}).get('query', '') or
                                  result.get('query', ''))

                    # If not in result, try to get from the parent state context
                    if not user_query and 'user_request' in state:
                        user_query = state['user_request']

                    # If we still don't have a query, use a default
                    if not user_query:
                        user_query = "Provide a summary of this content"

                    # Process search results with download and summarization
                    processed_results = rag_orchestrator.process_search_results_with_download(
                        search_results=search_results,
                        user_query=user_query
                    )

                    # Apply reranking using the RAG MCP server
                    try:
                        # Import required components
                        from models.dedicated_mcp_model import DedicatedMCPModel
                        from registry.registry_client import ServiceRegistryClient
                        from config.settings import MCP_REGISTRY_URL
                        from rag_component.config import RERANK_TOP_K_RESULTS

                        # Discover available RAG services
                        registry_client = ServiceRegistryClient(MCP_REGISTRY_URL)
                        rag_services = [s for s in registry_client.discover_services() if s.type == "rag"]

                        if not rag_services:
                            logger.warning("[SEARCH_ENHANCEMENT] No RAG MCP services available for reranking, skipping.")
                        else:
                            rag_service = rag_services[0]  # Use the first available RAG service

                            # Prepare documents for reranking - extract the summaries/content to be reranked
                            rerank_documents = []
                            for item in processed_results:
                                # Create a document-like structure for reranking
                                doc = {
                                    'content': item.get('summary', ''),  # Use the LLM-generated summary
                                    'title': item.get('title', ''),
                                    'url': item.get('url', ''),
                                    'original_description': item.get('original_description', '')
                                }
                                rerank_documents.append(doc)

                            # Prepare parameters for the MCP rerank call
                            rerank_params = {
                                "query": user_query,
                                "documents": rerank_documents,
                                "top_k": RERANK_TOP_K_RESULTS
                            }

                            # Call the RAG MCP server for reranking
                            mcp_model = DedicatedMCPModel()
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

                                # Update the processed results with reranking information
                                # Create a mapping of original results by URL for quick lookup
                                original_results_map = {item.get('url'): item for item in processed_results if item.get('url')}

                                reranked_processed_results = []
                                for reranked_doc in reranked_results:
                                    url = reranked_doc.get('url', '')
                                    # Find the original processed result that matches this reranked document
                                    original_result = original_results_map.get(url)

                                    if original_result:
                                        # Update with reranking score and position
                                        original_result['relevance_score'] = reranked_doc.get('score', 0.0)
                                        original_result['reranked'] = True
                                        reranked_processed_results.append(original_result)
                                    else:
                                        # If no original match found, create a new result with the reranked data
                                        reranked_processed_results.append({
                                            'title': reranked_doc.get('title', ''),
                                            'url': reranked_doc.get('url', ''),
                                            'summary': reranked_doc.get('content', ''),
                                            'original_description': reranked_doc.get('original_description', ''),
                                            'relevance_score': reranked_doc.get('score', 0.0),
                                            'reranked': True
                                        })

                                processed_results = reranked_processed_results
                            else:
                                logger.warning(f"[SEARCH_ENHANCEMENT] RAG MCP reranking failed: {rerank_result.get('error', 'Unknown error')}, skipping reranking.")

                    except ImportError:
                        logger.warning("[SEARCH_ENHANCEMENT] Required modules for MCP reranking not available, skipping reranking step.")
                    except Exception as e:
                        logger.error(f"[SEARCH_ENHANCEMENT] Error during MCP-based reranking: {str(e)}")
                        # Continue with original processed results if reranking fails

                    # Create enhanced result with the processed data
                    enhanced = {
                        'enhanced_results': processed_results,
                        'enhanced_at': time.time(),
                        'type': 'search_enhanced_with_content',
                        'enhancement_method': 'download_and_summarize_and_rerank'
                    }

                    # Log the full enhanced result leaving the function
                    logger.info(f"[SEARCH_ENHANCEMENT] Enhanced search result leaving function: {enhanced}")
                    return enhanced
                except ImportError as e:
                    logger.warning(f"[SEARCH_ENHANCEMENT] Could not import required modules: {str(e)}. Falling back to basic enhancement.")
                    # Fallback to basic enhancement if imports fail
                    enhanced = {
                        'enhanced_at': time.time(),
                        'type': 'search_enhanced'
                    }
                    return enhanced
                except Exception as e:
                    logger.error(f"[SEARCH_ENHANCEMENT] Error enhancing search result: {str(e)}")
                    # Return an error indication
                    error_result = {
                        "error": f"Error enhancing search result: {str(e)}",
                        "enhanced_at": time.time(),
                        "type": "enhancement_error"
                    }
                    logger.info(f"[SEARCH_ENHANCEMENT] Error result leaving function: {error_result}")
                    return error_result
            else:
                # Log the error when enhancement is not possible
                logger.warning(f"[PARALLEL_EXECUTION] Cannot enhance search result: {result}")
                # Log specifically when input is not a dictionary
                if not isinstance(result, dict):
                    logger.warning(f"[SEARCH_ENHANCEMENT] Input is not a dictionary: type={type(result)}, value={result}")
                # Return an error indication when enhancement is not possible
                error_result = {
                    "error": "Cannot enhance: result is not a valid dictionary",
                    "enhanced_at": time.time(),
                    "type": "enhancement_error"
                }
                logger.info(f"[SEARCH_ENHANCEMENT] Error result leaving function: {error_result}")
                return error_result

        def enhance_dns_result(result):
            """Enhance DNS-type results"""
            if result and isinstance(result, dict):
                enhanced = result.copy()
                # Add any DNS-specific enhancements
                enhanced['enhanced_at'] = time.time()
                enhanced['type'] = 'dns_enhanced'
                return enhanced
            else:
                # Log the error when enhancement is not possible
                logger.warning(f"[PARALLEL_EXECUTION] Cannot enhance DNS result: {result}")
                # Return an error indication when enhancement is not possible
                return {
                    "error": "Cannot enhance: result is not a valid dictionary",
                    "enhanced_at": time.time(),
                    "type": "enhancement_error"
                }

        def enhance_download_result(result):
            """Enhance download-type results"""
            if result and isinstance(result, dict):
                enhanced = result.copy()
                # Add any download-specific enhancements
                enhanced['enhanced_at'] = time.time()
                enhanced['type'] = 'download_enhanced'
                return enhanced
            else:
                # Log the error when enhancement is not possible
                logger.warning(f"[PARALLEL_EXECUTION] Cannot enhance download result: {result}")
                # Return an error indication when enhancement is not possible
                return {
                    "error": "Cannot enhance: result is not a valid dictionary",
                    "enhanced_at": time.time(),
                    "type": "enhancement_error"
                }

        def enhance_rag_result(result):
            """Enhance RAG-type results by reranking with the RAG MCP server"""

            if result and isinstance(result, dict):
                try:
                    # Import required components
                    from models.dedicated_mcp_model import DedicatedMCPModel
                    from registry.registry_client import ServiceRegistryClient
                    from config.settings import MCP_REGISTRY_URL
                    from rag_component.config import RERANK_TOP_K_RESULTS

                    # Extract RAG results - check multiple possible structures based on actual data
                    rag_results = []

                    # Case 1: Direct results in 'result' field (most common for RAG)
                    if 'result' in result and isinstance(result['result'], list):
                        rag_results = result['result']
                    # Case 2: Nested structure like RAG MCP results
                    elif 'result' in result and isinstance(result['result'], dict):
                        nested_result = result['result']
                        if 'results' in nested_result and isinstance(nested_result['results'], list):
                            rag_results = nested_result['results']
                    # Case 3: Direct results in 'results' field
                    elif 'results' in result and isinstance(result['results'], list):
                        rag_results = result['results']
                    # Case 4: The result itself might be a single RAG document (based on test_actual_structures.py)
                    elif 'content' in result and 'metadata' in result:
                        # Single document, wrap in a list
                        rag_results = [result]
                    # Case 5: Results directly in the top level 'result' field (duplicate check with case 1 but more explicit)
                    elif isinstance(result.get('result'), list):
                        rag_results = result['result']
                    # Case 6: If result itself is a list of documents
                    elif isinstance(result, list):
                        rag_results = result
                    # Case 7: If the result is a single document dict
                    elif isinstance(result, dict) and 'content' in result and 'metadata' in result:
                        rag_results = [result]
                    # Case 8: Last resort - if none of the above matched
                    else:
                        # If we still haven't found results, log the structure for debugging
                        logger.warning(f"[RAG_ENHANCEMENT] No RAG results found, result structure: {type(result)} with keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

                    logger.debug(f"[RAG_ENHANCEMENT] Detected {len(rag_results)} RAG results from structure")

                    # Get the user query from the state
                    user_query = state.get('user_request', '')

                    # If no RAG results to enhance, return an error
                    if not rag_results:
                        return {
                            "error": "No RAG results to enhance",
                            "enhanced_at": time.time(),
                            "type": "enhancement_error"
                        }

                    # Discover available RAG services for reranking
                    registry_client = ServiceRegistryClient(MCP_REGISTRY_URL)
                    rag_services = [s for s in registry_client.discover_services() if s.type == "rag"]

                    if not rag_services:
                        return {
                            "error": "No RAG MCP services available for reranking",
                            "enhanced_at": time.time(),
                            "type": "enhancement_error"
                        }

                    rag_service = rag_services[0]  # Use the first available RAG service

                    # Prepare documents for reranking - extract the content to be reranked
                    rerank_documents = []
                    for item in rag_results:
                        # Create a document-like structure for reranking
                        if isinstance(item, dict):
                            doc = {
                                'content': item.get('content', ''),
                                'title': item.get('title', ''),
                                'source': item.get('source', ''),
                                'metadata': item.get('metadata', {}),
                                'score': item.get('score', 0.0)
                            }
                        else:
                            # If it's not a dict, try to convert it
                            doc = {
                                'content': str(item),
                                'title': '',
                                'source': '',
                                'metadata': {},
                                'score': 0.0
                            }
                        rerank_documents.append(doc)

                    # Prepare parameters for the MCP rerank call
                    rerank_params = {
                        "query": user_query,
                        "documents": rerank_documents,
                        "top_k": RERANK_TOP_K_RESULTS
                    }

                    # Call the RAG MCP server for reranking
                    mcp_model = DedicatedMCPModel()
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


                        # Update the original RAG results with reranking information
                        # Create a mapping of content to reranked document for quick lookup
                        # Use a more robust matching approach since content might be slightly different
                        content_to_reranked = {}
                        for doc in reranked_results:
                            content = doc.get('content', '')
                            if content:
                                content_to_reranked[content] = doc

                        # Use only the reranked results, not the original unmatched documents
                        updated_results = []
                        for reranked_doc in reranked_results:
                            # Find the corresponding original document to preserve metadata
                            reranked_content = reranked_doc.get('content', '')

                            # Look for the original document with matching content
                            original_match = None
                            for original_item in rag_results:
                                if isinstance(original_item, dict) and original_item.get('content', '') == reranked_content:
                                    original_match = original_item
                                    break

                            if original_match:
                                # Update the original document with the new reranking score
                                updated_item = original_match.copy()
                                updated_item['score'] = reranked_doc.get('score', original_match.get('score'))
                                updated_item['reranked'] = True
                                updated_results.append(updated_item)
                            else:
                                # If no match found, use the reranked document as is
                                updated_item = {
                                    'content': reranked_doc.get('content', ''),
                                    'metadata': reranked_doc.get('metadata', {}),
                                    'score': reranked_doc.get('score', 0.0),
                                    'reranked': True
                                }
                                updated_results.append(updated_item)

                        # Create enhanced result with reranked data
                        # Preserve the original structure of the result
                        enhanced = result.copy()
                        # Update the results based on the original structure
                        if 'result' in result and isinstance(result['result'], list):
                            enhanced['result'] = updated_results
                        elif 'result' in result and isinstance(result['result'], dict) and 'results' in result['result']:
                            enhanced['result']['results'] = updated_results
                            # Also update the count to reflect the actual number of results after reranking
                            enhanced['result']['count'] = len(updated_results)
                        elif 'results' in result:
                            enhanced['results'] = updated_results
                            # Update count if it exists in the structure
                            if 'count' in enhanced:
                                enhanced['count'] = len(updated_results)
                        else:
                            # If single document was wrapped, return the updated list
                            enhanced = updated_results[0] if len(updated_results) == 1 else updated_results

                        enhanced['enhanced_at'] = time.time()
                        enhanced['type'] = 'rag_enhanced_with_rerank'
                        enhanced['enhancement_method'] = 'rerank_documents_via_mcp'

                    else:
                        # Return an error instead of original results
                        return {
                            "error": f"RAG MCP reranking failed: {rerank_result.get('error', 'Unknown error')}",
                            "enhanced_at": time.time(),
                            "type": "enhancement_error"
                        }

                    return enhanced
                except Exception as e:
                    # Return an error indication
                    return {
                        "error": f"Error enhancing RAG result: {str(e)}",
                        "enhanced_at": time.time(),
                        "type": "enhancement_error"
                    }
            else:
                # Return an error indication when enhancement is not possible
                return {
                    "error": "Cannot enhance: result is not a valid dictionary",
                    "enhanced_at": time.time(),
                    "type": "enhancement_error"
                }

        def enhance_generic_result(result):
            """Generic enhancement for other result types"""
            if result and isinstance(result, dict):
                enhanced = result.copy()
                enhanced['enhanced_at'] = time.time()
                enhanced['type'] = 'generic_enhanced'
                return enhanced
            else:
                # Log the error when enhancement is not possible
                logger.warning(f"[PARALLEL_EXECUTION] Cannot enhance generic result: {result}")
                # Return an error indication when enhancement is not possible
                return {
                    "error": "Cannot enhance: result is not a valid dictionary",
                    "enhanced_at": time.time(),
                    "type": "enhancement_error"
                }

        # Create a function to execute and enhance a single tool call
        def execute_and_enhance_single_call(tool_call):
            try:
                mcp_model = DedicatedMCPModel()
                # Execute the single tool call against the available services
                result = mcp_model.execute_mcp_tool_calls([tool_call], mcp_servers)

                # Get the service ID to determine which enhancement function to use
                service_id = tool_call.get("service_id", "").lower()

                # Select enhancement function based on service type
                if 'sql' in service_id or 'database' in service_id:
                    enhancer_func = enhance_sql_result
                elif 'search' in service_id or 'web' in service_id:
                    enhancer_func = enhance_search_result
                elif 'dns' in service_id:
                    enhancer_func = enhance_dns_result
                elif 'download' in service_id:
                    enhancer_func = enhance_download_result
                elif 'rag' in service_id:
                    enhancer_func = enhance_rag_result
                else:
                    enhancer_func = enhance_generic_result

                # Apply enhancement to the result
                original_result = result[0] if result and isinstance(result, list) and len(result) > 0 else result
                enhanced_result = enhancer_func(original_result)

                return {
                    "tool_call": tool_call,
                    "result": enhanced_result,  # Return the enhanced result
                    "status": "success"
                }
            except Exception as e:
                logger.error(f"[PARALLEL_EXECUTION] Failed to execute or enhance tool call {tool_call.get('service_id', 'unknown')}: {str(e)}")
                return {
                    "tool_call": tool_call,
                    "result": None,
                    "status": "error",
                    "error": str(e)
                }

        # Execute all tool calls in parallel with immediate enhancement using ThreadPoolExecutor
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tool_calls), 10)) as executor:
            # Submit all tasks
            future_to_call = {executor.submit(execute_and_enhance_single_call, call): call for call in tool_calls}

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_call):
                result = future.result()
                results.append(result)

        # Separate successful results and errors
        successful_results = []
        errors = []

        for result in results:
            if result["status"] == "success" and result["result"]:
                # Add the enhanced result directly
                successful_results.append(result["result"])
            else:
                errors.append(result)

        elapsed_time = time.time() - start_time
        logger.info(f"[PARALLEL_EXECUTION] Parallel execution with enhancement completed in {elapsed_time:.2f}s")
        logger.info(f"[PARALLEL_EXECUTION] Successful results: {len(successful_results)}, Errors: {len(errors)}")

        # Merge results back into the state
        result_state = {
            **state,
            "mcp_results": successful_results,
            "mcp_execution_errors": errors
        }

        return result_state
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Parallel execution with enhancement failed: {str(e)}"
        logger.error(f"[PARALLEL_EXECUTION] {error_msg} after {elapsed_time:.2f}s")

        # Return state with error information
        result_state = {
            **state,
            "error_message": error_msg,
            "mcp_results": [],
            "mcp_execution_errors": [{"error": str(e), "status": "failed"}]
        }

        return result_state


def enhanced_results_collection_node(state: AgentState) -> AgentState:
    """
    Node to collect enhanced results and conditionally generate a response based on environment settings.
    This is the seventh step in the workflow.
    """
    import time
    import os
    from config.settings import str_to_bool
    from models.response_generator import ResponseGenerator


    start_time = time.time()
    logger.info("[ENHANCED_RESULTS_COLLECTION] Starting enhanced results collection and conditional response generation")

    try:
        # Load environment variables from .env file if it exists
        try:
            from dotenv import load_dotenv
            load_dotenv()  # Load .env file into environment variables
        except ImportError:
            logger.warning("python-dotenv not installed, skipping .env file loading")
        except Exception as e:
            logger.warning(f"Could not load .env file: {str(e)}")

        # Check the DISABLE_RESPONSE_GENERATION environment variable
        disable_response_generation = str_to_bool(os.getenv("DISABLE_RESPONSE_GENERATION", "false"))

        # Get the original user query and enhanced results from the state
        user_query = state.get("user_request", "")
        # Now that enhancement happens in parallel execution, the results are in mcp_results
        enhanced_results = state.get("mcp_results", [])

        logger.info(f"[ENHANCED_RESULTS_COLLECTION] User query: '{user_query}'")
        logger.info(f"[ENHANCED_RESULTS_COLLECTION] Enhanced results count: {len(enhanced_results)}")
        logger.info(f"[ENHANCED_RESULTS_COLLECTION] Response generation disabled: {disable_response_generation}")

        if disable_response_generation:
            # Return results directly to the user without LLM processing
            logger.info("[ENHANCED_RESULTS_COLLECTION] Response generation disabled, returning enhanced results directly")

            # Format the response with only the original user request and enhanced results (nothing else)
            final_response = {
                "original_request": user_query,
                "enhanced_results": enhanced_results,
                "status": "direct_response",
                "message": "Response generation is disabled. Returning enhanced results directly."
            }

            elapsed_time = time.time() - start_time
            logger.info(f"[ENHANCED_RESULTS_COLLECTION] Direct response completed in {elapsed_time:.2f}s")

            result_state = {
                **state,
                "final_answer": str(final_response),
                "synthesized_result": str(final_response),
                "can_answer": True,
                "response_generated": False  # Indicates no LLM was used
            }


            return result_state
        else:
            # Load the response generation prompt from file
            prompt_file_path = "./core/prompts/response_generator.txt"
            try:
                with open(prompt_file_path, 'r', encoding='utf-8') as file:
                    prompt_template = file.read()
            except FileNotFoundError:
                error_msg = f"Response generation prompt file not found: {prompt_file_path}"
                logger.error(f"[ENHANCED_RESULTS_COLLECTION] {error_msg}")

                # Return error response
                result_state = {
                    **state,
                    "error_message": error_msg,
                    "final_answer": f"Error: {error_msg}",
                    "can_answer": False
                }

                return result_state

            # Format ALL enhanced results to send to the LLM (no truncation)
            results_text = "\n".join([
                f"- {res.get('type', 'result')}: {str(res)}"
                for res in enhanced_results  # Include ALL results, no truncation
            ])

            # Log the full informational content being sent for enhancement
            logger.info(f"[ENHANCED_RESULTS_COLLECTION] Informational content being sent for enhancement: {len(enhanced_results)} enhanced results")

            # Log the complete data being sent for enhancement
            logger.info(f"[ENHANCED_RESULTS_COLLECTION] Calling response generator with:")
            logger.info(f"  - user_request: {user_query}")
            logger.info(f"  - informational_content: {len(enhanced_results)} enhanced results")
            logger.info(f"  - previous_signals: []")
            logger.info(f"  - previous_tool_calls: []")

            # Call the response generation LLM
            try:
                response_generator = ResponseGenerator()
                llm_response = response_generator.generate_response(
                    user_request=user_query,
                    informational_content=results_text,
                    previous_signals=[],  # No previous signals at this stage
                    previous_tool_calls=[]  # No previous tool calls at this stage
                )

                elapsed_time = time.time() - start_time
                logger.info(f"[ENHANCED_RESULTS_COLLECTION] LLM response generation completed in {elapsed_time:.2f}s")

                result_state = {
                    **state,
                    "final_answer": llm_response,
                    "synthesized_result": llm_response,
                    "can_answer": True,
                    "response_generated": True  # Indicates LLM was used
                }

                return result_state
            except Exception as e:
                error_msg = f"Response generation failed: {str(e)}"
                logger.error(f"[ENHANCED_RESULTS_COLLECTION] {error_msg}")

                # Return error response but still include the enhanced results
                result_state = {
                    **state,
                    "error_message": error_msg,
                    "final_answer": f"Response generation failed, but here are the enhanced results: {str(enhanced_results[:3])}",  # Show first 3 results
                    "synthesized_result": str(enhanced_results),
                    "can_answer": True,  # We still have results to return
                    "response_generated": False
                }

                return result_state

    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Enhanced results collection and response generation failed: {str(e)}"
        logger.error(f"[ENHANCED_RESULTS_COLLECTION] {error_msg} after {elapsed_time:.2f}s")

        # Return state with error information
        result_state = {
            **state,
            "error_message": error_msg,
            "final_answer": f"Error: {error_msg}",
            "can_answer": False
        }

        return result_state


def create_enhanced_agent_graph():
    """
    Creates the LangGraph workflow with the input reception, MCP registry call, MCP model query, planning/filtering, parallel execution, parallel enhancement, and enhanced results collection nodes.
    """
    # Create a simple graph as a starting point
    workflow = StateGraph(AgentState)

    # Add the input reception node to the workflow
    workflow.add_node("input_reception", input_reception_node)

    # Add the MCP registry call node to the workflow
    workflow.add_node("mcp_registry_call", mcp_registry_call_node)

    # Add the MCP model query node to the workflow
    workflow.add_node("mcp_model_query", mcp_model_query_node)

    # Add the planning and filtering node to the workflow
    workflow.add_node("planning_and_filtering", planning_and_filtering_node)

    # Add the parallel execution node to the workflow
    workflow.add_node("parallel_execution", parallel_execution_node)


    # Add the enhanced results collection node to the workflow
    workflow.add_node("enhanced_results_collection", enhanced_results_collection_node)

    # Set the entry point to the input reception node
    workflow.set_entry_point("input_reception")

    # Connect input reception to MCP registry call
    workflow.add_edge("input_reception", "mcp_registry_call")

    # Connect MCP registry call to MCP model query
    workflow.add_edge("mcp_registry_call", "mcp_model_query")

    # Connect MCP model query to planning and filtering
    workflow.add_edge("mcp_model_query", "planning_and_filtering")

    # Connect planning and filtering to parallel execution
    workflow.add_edge("planning_and_filtering", "parallel_execution")

    # Connect parallel execution directly to enhanced results collection (since enhancement now happens in parallel execution)
    workflow.add_edge("parallel_execution", "enhanced_results_collection")

    # For now, just return the graph with all implemented nodes
    # Future implementation will add more nodes and edges here

    return workflow.compile()


class AgentMonitoringCallback:
    """
    Callback class to monitor and log the execution of the LangGraph agent
    """
    def __init__(self):
        self.execution_log = []
        self.start_time = None

    def on_graph_start(self, state: AgentState):
        self.start_time = time.time()
        log_entry = {
            "timestamp": datetime.now(),
            "event": "graph_start",
            "node": "start",
            "state_summary": {
                "request_length": len(state.get("user_request", "")),
                "has_schema": bool(state.get("schema_dump")),
                "has_sql": bool(state.get("sql_query")),
                "retry_count": state.get("retry_count", 0)
            }
        }
        self.execution_log.append(log_entry)
        logger.info(f"[GRAPH START] Processing request: {state['user_request']}")

    def on_graph_end(self, state: AgentState):
        total_time = time.time() - self.start_time if self.start_time else 0
        log_entry = {
            "timestamp": datetime.now(),
            "event": "graph_end",
            "node": "end",
            "total_execution_time": total_time,
            "state_summary": {
                "has_sql": bool(state.get("sql_query")),
                "result_count": len(state.get("db_results", [])),
                "final_response_length": len(state.get("final_response", "")),
                "retry_count": state.get("retry_count", 0),
                "errors": {
                    "validation": state.get("validation_error"),
                    "execution": state.get("execution_error"),
                    "generation": state.get("sql_generation_error")
                }
            }
        }
        self.execution_log.append(log_entry)
        logger.info(f"[GRAPH END] Completed in {total_time:.2f}s, retries: {state.get('retry_count', 0)}")


def run_enhanced_agent(user_request: str, mcp_servers: List[Dict[str, Any]] = None, disable_sql_blocking: bool = False, disable_databases: bool = False, registry_url: str = None) -> Dict[str, Any]:
    """
    Function to run the enhanced agent with a user request.
    This serves as an entry point that will work with the reconstructed graph.
    """
    # Import the registry URL from config if not provided
    from config.settings import MCP_REGISTRY_URL
    effective_registry_url = registry_url or MCP_REGISTRY_URL

    # Log the user_request at the start
    logger.info(f"[RUN_ENHANCED_AGENT] Initial user_request: '{user_request}' (length: {len(user_request) if user_request else 0})")
    logger.info(f"[RUN_ENHANCED_AGENT] Type of user_request: {type(user_request)}")
    logger.info(f"[RUN_ENHANCED_AGENT] Repr of user_request: {repr(user_request)}")

    # Create the graph
    graph = create_enhanced_agent_graph()

    # Define initial state for the agent
    initial_state: AgentState = {
        "user_request": user_request,
        "mcp_queries": [],
        "mcp_results": [],
        "synthesized_result": "",
        "can_answer": False,
        "iteration_count": 0,
        "max_iterations": 3,
        "final_answer": "",
        "error_message": None,
        "mcp_servers": mcp_servers or [],
        "refined_queries": [],
        "failure_reason": None,
        # Fields retained for compatibility
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "",
        "messages": [],
        "validation_error": None,
        "retry_count": 0,
        "execution_error": None,
        "sql_generation_error": None,
        "disable_sql_blocking": disable_sql_blocking,
        "disable_databases": disable_databases,
        "query_type": "initial",
        "database_name": "",
        "previous_sql_queries": [],
        "registry_url": effective_registry_url,
        "discovered_services": [],
        "mcp_service_results": [],
        "use_mcp_results": False,
        "mcp_tool_calls": [],
        "mcp_capable_response": "",
        "return_mcp_results_to_llm": False,
        "is_final_answer": False,
        "rag_documents": [],
        "rag_context": "",
        "use_rag_flag": False,
        "rag_relevance_score": 0.0,
        "rag_query": "",
        "rag_response": "",
        "enhancement_errors": [],
        "mcp_execution_errors": []
    }

    # Create monitoring callback
    callback_handler = AgentMonitoringCallback()
    callback_handler.on_graph_start(initial_state)

    # Run the graph with a recursion limit to prevent infinite loops
    try:
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": "default"}, "recursion_limit": 50})
    except Exception as e:
        # If we hit a recursion limit or other error, return a meaningful response
        error_msg = str(e)
        logger.error(f"Error in graph execution: {error_msg}")
        result = {
            "user_request": user_request,
            "mcp_queries": [],
            "mcp_results": [],
            "synthesized_result": "",
            "can_answer": False,
            "iteration_count": 0,
            "max_iterations": 3,
            "final_answer": f"Error: The system encountered an issue while processing your request: {error_msg}",
            "error_message": error_msg,
            "mcp_servers": mcp_servers or [],
            "refined_queries": [],
            "failure_reason": error_msg,
            # Compatibility fields
            "schema_dump": {},
            "sql_query": "",
            "db_results": [],
            "all_db_results": {},
            "table_to_db_mapping": {},
            "table_to_real_db_mapping": {},
            "response_prompt": "",
            "messages": [],
            "validation_error": error_msg,
            "retry_count": 0,
            "execution_error": error_msg,
            "sql_generation_error": error_msg,
            "disable_sql_blocking": False,
            "disable_databases": False,
            "query_type": "initial",
            "database_name": "",
            "previous_sql_queries": [],
            "registry_url": effective_registry_url,
            "discovered_services": [],
            "mcp_service_results": [],
            "use_mcp_results": False,
            "mcp_tool_calls": [],
            "mcp_capable_response": "",
            "return_mcp_results_to_llm": False,
            "is_final_answer": False,
            "rag_documents": [],
            "rag_context": "",
            "use_rag_flag": False,
            "rag_relevance_score": 0.0,
            "rag_query": "",
            "rag_response": ""
        }

    callback_handler.on_graph_end(result)

    return {
        "original_request": user_request,
        "final_answer": result.get("final_answer"),
        "can_answer": result.get("can_answer"),
        "iteration_count": result.get("iteration_count"),
        "mcp_tool_calls": result.get("mcp_tool_calls"),
        "is_final_answer": result.get("is_final_answer"),
        "has_sufficient_info": result.get("has_sufficient_info"),
        "confidence_level": result.get("confidence_level")
    }
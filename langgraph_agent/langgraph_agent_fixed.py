"""
New LangGraph implementation of the AI Agent focused on MCP service orchestration,
with enhanced state management, conditional logic, and iterative refinement capabilities.
"""

from typing import TypedDict, List, Dict, Any, Literal, Optional
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
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


class AgentState(TypedDict):
    """
    New state definition for the MCP-focused LangGraph agent.
    """
    user_request: str                           # Original user request
    mcp_queries: List[Dict[str, Any]]           # Planned MCP queries to execute
    mcp_results: List[Dict[str, Any]]           # Results from executed MCP queries
    synthesized_result: str                     # Synthesized result from all MCP queries
    can_answer: bool                           # Flag indicating if we can answer the question
    iteration_count: int                       # Number of iterations performed
    max_iterations: int                        # Maximum allowed iterations
    final_answer: str                          # Final answer to return to user
    error_message: Optional[str]               # Any error messages encountered
    mcp_servers: List[Dict[str, str]]          # Available MCP servers in the pool
    refined_queries: List[Dict[str, Any]]      # Refined queries for next iteration
    failure_reason: Optional[str]              # Reason for failure if iterations exhausted
    # Fields retained for compatibility
    schema_dump: Dict[str, Any]
    sql_query: str
    db_results: List[Dict[str, Any]]
    all_db_results: Dict[str, List[Dict[str, Any]]]
    table_to_db_mapping: Dict[str, str]
    table_to_real_db_mapping: Dict[str, str]
    response_prompt: str
    messages: List[BaseMessage]
    validation_error: str
    retry_count: int
    execution_error: str
    sql_generation_error: str
    disable_sql_blocking: bool
    disable_databases: bool
    query_type: str
    database_name: str
    previous_sql_queries: List[str]
    registry_url: Optional[str]
    discovered_services: List[Dict[str, Any]]
    mcp_service_results: List[Dict[str, Any]]
    use_mcp_results: bool
    mcp_tool_calls: List[Dict[str, Any]]
    mcp_capable_response: str
    return_mcp_results_to_llm: bool
    is_final_answer: bool  # Flag to indicate if the LLM response is a final answer
    # RAG-specific fields
    rag_documents: List[Dict[str, Any]]
    rag_context: str
    use_rag_flag: bool
    rag_relevance_score: float
    rag_query: str
    rag_response: str


def initialize_agent_state_node(state: AgentState) -> AgentState:
    """
    Node to initialize the agent state with default values
    """
    start_time = time.time()
    logger.info(f"[NODE START] initialize_agent_state_node - Initializing state for request: {state['user_request']}")

    elapsed_time = time.time() - start_time
    logger.info(f"[NODE SUCCESS] initialize_agent_state_node - Initialized state in {elapsed_time:.2f}s")

    return {
        "user_request": state["user_request"],
        "mcp_queries": [],
        "mcp_results": [],
        "synthesized_result": "",
        "can_answer": False,
        "iteration_count": 0,
        "max_iterations": 3,  # Set max iterations to 3 by default
        "final_answer": "",
        "error_message": None,
        "mcp_servers": state.get("mcp_servers", []),  # Will be populated by discover_services_node
        "refined_queries": [],
        "failure_reason": None,
        # Retain other fields for compatibility
        "schema_dump": state.get("schema_dump", {}),
        "sql_query": state.get("sql_query", ""),
        "db_results": state.get("db_results", []),
        "all_db_results": state.get("all_db_results", {}),
        "table_to_db_mapping": state.get("table_to_db_mapping", {}),
        "table_to_real_db_mapping": state.get("table_to_real_db_mapping", {}),
        "response_prompt": state.get("response_prompt", ""),
        "messages": state.get("messages", []),
        "validation_error": state.get("validation_error", None),
        "retry_count": state.get("retry_count", 0),
        "execution_error": state.get("execution_error", None),
        "sql_generation_error": state.get("sql_generation_error", None),
        "disable_sql_blocking": state.get("disable_sql_blocking", False),
        "disable_databases": state.get("disable_databases", False),
        "query_type": state.get("query_type", "initial"),
        "database_name": state.get("database_name", ""),
        "previous_sql_queries": state.get("previous_sql_queries", []),
        "registry_url": state.get("registry_url", None),
        "discovered_services": state.get("discovered_services", []),  # Will be populated by discover_services_node
        "mcp_service_results": state.get("mcp_service_results", []),
        "use_mcp_results": state.get("use_mcp_results", False),
        "mcp_tool_calls": state.get("mcp_tool_calls", []),
        "mcp_capable_response": state.get("mcp_capable_response", ""),
        "return_mcp_results_to_llm": state.get("return_mcp_results_to_llm", False),
        "is_final_answer": state.get("is_final_answer", False),  # Initialize to False by default
        "rag_documents": state.get("rag_documents", []),
        "rag_context": state.get("rag_context", ""),
        "use_rag_flag": state.get("use_rag_flag", False),
        "rag_relevance_score": state.get("rag_relevance_score", 0.0),
        "rag_query": state.get("rag_query", ""),
        "rag_response": state.get("rag_response", "")
    }


def discover_services_node(state: AgentState) -> AgentState:
    """
    Node to discover services from the MCP registry
    """
    start_time = time.time()
    registry_url = state.get("registry_url")
    logger.info(f"[NODE START] discover_services_node - Discovering services from registry: {registry_url}")

    try:
        # Only proceed if registry URL is provided
        if not registry_url:
            logger.info("[NODE INFO] discover_services_node - No registry URL provided, skipping service discovery")
            return {
                **state,
                "mcp_servers": [],
                "discovered_services": []
            }

        # Import the registry client
        try:
            from registry.registry_client import ServiceRegistryClient
        except ImportError:
            logger.warning("[NODE WARNING] discover_services_node - Registry client not available, skipping service discovery")
            return {
                **state,
                "mcp_servers": [],
                "discovered_services": []
            }

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
        logger.info(f"[NODE SUCCESS] discover_services_node - Discovered {len(services_as_dicts)} services in {elapsed_time:.2f}s")

        # Update the state with discovered services
        # The mcp_servers field will now contain the discovered services
        return {
            **state,
            "mcp_servers": services_as_dicts,
            "discovered_services": services_as_dicts
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error discovering services: {str(e)}"
        logger.error(f"[NODE ERROR] discover_services_node - {error_msg} after {elapsed_time:.2f}s")

        return {
            **state,
            "mcp_servers": [],
            "discovered_services": [],
            "error_message": error_msg
        }


def analyze_request_node(state: AgentState) -> AgentState:
    """
    Node to analyze the user request and determine how to proceed
    """
    start_time = time.time()
    logger.info(f"[NODE START] analyze_request_node - Analyzing request: {state['user_request']}")

    try:
        # Import required components
        from models.dedicated_mcp_model import DedicatedMCPModel
        from config.settings import str_to_bool
        import os

        # Check service-specific enable settings
        sql_enabled = str_to_bool(os.getenv("SQL_ENABLE", "true"))
        web_search_enabled = str_to_bool(os.getenv("WEB_SEARCH_ENABLE", "true"))
        dns_enabled = str_to_bool(os.getenv("DNS_ENABLE", "true"))
        download_enabled = str_to_bool(os.getenv("DOWNLOAD_ENABLE", "true"))
        rag_enabled = str_to_bool(os.getenv("RAG_ENABLED", "true"))

        mcp_model = DedicatedMCPModel()

        # Analyze the request to determine what MCP queries might be needed
        analysis_result = mcp_model.analyze_request_for_mcp_services(
            state["user_request"],
            state["mcp_servers"]
        )

        # Check for is_final_answer flag in the analysis result
        is_final_answer = analysis_result.get("is_final_answer", False)

        # Handle both possible keys for backward compatibility and correct structure
        suggested_queries = analysis_result.get("suggested_queries", [])
        tool_calls = analysis_result.get("tool_calls", [])

        # If we have tool_calls (which is the actual structure returned by the model), use those
        if tool_calls:
            # Filter the tool calls based on enabled services
            filtered_tool_calls = []
            for call in tool_calls:
                service_id = call.get('service_id', '').lower()

                # Check if the service type is enabled
                is_enabled = True
                if 'sql' in service_id or 'database' in service_id:
                    is_enabled = sql_enabled
                elif 'search' in service_id or 'web' in service_id:
                    is_enabled = web_search_enabled
                elif 'dns' in service_id:
                    is_enabled = dns_enabled
                elif 'download' in service_id:
                    is_enabled = download_enabled
                elif 'rag' in service_id:
                    is_enabled = rag_enabled

                if is_enabled:
                    filtered_tool_calls.append(call)

            # Store the filtered tool calls in mcp_queries for execution
            mcp_queries = filtered_tool_calls
            final_tool_calls = filtered_tool_calls
        elif suggested_queries:
            # Fallback to suggested_queries if tool_calls is not present
            # Also filter these if they contain service information
            filtered_suggested_queries = []
            for query in suggested_queries:
                service_id = query.get('service_id', '').lower()

                # Check if the service type is enabled
                is_enabled = True
                if 'sql' in service_id or 'database' in service_id:
                    is_enabled = sql_enabled
                elif 'search' in service_id or 'web' in service_id:
                    is_enabled = web_search_enabled
                elif 'dns' in service_id:
                    is_enabled = dns_enabled
                elif 'download' in service_id:
                    is_enabled = download_enabled
                elif 'rag' in service_id:
                    is_enabled = rag_enabled

                if is_enabled:
                    filtered_suggested_queries.append(query)

            mcp_queries = filtered_suggested_queries
            final_tool_calls = []  # No tool calls in this case
        else:
            # If neither is present, use an empty list
            mcp_queries = []
            final_tool_calls = []

        # Update state with analysis
        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] analyze_request_node - Analyzed request in {elapsed_time:.2f}s")
        logger.info(f"[NODE INFO] analyze_request_node - Services enabled - SQL: {sql_enabled}, Web Search: {web_search_enabled}, DNS: {dns_enabled}, Download: {download_enabled}, RAG: {rag_enabled}")
        logger.info(f"[NODE INFO] analyze_request_node - Original tool calls: {len(tool_calls)}, Filtered tool calls: {len(final_tool_calls)}, Is final answer: {is_final_answer}")

        return {
            **state,
            "mcp_queries": mcp_queries,
            "mcp_tool_calls": final_tool_calls,  # Also store in the dedicated field for reference
            "is_final_answer": is_final_answer,
            "iteration_count": state.get("iteration_count", 0)
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error analyzing request: {str(e)}"
        logger.error(f"[NODE ERROR] analyze_request_node - {error_msg} after {elapsed_time:.2f}s")

        return {
            **state,
            "mcp_queries": [],
            "mcp_tool_calls": [],
            "error_message": error_msg
        }


def plan_mcp_queries_node(state: AgentState) -> AgentState:
    """
    Node to plan MCP queries based on the analyzed request
    """
    start_time = time.time()
    logger.info(f"[NODE START] plan_mcp_queries_node - Planning MCP queries for request: {state['user_request']}")

    try:
        # If we have refined queries from a previous iteration, use those
        if state.get("refined_queries"):
            planned_queries = state["refined_queries"]
        else:
            # Otherwise, use the initial planned queries
            planned_queries = state["mcp_queries"]

        logger.info(f"[NODE INFO] plan_mcp_queries_node - Planned {len(planned_queries)} queries")

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] plan_mcp_queries_node - Planned queries in {elapsed_time:.2f}s")

        return {
            **state,
            "mcp_queries": planned_queries
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error planning MCP queries: {str(e)}"
        logger.error(f"[NODE ERROR] plan_mcp_queries_node - {error_msg} after {elapsed_time:.2f}s")

        return {
            **state,
            "mcp_queries": [],
            "error_message": error_msg
        }


def execute_mcp_queries_node(state: AgentState) -> AgentState:
    """
    Node to execute MCP queries in parallel or sequentially
    """
    start_time = time.time()

    # Import required components to check service enable settings
    from config.settings import str_to_bool
    import os

    # Check service-specific enable settings
    sql_enabled = str_to_bool(os.getenv("SQL_ENABLE", "true"))
    web_search_enabled = str_to_bool(os.getenv("WEB_SEARCH_ENABLE", "true"))
    dns_enabled = str_to_bool(os.getenv("DNS_ENABLE", "true"))
    download_enabled = str_to_bool(os.getenv("DOWNLOAD_ENABLE", "true"))
    rag_enabled = str_to_bool(os.getenv("RAG_ENABLE", "true"))

    # Filter the queries based on enabled services
    filtered_queries = []
    for query in state["mcp_queries"]:
        service_id = query.get('service_id', '').lower()

        # Check if the service type is enabled
        is_enabled = True
        if 'sql' in service_id or 'database' in service_id:
            is_enabled = sql_enabled
        elif 'search' in service_id or 'web' in service_id:
            is_enabled = web_search_enabled
        elif 'dns' in service_id:
            is_enabled = dns_enabled
        elif 'download' in service_id:
            is_enabled = download_enabled
        elif 'rag' in service_id:
            is_enabled = rag_enabled

        if is_enabled:
            filtered_queries.append(query)

    logger.info(f"[NODE START] execute_mcp_queries_node - Executing {len(filtered_queries)} MCP queries (out of {len(state['mcp_queries'])} total)")
    logger.info(f"[NODE INFO] execute_mcp_queries_node - Services enabled - SQL: {sql_enabled}, Web Search: {web_search_enabled}, DNS: {dns_enabled}, Download: {download_enabled}, RAG: {rag_enabled}")

    try:
        # Import required components
        from models.dedicated_mcp_model import DedicatedMCPModel
        mcp_model = DedicatedMCPModel()

        # Execute all planned queries against the MCP server pool
        # If the queries are tool calls (which they should be after our fix), use execute_mcp_tool_calls
        if filtered_queries:
            # Check if the first query looks like a tool call (has service_id/method/params)
            first_query = filtered_queries[0]
            if isinstance(first_query, dict) and ('service_id' in first_query or 'service' in first_query):
                # These appear to be tool calls, so use the execute_mcp_tool_calls method
                results = mcp_model.execute_mcp_tool_calls(filtered_queries, state["mcp_servers"])
            else:
                # These appear to be regular queries, so execute them individually
                results = []
                for query in filtered_queries:
                    result = mcp_model.execute_single_query(query, state["mcp_servers"])
                    results.append(result)
        else:
            # No queries to execute after filtering
            results = []

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] execute_mcp_queries_node - Executed {len(results)} queries successfully in {elapsed_time:.2f}s")

        return {
            **state,
            "mcp_results": results,
            "error_message": None
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error executing MCP queries: {str(e)}"
        logger.error(f"[NODE ERROR] execute_mcp_queries_node - {error_msg} after {elapsed_time:.2f}s")

        return {
            **state,
            "mcp_results": [],
            "error_message": error_msg
        }


def validate_sql_node(state: AgentState) -> AgentState:
    """
    Node to validate SQL query safety
    """
    start_time = time.time()
    sql = state["sql_query"]
    disable_blocking = state.get("disable_sql_blocking", False)
    schema_dump = state.get("schema_dump", {})

    logger.info(f"[NODE START] validate_sql_node - Validating SQL: {sql} (blocking {'disabled' if disable_blocking else 'enabled'})")

    # If SQL blocking is disabled, skip all validations and return success
    if disable_blocking:
        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] validate_sql_node - SQL validation skipped (blocking disabled) in {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": None,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
        }

    # Basic validation: Check if query is empty
    if not sql or sql.strip() == "":
        error_msg = "SQL query is empty"
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
        }

    # Use the security LLM for advanced analysis if enabled
    # Read the configuration dynamically to allow tests to override it
    use_security_llm = str_to_bool(os.getenv("USE_SECURITY_LLM", "true"))
    if use_security_llm:
        logger.info("[NODE INFO] validate_sql_node - Using security LLM for advanced analysis")
        try:
            security_detector = SecuritySQLDetector()
            is_safe, reason = security_detector.is_query_safe(sql, schema_dump)

            if not is_safe:
                error_msg = f"Security LLM detected potential security issue: {reason}"
                elapsed_time = time.time() - start_time
                logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": error_msg,
                    "retry_count": state.get("retry_count", 0) + 1,
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
                }
            else:
                # If security LLM says it's safe, skip basic validation
                elapsed_time = time.time() - start_time
                logger.info(f"[NODE SUCCESS] validate_sql_node - Security LLM validation passed in {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": None,
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
                }
        except NameError as ne:
            # Specifically handle the case where ChatOpenAI is not defined
            logger.warning(f"[NODE WARNING] validate_sql_node - Security LLM failed due to name error: {str(ne)}, falling back to basic validation")
            # If security LLM fails, fall back to basic validation
            pass
        except Exception as e:
            logger.warning(f"[NODE WARNING] validate_sql_node - Security LLM failed: {str(e)}, falling back to basic validation")
            # If security LLM fails, fall back to basic validation
            pass

    # Fallback to enhanced basic keyword matching if security LLM is disabled or failed
    logger.info("[NODE INFO] validate_sql_node - Using enhanced basic keyword matching for analysis")

    # Check for potentially harmful SQL commands
    sql_lower = sql.lower().strip()
    harmful_commands = ["drop", "delete", "insert", "update", "truncate", "alter", "exec", "execute", "merge", "replace"]

    for command in harmful_commands:
        # Skip 'create' if it's part of a column name like 'created_at'
        if command == "create":
            # Check if 'create' appears as a standalone command (not part of a column name)
            # Look for 'create' followed by a space or semicolon (indicating a command)
            import re
            if re.search(r'\bcreate\s+(table|database|index|view|procedure|function|trigger|role|user|schema)\b', sql_lower):
                error_msg = f"Potentially harmful SQL detected: {command}"
                elapsed_time = time.time() - start_time
                logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": error_msg,
                    "retry_count": state.get("retry_count", 0) + 1,
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
                }
        elif command in sql_lower:
            error_msg = f"Potentially harmful SQL detected: {command}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
            }

    # Additional validation: Check if query starts with SELECT
    if not sql_lower.startswith('select'):
        # Allow WITH clauses as they can be used safely for complex queries
        if not sql_lower.startswith('with'):
            error_msg = "SQL query does not start with SELECT or WITH, which is required for safety"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
            }

    # Check for dangerous patterns that might indicate SQL injection
    dangerous_patterns = [
        "union select",  # Could indicate SQL injection
        "information_schema",  # Could be used to extract schema info
        "pg_",  # PostgreSQL system tables/functions
        "sqlite_",  # SQLite system tables/functions
        "xp_",  # SQL Server extended procedures
        "sp_",  # SQL Server stored procedures
        "exec\\(",  # Execution functions
        "execute\\(",  # Execution functions
        "eval\\(",  # Evaluation functions
        "waitfor delay",  # Time-based attacks
        "benchmark\\(",  # Performance-based attacks
        "sleep\\(",  # Time-based attacks
        "load_file\\(",  # MySQL file access
        "into outfile",  # MySQL file write
        "into dumpfile",  # MySQL file write
        "cmdshell",  # SQL Server command execution
        "polyfromtext",  # Potential geography function abuse
        "st_astext",  # Potential geography function abuse
        "cast\\(.*as.*\\)",  # Potential casting for injection
        "convert\\(.*\\)",  # Potential conversion for injection
        "char\\(",  # Character code manipulation
        "nchar\\(",  # Unicode character code manipulation
        "substring\\(",  # String manipulation for extraction
        "mid\\(",  # String manipulation for extraction
        "asc\\(",  # ASCII value extraction
        "hex\\(",  # Hexadecimal manipulation
        "unhex\\(",  # Hexadecimal manipulation
        "quote\\(",  # Quote manipulation
        "concat\\(",  # String concatenation for injection
        "group_concat\\(",  # Aggregation for data extraction
        "load_xml\\(",  # XML loading for injection
        "extractvalue\\(",  # XML extraction for injection
        "updatexml\\(",  # XML update for injection
        "fn:.*\\(",  # XPath function calls
        "declare\\s+@.*=",  # T-SQL variable declaration
        "set\\s+@.*=",  # T-SQL variable assignment
        "openrowset\\(",  # T-SQL external data access
        "opendatasource\\(",  # T-SQL external data access
        "bulk\\s+insert",  # Bulk data insertion
        "openquery\\(",  # T-SQL remote query
        "execute\\s+as",  # T-SQL impersonation
        "impersonate",  # Impersonation attempts
        "shutdown",  # Database shutdown attempts
        "backup\\s+database",  # Database backup attempts
        "restore\\s+database",  # Database restore attempts
        "addsignature",  # Signature addition
        "makesignature",  # Signature creation
        "ctxsys.driddl",  # Oracle text index manipulation
        "sys.dbms",  # Oracle system package
        "sys.any",  # Oracle system type
        "any_data",  # Oracle system type
        "any_type",  # Oracle system type
        "anydataset",  # Oracle system type
        "sys.xmlgen",  # Oracle XML generation
        "sdo_util.to_clob",  # Oracle spatial utility
        "sdo_sql.shapefilereader",  # Oracle spatial utility
        "dbms_java.grant_permission",  # Oracle Java permissions
        "dbms_javaxx",  # Oracle Java permissions
        "dbms_scheduler",  # Oracle job scheduling
        "dbms_pipe",  # Oracle inter-session communication
        "dbms_alert",  # Oracle alert system
        "dbms_aq",  # Oracle queuing
        "dbms_datapump",  # Oracle data pump
        "dbms_metadata",  # Oracle metadata extraction
        "dbms_repcat",  # Oracle replication
        "dbms_registry",  # Oracle registry
        "dbms_rule",  # Oracle rules engine
        "dbms_streams",  # Oracle streaming
        "dbms_system",  # Oracle system operations
        "dbms_utility",  # Oracle utility functions
        "dbms_workload_repository",  # Oracle workload repository
        "dbms_xa",  # Oracle distributed transactions
        "dbms_xstream",  # Oracle XStream
        "dbms_crypto",  # Oracle cryptography
        "dbms_random",  # Oracle random generation
        "dbms_scheduler",  # Oracle scheduler
        "dbms_lock",  # Oracle locking mechanisms
        "dbms_lob",  # Oracle LOB operations
        "dbms_xmlgen",  # Oracle XML operations
        "dbms_xmlstore",  # Oracle XML storage
        "dbms_xmlschema",  # Oracle XML schema
        "dbms_xmlquery",  # Oracle XML querying
        "dbms_xmlsave",  # Oracle XML saving
        "dbms_xmlparser",  # Oracle XML parsing
        "dbms_xmlgen.getxml",  # Oracle XML generation
        "dbms_xmlgen.getclobval",  # Oracle XML generation
        "dbms_xmlgen.getstringval",  # Oracle XML generation
        "dbms_xmlgen.getnumberval",  # Oracle XML generation
        "dbms_xmlgen.getdateval",  # Oracle XML generation
        "dbms_xmlgen.getrowset",  # Oracle XML generation
        "dbms_xmlgen.getxmltype",  # Oracle XML generation
        "dbms_xmlgen.getxmlval",  # Oracle XML generation
        "dbms_xmlgen.getxmlstring",  # Oracle XML generation
        "dbms_xmlgen.getxmldoc",  # Oracle XML generation
        "dbms_xmlgen.getxmlfragment",  # Oracle XML generation
        "dbms_xmlgen.getxmlattribute",  # Oracle XML generation
        "dbms_xmlgen.getxmltext",  # Oracle XML generation
        "dbms_xmlgen.getxmlcomment",  # Oracle XML generation
        "dbms_xmlgen.getxmlpi",  # Oracle XML generation
        "dbms_xmlgen.getxmlcdata",  # Oracle XML generation
        "dbms_xmlgen.getxmlnamespace",  # Oracle XML generation
        "dbms_xmlgen.getxmlroot",  # Oracle XML generation
        "dbms_xmlgen.getxmlprolog",  # Oracle XML generation
        "dbms_xmlgen.getxmldeclaration",  # Oracle XML generation
        "dbms_xmlgen.getxmlstylesheet",  # Oracle XML generation
        "dbms_xmlgen.getxmltransform",  # Oracle XML generation
        "dbms_xmlgen.getxmloutput",  # Oracle XML generation
        "dbms_xmlgen.getxmlinput",  # Oracle XML generation
        "dbms_xmlgen.getxmlencoding",  # Oracle XML generation
        "dbms_xmlgen.getxmlversion",  # Oracle XML generation
        "dbms_xmlgen.getxmlstandalone",  # Oracle XML generation
        "dbms_xmlgen.getxmlindent",  # Oracle XML generation
        "dbms_xmlgen.getxmlformat",  # Oracle XML generation
        "dbms_xmlgen.getxmlcompression",  # Oracle XML generation
        "dbms_xmlgen.getxmldatatype",  # Oracle XML generation
        "dbms_xmlgen.getxmlschema",  # Oracle XML generation
        "dbms_xmlgen.getxmlvalidation",  # Oracle XML generation
        "dbms_xmlgen.getxmlnormalization",  # Oracle XML generation
        "dbms_xmlgen.getxmlcanonicalization",  # Oracle XML generation
        "dbms_xmlgen.getxmlserialization",  # Oracle XML generation
        "dbms_xmlgen.getxmlparsing",  # Oracle XML generation
        "dbms_xmlgen.getxmlprocessing",  # Oracle XML generation
        "dbms_xmlgen.getxmlrendering",  # Oracle XML generation
        "dbms_xmlgen.getxmlpresentation",  # Oracle XML generation
        "dbms_xmlgen.getxmltransformation",  # Oracle XML generation
        "dbms_xmlgen.getxmltranslation",  # Oracle XML generation
        "dbms_xmlgen.getxmlconversion",  # Oracle XML generation
        "dbms_xmlgen.getxmlmanipulation",  # Oracle XML generation
        "dbms_xmlgen.getxmlcreation",  # Oracle XML generation
        "dbms_xmlgen.getxmlmodification",  # Oracle XML generation
        "dbms_xmlgen.getxmldeletion",  # Oracle XML generation
        "dbms_xmlgen.getxmlinsertion",  # Oracle XML generation
        "dbms_xmlgen.getxmlupdate",  # Oracle XML generation
        "dbms_xmlgen.getxmlretrieval",  # Oracle XML generation
        "dbms_xmlgen.getxmlsearch",  # Oracle XML generation
        "dbms_xmlgen.getxmlfilter",  # Oracle XML generation
        "dbms_xmlgen.getxmlsort",  # Oracle XML generation
        "dbms_xmlgen.getxmlaggregation",  # Oracle XML generation
        "dbms_xmlgen.getxmlgrouping",  # Oracle XML generation
        "dbms_xmlgen.getxmlpartitioning",  # Oracle XML generation
        "dbms_xmlgen.getxmlindexing",  # Oracle XML generation
        "dbms_xmlgen.getxmlcaching",  # Oracle XML generation
        "dbms_xmlgen.getxmloptimization",  # Oracle XML generation
        "dbms_xmlgen.getxmlprofiling",  # Oracle XML generation
        "dbms_xmlgen.getxmlmonitoring",  # Oracle XML generation
        "dbms_xmlgen.getxmldebugging",  # Oracle XML generation
        "dbms_xmlgen.getxmllogging",  # Oracle XML generation
        "dbms_xmlgen.getxmltracing",  # Oracle XML generation
        "dbms_xmlgen.getxmlauditing",  # Oracle XML generation
        "dbms_xmlgen.getxmlsecurity",  # Oracle XML generation
        "dbms_xmlgen.getxmlencryption",  # Oracle XML generation
        "dbms_xmlgen.getxmldecryption",  # Oracle XML generation
        "dbms_xmlgen.getxmlauthentication",  # Oracle XML generation
        "dbms_xmlgen.getxmlauthorization",  # Oracle XML generation
        "dbms_xmlgen.getxmlprivilege",  # Oracle XML generation
        "dbms_xmlgen.getxmlpermission",  # Oracle XML generation
        "dbms_xmlgen.getxmlaccess",  # Oracle XML generation
        "dbms_xmlgen.getxmlcontrol",  # Oracle XML generation
        "dbms_xmlgen.getxmlmanagement",  # Oracle XML generation
        "dbms_xmlgen.getxmladministration",  # Oracle XML generation
        "dbms_xmlgen.getxmlconfiguration",  # Oracle XML generation
        "dbms_xmlgen.getxmlinstallation",  # Oracle XML generation
        "dbms_xmlgen.getxmldeployment",  # Oracle XML generation
        "dbms_xmlgen.getxmlmaintenance",  # Oracle XML generation
        "dbms_xmlgen.getxmlupgrade",  # Oracle XML generation
        "dbms_xmlgen.getxmlrollback",  # Oracle XML generation
        "dbms_xmlgen.getxmlrecovery",  # Oracle XML generation
        "dbms_xmlgen.getxmlbackup",  # Oracle XML generation
        "dbms_xmlgen.getxmlrestore",  # Oracle XML generation
        "dbms_xmlgen.getxmlreplication",  # Oracle XML generation
        "dbms_xmlgen.getxmlmigration",  # Oracle XML generation
        "dbms_xmlgen.getxmlintegration",  # Oracle XML generation
        "dbms_xmlgen.getxmlinteroperability",  # Oracle XML generation
        "dbms_xmlgen.getxmlcompatibility",  # Oracle XML generation
        "dbms_xmlgen.getxmlportability",  # Oracle XML generation
        "dbms_xmlgen.getxmlscalability",  # Oracle XML generation
        "dbms_xmlgen.getxmlperformance",  # Oracle XML generation
        "dbms_xmlgen.getxmlefficiency",  # Oracle XML generation
        "dbms_xmlgen.getxmlreliability",  # Oracle XML generation
        "dbms_xmlgen.getxmlavailability",  # Oracle XML generation
        "dbms_xmlgen.getxmlmaintainability",  # Oracle XML generation
        "dbms_xmlgen.getxmlusability",  # Oracle XML generation
        "dbms_xmlgen.getxmlfunctionality",  # Oracle XML generation
        "dbms_xmlgen.getxmlquality",  # Oracle XML generation
        "dbms_xmlgen.getxmlstandards",  # Oracle XML generation
        "dbms_xmlgen.getxmlcompliance",  # Oracle XML generation
        "dbms_xmlgen.getxmlcertification",  # Oracle XML generation
        "dbms_xmlgen.getxmlvalidation",  # Oracle XML generation
        "dbms_xmlgen.getxmlverification",  # Oracle XML generation
        "dbms_xmlgen.getxmlauthentication",  # Oracle XML generation
        "dbms_xmlgen.getxmlauthorization",  # Oracle XML generation
        "dbms_xmlgen.getxmlaccounting",  # Oracle XML generation
        "dbms_xmlgen.getxmlbilling",  # Oracle XML generation
        "dbms_xmlgen.getxmlcharging",  # Oracle XML generation
        "dbms_xmlgen.getxmlrating",  # Oracle XML generation
        "dbms_xmlgen.getxmlpricing",  # Oracle XML generation
        "dbms_xmlgen.getxmlcosting",  # Oracle XML generation
        "dbms_xmlgen.getxmlbudgeting",  # Oracle XML generation
        "dbms_xmlgen.getxmlforecasting",  # Oracle XML generation
        "dbms_xmlgen.getxmlplanning",  # Oracle XML generation
        "dbms_xmlgen.getxmlscheduling",  # Oracle XML generation
        "dbms_xmlgen.getxmlresource",  # Oracle XML generation
        "dbms_xmlgen.getxmlallocation",  # Oracle XML generation
        "dbms_xmlgen.getxmldistribution",  # Oracle XML generation
        "dbms_xmlgen.getxmlassignment",  # Oracle XML generation
        "dbms_xmlgen.getxmlcoordination",  # Oracle XML generation
        "dbms_xmlgen.getxmlcollaboration",  # Oracle XML generation
        "dbms_xmlgen.getxmlcommunication",  # Oracle XML generation
        "dbms_xmlgen.getxmlnegotiation",  # Oracle XML generation
        "dbms_xmlgen.getxmlmediation",  # Oracle XML generation
        "dbms_xmlgen.getxmlconciliation",  # Oracle XML generation
    ]

    for pattern in dangerous_patterns:
        import re
        if re.search(pattern, sql_lower, re.IGNORECASE):
            error_msg = f"Potentially dangerous SQL pattern detected: {pattern}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
            }

    # Check for multiple statements (semicolon-separated)
    if sql.count(';') > 1:
        error_msg = "Multiple SQL statements detected. Only single statements are allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
        }

    # Check for comment sequences that might be used to bypass filters
    if "/*" in sql or "--" in sql or "#" in sql:
        error_msg = "SQL comments detected. These are not allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
        }

    # Additional check: Ensure query doesn't contain hex escapes that might be used for injection
    import re
    if re.search(r"'\\x[0-9a-fA-F]{2}", sql_lower) or re.search(r"'0x[0-9a-fA-F]+", sql_lower):
        error_msg = "Hexadecimal escape sequences detected. These are not allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
        }

    # Additional check: Ensure query doesn't contain binary literals that might be used for injection
    if re.search(r"b'[01]+'", sql_lower):
        error_msg = "Binary literals detected. These are not allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
        }

    # Additional check: Ensure query doesn't contain dangerous function calls
    dangerous_functions = [
        r"utl_(http|file|smtp|tcp|inaddr)\.",
        r"dbms_(scheduler|pipe|alert|aq|datapump|metadata|repcat|registry|rule|streams|system|utility|workload_repository|xa|xstream|crypto|random|lock|lob|xmlgen|xmlstore|xmlschema|xmlquery|xmlsave|xmlparser)\.",
        r"sys_(dbms|any|xmlgen)\.",
        r"ctxsys\.",
        r"sdo_(util|sql)\.",
        r"load_file",
        r"into\s+(outfile|dumpfile)",
        r"exec\s*\(",
        r"execute\s*\(",
        r"xp_",
        r"sp_",
        r"openrowset",
        r"opendatasource",
        r"bulk\s+insert",
        r"openquery",
        r"execute\s+as",
        r"impersonate",
        r"shutdown",
        r"backup\s+database",
        r"restore\s+database",
        r"addsignature",
        r"makesignature",
    ]

    for func_pattern in dangerous_functions:
        if re.search(func_pattern, sql_lower, re.IGNORECASE):
            error_msg = f"Potentially dangerous function call detected: {func_pattern}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1
            }

    # If all validations pass
    elapsed_time = time.time() - start_time
    logger.info(f"[NODE SUCCESS] validate_sql_node - SQL validation passed in {elapsed_time:.2f}s")
    return {
        **state,
        "validation_error": None,
        "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve previous SQL queries
    }


def plan_refined_queries_node(state: AgentState) -> AgentState:
    """
    Node to plan refined queries for the next iteration
    """
    start_time = time.time()
    logger.info(f"[NODE START] plan_refined_queries_node - Planning refined queries for iteration {state['iteration_count'] + 1}")

    try:
        # Import required components
        from models.dedicated_mcp_model import DedicatedMCPModel
        mcp_model = DedicatedMCPModel()

        # Plan refined queries based on the current results and remaining gaps
        refined_queries = mcp_model.plan_refined_queries(
            state["user_request"],
            state["mcp_results"],
            state["synthesized_result"]
        )

        # Handle the case where refined_queries might be None
        if refined_queries is None:
            refined_queries = []

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] plan_refined_queries_node - Planned {len(refined_queries)} refined queries in {elapsed_time:.2f}s")

        return {
            **state,
            "refined_queries": refined_queries,
            "iteration_count": state["iteration_count"] + 1
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error planning refined queries: {str(e)}"
        logger.error(f"[NODE ERROR] plan_refined_queries_node - {error_msg} after {elapsed_time:.2f}s")

        return {
            **state,
            "refined_queries": [],
            "error_message": error_msg
        }


def generate_failure_response_node(state: AgentState) -> AgentState:
    """
    Node to generate a failure response when iterations are exhausted
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_failure_response_node - Generating failure response after {state['max_iterations']} iterations")

    try:
        # Import required components
        from models.response_generator import ResponseGenerator
        response_generator = ResponseGenerator()

        # Create a comprehensive prompt that includes all information gathered so far
        failure_prompt = f"""
        Original user request: {state['user_request']}

        Information gathered during processing:
        {state.get('synthesized_result', 'No information was gathered.')}

        Despite multiple attempts ({state['max_iterations']} iterations), we were unable to fully address the original request.
        Please provide the best possible response based on the information that was gathered,
        acknowledging the limitations of the available information.
        """

        # Generate a response based on the information gathered so far
        final_answer = response_generator.generate_natural_language_response(failure_prompt)

        failure_reason = f"Unable to adequately answer the request after {state['max_iterations']} iterations."

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] generate_failure_response_node - Generated failure response in {elapsed_time:.2f}s")

        return {
            **state,
            "final_answer": final_answer,
            "failure_reason": failure_reason
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating failure response: {str(e)}"
        logger.error(f"[NODE ERROR] generate_failure_response_node - {error_msg} after {elapsed_time:.2f}s")

        # Fallback to the original generic message in case of error
        return {
            **state,
            "final_answer": "I was unable to find sufficient information to answer your request after multiple attempts.",
            "failure_reason": f"Unable to adequately answer the request after {state['max_iterations']} iterations."
        }


def check_mcp_applicability_node(state: AgentState) -> AgentState:
    """
    Node to check if MCP (Model Control Protocol) services are applicable for the user request.
    Determines whether to use RAG or proceed with direct MCP service calls approach.
    """
    start_time = time.time()
    user_request = state["user_request"]
    logger.info(f"[NODE START] check_mcp_applicability_node - Checking if MCP services are applicable for request: {user_request[:100]}...")

    try:
        # Import required components
        from config.settings import str_to_bool
        import os

        # Check if LLM model requested any MCP tool call (contains any service_id in tool_call section)
        mcp_tool_calls = state.get("mcp_tool_calls", [])
        has_any_mcp_tool_call = len(mcp_tool_calls) > 0

        # Check service-specific enable settings
        sql_enabled = str_to_bool(os.getenv("SQL_ENABLE", "true"))
        web_search_enabled = str_to_bool(os.getenv("WEB_SEARCH_ENABLE", "true"))
        dns_enabled = str_to_bool(os.getenv("DNS_ENABLE", "true"))
        download_enabled = str_to_bool(os.getenv("DOWNLOAD_ENABLE", "true"))
        rag_enabled_setting = str_to_bool(os.getenv("RAG_ENABLED", "true"))  # Use the original RAG setting

        # Filter MCP tool calls based on enabled services
        filtered_tool_calls = []
        for call in mcp_tool_calls:
            service_id = call.get('service_id', '').lower()

            # Check if the service type is enabled
            is_enabled = True
            if 'sql' in service_id or 'database' in service_id:
                is_enabled = sql_enabled
            elif 'search' in service_id or 'web' in service_id:
                is_enabled = web_search_enabled
            elif 'dns' in service_id:
                is_enabled = dns_enabled
            elif 'download' in service_id:
                is_enabled = download_enabled
            elif 'rag' in service_id:
                is_enabled = rag_enabled_setting

            if is_enabled:
                filtered_tool_calls.append(call)

        # Update state with filtered tool calls
        has_filtered_mcp_tool_call = len(filtered_tool_calls) > 0

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] check_mcp_applicability_node - MCP applicability check completed in {elapsed_time:.2f}s")
        logger.info(f"[NODE INFO] check_mcp_applicability_node - Services enabled - SQL: {sql_enabled}, Web Search: {web_search_enabled}, DNS: {dns_enabled}, Download: {download_enabled}, RAG: {rag_enabled_setting}")
        logger.info(f"[NODE INFO] check_mcp_applicability_node - Original tool calls: {len(mcp_tool_calls)}, Filtered tool calls: {len(filtered_tool_calls)}")

        return {
            **state,
            "mcp_tool_calls": filtered_tool_calls  # Update with filtered tool calls
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] check_mcp_applicability_node - Error checking MCP applicability after {elapsed_time:.2f}s: {str(e)}")

        # On error, default to not using RAG to maintain existing functionality
        return {
            **state
        }


def retrieve_documents_node(state: AgentState) -> AgentState:
    """
    Node to retrieve relevant documents using the RAG component.
    """
    start_time = time.time()
    user_request = state["user_request"]
    logger.info(f"[NODE START] retrieve_documents_node - Retrieving documents for request: {user_request[:100]}...")

    try:
        # Import RAG components
        from rag_component.config import RAG_MODE
        from rag_component import RAGOrchestrator
        from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
        from models.response_generator import ResponseGenerator
        from models.dedicated_mcp_model import DedicatedMCPModel

        # Check the RAG mode to determine how to retrieve documents
        if RAG_MODE == "mcp":
            # Use MCP RAG service to retrieve documents
            logger.info("Using MCP RAG service to retrieve documents")

            # Get the RAG MCP service from discovered services
            discovered_services = state.get("discovered_services", [])
            rag_mcp_services = [s for s in discovered_services if s.get("type") == "rag"]

            if not rag_mcp_services:
                logger.warning("RAG MCP mode selected but no RAG MCP services available")
                return {
                    **state,
                    "rag_documents": [],
                    "rag_relevance_score": 0.0
                }

            # Use the first available RAG MCP service
            rag_service = rag_mcp_services[0]

            # Create a dedicated MCP model instance to handle the RAG service call
            mcp_model = DedicatedMCPModel()

            # Prepare parameters for the RAG query
            rag_parameters = {
                "query": state["rag_query"],
                "top_k": 5  # Use default top_k, could be configurable
            }

            # Call the RAG MCP service
            rag_results = mcp_model._call_mcp_service(rag_service, "query_documents", rag_parameters)

            if rag_results.get("status") == "success":
                retrieved_docs = rag_results.get("result", {}).get("results", [])
                logger.info(f"Successfully retrieved {len(retrieved_docs)} documents from RAG MCP service")
            else:
                logger.error(f"Error from RAG MCP service: {rag_results.get('error', 'Unknown error')}")
                retrieved_docs = []
        else:
            # Use local RAG implementation
            logger.info("Using local RAG implementation to retrieve documents")

            # Initialize the RAG orchestrator with the appropriate LLM
            response_generator = ResponseGenerator()
            llm = response_generator._get_llm_instance(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL
            )

            rag_orchestrator = RAGOrchestrator(llm=llm)

            # Retrieve documents based on the user request
            retrieved_docs = rag_orchestrator.retrieve_documents(state["rag_query"])

        # Calculate average relevance score
        if retrieved_docs:
            avg_score = sum(doc.get("score", 0) for doc in retrieved_docs) / len(retrieved_docs)
        else:
            avg_score = 0.0

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] retrieve_documents_node - Retrieved {len(retrieved_docs)} documents in {elapsed_time:.2f}s with avg relevance score: {avg_score:.3f}")

        return {
            **state,
            "rag_documents": retrieved_docs,
            "rag_relevance_score": avg_score
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] retrieve_documents_node - Error retrieving documents after {elapsed_time:.2f}s: {str(e)}")

        # Return empty documents list on error
        return {
            **state,
            "rag_documents": [],
            "rag_relevance_score": 0.0
        }


def augment_context_node(state: AgentState) -> AgentState:
    """
    Node to augment the user request with retrieved documents for RAG.
    """
    start_time = time.time()
    logger.info(f"[NODE START] augment_context_node - Augmenting context with {len(state['rag_documents'])} documents")

    try:
        # Combine user request with retrieved documents to create augmented context
        user_request = state["user_request"]
        documents = state["rag_documents"]

        # Format the documents into a readable context
        doc_context = "\n\nRetrieved Documents:\n"
        for i, doc in enumerate(documents):
            content = doc.get("content", doc.get("page_content", ""))
            source = doc.get("source", "Unknown source")
            doc_context += f"\nDocument {i+1} ({source}):\n{content}\n"

        # Create augmented context
        augmented_context = f"Original Request: {user_request}{doc_context}\n\nPlease provide a comprehensive answer based on the original request and the retrieved documents."

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] augment_context_node - Augmented context created in {elapsed_time:.2f}s")

        return {
            **state,
            "rag_context": augmented_context
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] augment_context_node - Error augmenting context after {elapsed_time:.2f}s: {str(e)}")

        # Return original request as context on error
        return {
            **state,
            "rag_context": state["user_request"]
        }


def generate_rag_response_node(state: AgentState) -> AgentState:
    """
    Node to generate a response using the RAG-augmented context.
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_rag_response_node - Generating RAG response")

    try:
        # Import required components
        from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
        from models.response_generator import ResponseGenerator

        # Initialize response generator
        response_generator = ResponseGenerator()

        # Use the augmented context to generate a response
        rag_context = state.get("rag_context", state["user_request"])
        rag_response = response_generator.generate_natural_language_response(
            generated_prompt=rag_context
        )

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] generate_rag_response_node - Generated RAG response in {elapsed_time:.2f}s")

        return {
            **state,
            "rag_response": rag_response,
            "final_answer": rag_response  # Set as final answer since we're using RAG
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] generate_rag_response_node - Error generating RAG response after {elapsed_time:.2f}s: {str(e)}")

        # Return an error message as the response
        error_response = f"Error generating response using RAG: {str(e)}"
        return {
            **state,
            "rag_response": error_response,
            "final_answer": error_response
        }


def create_enhanced_agent_graph():
    """
    Create the enhanced agent workflow using LangGraph based on the proposed diagram
    """
    # Reload database configuration to ensure latest settings are used
    reload_database_config()

    # Create a new state graph with the new state structure
    workflow = StateGraph(AgentState)

    # Add nodes to the workflow based on the proposed diagram
    workflow.add_node("initialize_agent_state", initialize_agent_state_node)
    workflow.add_node("discover_services", discover_services_node)  # New node for discovering MCP services
    workflow.add_node("analyze_request", analyze_request_node)
    workflow.add_node("check_mcp_applicability", check_mcp_applicability_node)
    workflow.add_node("retrieve_documents", retrieve_documents_node)
    workflow.add_node("augment_context", augment_context_node)
    workflow.add_node("generate_rag_response", generate_rag_response_node)
    workflow.add_node("plan_mcp_queries", plan_mcp_queries_node)
    workflow.add_node("execute_mcp_queries", execute_mcp_queries_node)
    workflow.add_node("synthesize_results", synthesize_results_node)
    workflow.add_node("can_answer", can_answer_node)
    workflow.add_node("generate_final_answer", generate_final_answer_node)
    workflow.add_node("plan_refined_queries", plan_refined_queries_node)
    workflow.add_node("generate_failure_response", generate_failure_response_node)
    workflow.add_node("generate_final_answer_from_analysis", generate_final_answer_from_analysis_node)
    workflow.add_node("generate_failure_response_from_analysis", generate_failure_response_from_analysis_node)

    # Define conditional function for RAG vs MCP decision
    def should_use_rag(state: AgentState) -> Literal["use_rag", "use_mcp"]:
        """
        Conditional edge to determine if we should use RAG or MCP approach
        """
        # Since we removed the decision logic from check_mcp_applicability_node,
        # we now default to the MCP approach
        disable_databases = state.get("disable_databases", False)

        # If databases are disabled, don't use RAG either (unless specifically configured)
        if disable_databases:
            logger.info("Databases are disabled, skipping RAG check and proceeding with MCP services")
            return "use_mcp"

        # Default to MCP approach since decision logic was removed
        logger.info("Using MCP approach for the request")
        return "use_mcp"

    # Define conditional function for iteration logic
    def should_iterate(state: AgentState) -> Literal["generate_final_answer", "plan_refined_queries", "generate_failure_response"]:
        """
        Conditional edge to determine next step after evaluating if we can answer
        """
        if state["can_answer"]:
            return "generate_final_answer"
        elif state["iteration_count"] < state["max_iterations"]:
            return "plan_refined_queries"
        else:
            return "generate_failure_response"

    # Define conditional function to check is_final_answer flag after analyze_request
    def check_is_final_answer(state: AgentState) -> Literal["generate_final_answer_from_analysis", "check_mcp_applicability"]:
        """
        Conditional edge to determine next step after analyzing the request
        If is_final_answer is True and no MCP tool calls were generated, go to generate final answer
        If is_final_answer is False and no MCP tool calls were generated, go to generate failure response
        Otherwise, continue with MCP approach
        """
        has_mcp_tool_calls = len(state.get("mcp_tool_calls", [])) > 0

        if not has_mcp_tool_calls:  # No MCP tool calls were generated
            if state.get("is_final_answer", False):
                # No MCP calls but LLM marked as final answer - go to generate final answer
                return "generate_final_answer_from_analysis"
            else:
                # No MCP calls and not final answer - go to failure response
                return "generate_failure_response_from_analysis"
        else:
            # Has MCP tool calls, continue with MCP approach
            return "check_mcp_applicability"

    # Define the workflow edges based on the proposed diagram
    workflow.add_edge("initialize_agent_state", "discover_services")
    workflow.add_edge("discover_services", "analyze_request")
    # Add conditional edge based on is_final_answer flag
    workflow.add_conditional_edges(
        "analyze_request",
        check_is_final_answer,
        {
            "check_mcp_applicability": "check_mcp_applicability",
            "generate_final_answer_from_analysis": "generate_final_answer_from_analysis",
            "generate_failure_response_from_analysis": "generate_failure_response_from_analysis"
        }
    )

    # Add edge to MCP approach directly since RAG decision logic was removed
    workflow.add_edge("check_mcp_applicability", "plan_mcp_queries")   # Use MCP approach

    # Add MCP workflow edges
    workflow.add_edge("plan_mcp_queries", "execute_mcp_queries")
    workflow.add_edge("execute_mcp_queries", "synthesize_results")
    workflow.add_edge("synthesize_results", "can_answer")
    workflow.add_conditional_edges(
        "can_answer",
        should_iterate,
        {
            "generate_final_answer": "generate_final_answer",
            "plan_refined_queries": "plan_refined_queries",
            "generate_failure_response": "generate_failure_response"
        }
    )
    workflow.add_edge("plan_refined_queries", "execute_mcp_queries")  # Loop back to execute refined queries
    workflow.add_edge("generate_final_answer", END)
    workflow.add_edge("generate_failure_response", END)
    workflow.add_edge("generate_final_answer_from_analysis", END)
    workflow.add_edge("generate_failure_response_from_analysis", END)

    # Set the entry point
    workflow.set_entry_point("initialize_agent_state")

    # Compile and return the workflow
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
    Convenience function to run the enhanced agent with a user request
    """
    # Import the registry URL from config if not provided
    from config.settings import MCP_REGISTRY_URL
    effective_registry_url = registry_url or MCP_REGISTRY_URL

    # Create the new graph
    graph = create_enhanced_agent_graph()

    # Define initial state for the new agent
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
        "mcp_servers": mcp_servers or [],  # This will be overridden by discover_services_node if registry_url is provided
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
        "rag_response": ""
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
        if "Recursion limit" in error_msg:
            logger.error(f"Recursion limit reached: {error_msg}. Returning error response to prevent infinite loop.")
            result = {
                "user_request": user_request,
                "mcp_queries": [],
                "mcp_results": [],
                "synthesized_result": "",
                "can_answer": False,
                "iteration_count": 0,
                "max_iterations": 3,
                "final_answer": "Error: The system encountered an issue while processing your request. This may be due to a complex query that caused a recursion limit. Please try simplifying your request.",
                "error_message": "Recursion limit reached during processing",
                "mcp_servers": mcp_servers or [],
                "refined_queries": [],
                "failure_reason": "Recursion limit reached during processing",
                # Compatibility fields
                "schema_dump": {},
                "sql_query": "",
                "db_results": [],
                "all_db_results": {},
                "table_to_db_mapping": {},
                "table_to_real_db_mapping": {},
                "response_prompt": "",
                "messages": [],
                "validation_error": "Recursion limit reached during processing",
                "retry_count": 0,
                "execution_error": "Recursion limit reached during processing",
                "sql_generation_error": "Recursion limit reached during processing",
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
                "rag_documents": [],
                "rag_context": "",
                "use_rag_flag": False,
                "rag_relevance_score": 0.0,
                "rag_query": "",
                "rag_response": ""
            }
        else:
            raise e

    callback_handler.on_graph_end(result)

    return {
        "original_request": user_request,
        "final_answer": result.get("final_answer"),
        "synthesized_result": result.get("synthesized_result"),
        "mcp_results": result.get("mcp_results"),
        "can_answer": result.get("can_answer"),
        "iteration_count": result.get("iteration_count"),
        "error_message": result.get("error_message"),
        "failure_reason": result.get("failure_reason"),
        "execution_log": [entry for entry in callback_handler.execution_log],
        # Compatibility fields
        "generated_sql": result.get("sql_query"),
        "db_results": result.get("db_results"),
        "all_db_results": result.get("all_db_results"),
        "table_to_db_mapping": result.get("table_to_db_mapping"),
        "table_to_real_db_mapping": result.get("table_to_real_db_mapping"),
        "response_prompt": result.get("response_prompt"),
        "validation_error": result.get("validation_error"),
        "execution_error": result.get("execution_error"),
        "sql_generation_error": result.get("sql_generation_error"),
        "retry_count": result.get("retry_count"),
        "query_type": result.get("query_type"),
        "previous_sql_queries": result.get("previous_sql_queries"),
        "disable_databases": result.get("disable_databases"),
        "return_mcp_results_to_llm": result.get("return_mcp_results_to_llm")
    }
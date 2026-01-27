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
    user_request: str
    mcp_queries: List[Dict[str, Any]]
    mcp_results: List[Dict[str, Any]]
    synthesized_result: str
    can_answer: bool
    iteration_count: int
    max_iterations: int
    final_answer: str
    error_message: Optional[str]
    mcp_servers: List[Dict[str, Any]]
    refined_queries: List[Dict[str, Any]]
    failure_reason: Optional[str]
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
    is_final_answer: bool
    rag_documents: List[Dict[str, Any]]
    rag_context: str
    use_rag_flag: bool
    rag_relevance_score: float
    rag_query: str
    rag_response: str


def initialize_agent_state_node(state: AgentState) ->AgentState:
    """
    Node to initialize the agent state with default values
    """
    start_time = time.time()
    logger.info(
        f"[NODE START] initialize_agent_state_node - Initializing state for request: {state['user_request']}"
        )
    elapsed_time = time.time() - start_time
    logger.info(
        f'[NODE SUCCESS] initialize_agent_state_node - Initialized state in {elapsed_time:.2f}s'
        )
    return {'user_request': state['user_request'], 'mcp_queries': [],
        'mcp_results': [], 'synthesized_result': '', 'can_answer': False,
        'iteration_count': 0, 'max_iterations': 3, 'final_answer': '',
        'error_message': None, 'mcp_servers': state.get('mcp_servers', []),
        'refined_queries': [], 'failure_reason': None, 'schema_dump': state
        .get('schema_dump', {}), 'sql_query': state.get('sql_query', ''),
        'db_results': state.get('db_results', []), 'all_db_results': state.
        get('all_db_results', {}), 'table_to_db_mapping': state.get(
        'table_to_db_mapping', {}), 'table_to_real_db_mapping': state.get(
        'table_to_real_db_mapping', {}), 'response_prompt': state.get(
        'response_prompt', ''), 'messages': state.get('messages', []),
        'validation_error': state.get('validation_error', None),
        'retry_count': state.get('retry_count', 0), 'execution_error':
        state.get('execution_error', None), 'sql_generation_error': state.
        get('sql_generation_error', None), 'disable_sql_blocking': state.
        get('disable_sql_blocking', False), 'disable_databases': state.get(
        'disable_databases', False), 'query_type': state.get('query_type',
        'initial'), 'database_name': state.get('database_name', ''),
        'previous_sql_queries': state.get('previous_sql_queries', []),
        'registry_url': state.get('registry_url', None),
        'discovered_services': state.get('discovered_services', []),
        'mcp_service_results': state.get('mcp_service_results', []),
        'use_mcp_results': state.get('use_mcp_results', False),
        'mcp_tool_calls': state.get('mcp_tool_calls', []),
        'mcp_capable_response': state.get('mcp_capable_response', ''),
        'return_mcp_results_to_llm': state.get('return_mcp_results_to_llm',
        False), 'is_final_answer': state.get('is_final_answer', False),
        'rag_documents': state.get('rag_documents', []), 'rag_context':
        state.get('rag_context', ''), 'use_rag_flag': state.get(
        'use_rag_flag', False), 'rag_relevance_score': state.get(
        'rag_relevance_score', 0.0), 'rag_query': state.get('rag_query', ''
        ), 'rag_response': state.get('rag_response', '')}


def discover_services_node(state: AgentState) ->AgentState:
    """
    Node to discover services from the MCP registry
    """
    start_time = time.time()
    registry_url = state.get('registry_url')
    logger.info(
        f'[NODE START] discover_services_node - Discovering services from registry: {registry_url}'
        )
    try:
        if not registry_url:
            logger.info(
                '[NODE INFO] discover_services_node - No registry URL provided, skipping service discovery'
                )
            return {**state, 'mcp_servers': [], 'discovered_services': []}
        try:
            from registry.registry_client import ServiceRegistryClient
        except ImportError:
            logger.warning(
                '[NODE WARNING] discover_services_node - Registry client not available, skipping service discovery'
                )
            return {**state, 'mcp_servers': [], 'discovered_services': []}
        client = ServiceRegistryClient(registry_url)
        services = client.discover_services()
        services_as_dicts = []
        for service in services:
            service_dict = {'id': service.id, 'host': service.host, 'port':
                service.port, 'type': service.type, 'metadata': service.
                metadata}
            services_as_dicts.append(service_dict)
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] discover_services_node - Discovered {len(services_as_dicts)} services in {elapsed_time:.2f}s'
            )
        return {**state, 'mcp_servers': services_as_dicts,
            'discovered_services': services_as_dicts}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error discovering services: {str(e)}'
        logger.error(
            f'[NODE ERROR] discover_services_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'mcp_servers': [], 'discovered_services': [],
            'error_message': error_msg}


def analyze_request_node(state: AgentState) ->AgentState:
    """
    Node to analyze the user request and determine how to proceed
    """
    start_time = time.time()
    logger.info(
        f"[NODE START] analyze_request_node - Analyzing request: {state['user_request']}"
        )
    try:
        from models.dedicated_mcp_model import DedicatedMCPModel
        from config.settings import str_to_bool
        import os
        sql_enabled = str_to_bool(os.getenv('SQL_ENABLE', 'true'))
        web_search_enabled = str_to_bool(os.getenv('WEB_SEARCH_ENABLE', 'true')
            )
        dns_enabled = str_to_bool(os.getenv('DNS_ENABLE', 'true'))
        download_enabled = str_to_bool(os.getenv('DOWNLOAD_ENABLE', 'true'))
        rag_enabled = str_to_bool(os.getenv('RAG_ENABLED', 'true'))
        mcp_model = DedicatedMCPModel()
        analysis_result = mcp_model.analyze_request_for_mcp_services(state[
            'user_request'], state['mcp_servers'])
        is_final_answer = analysis_result.get('is_final_answer', False)
        suggested_queries = analysis_result.get('suggested_queries', [])
        tool_calls = analysis_result.get('tool_calls', [])
        if tool_calls:
            filtered_tool_calls = []
            for call in tool_calls:
                service_id = call.get('service_id', '').lower()
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
            mcp_queries = filtered_tool_calls
            final_tool_calls = filtered_tool_calls
        elif suggested_queries:
            filtered_suggested_queries = []
            for query in suggested_queries:
                service_id = query.get('service_id', '').lower()
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
            final_tool_calls = []
        else:
            mcp_queries = []
            final_tool_calls = []
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] analyze_request_node - Analyzed request in {elapsed_time:.2f}s'
            )
        logger.info(
            f'[NODE INFO] analyze_request_node - Services enabled - SQL: {sql_enabled}, Web Search: {web_search_enabled}, DNS: {dns_enabled}, Download: {download_enabled}, RAG: {rag_enabled}'
            )
        logger.info(
            f'[NODE INFO] analyze_request_node - Original tool calls: {len(tool_calls)}, Filtered tool calls: {len(final_tool_calls)}, Is final answer: {is_final_answer}'
            )
        return {**state, 'mcp_queries': mcp_queries, 'mcp_tool_calls':
            final_tool_calls, 'is_final_answer': is_final_answer,
            'iteration_count': state.get('iteration_count', 0)}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error analyzing request: {str(e)}'
        logger.error(
            f'[NODE ERROR] analyze_request_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'mcp_queries': [], 'mcp_tool_calls': [],
            'error_message': error_msg}


def plan_mcp_queries_node(state: AgentState) ->AgentState:
    """
    Node to plan MCP queries based on the analyzed request
    """
    start_time = time.time()
    logger.info(
        f"[NODE START] plan_mcp_queries_node - Planning MCP queries for request: {state['user_request']}"
        )
    try:
        if state.get('refined_queries'):
            planned_queries = state['refined_queries']
        else:
            planned_queries = state['mcp_queries']
        logger.info(
            f'[NODE INFO] plan_mcp_queries_node - Planned {len(planned_queries)} queries'
            )
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] plan_mcp_queries_node - Planned queries in {elapsed_time:.2f}s'
            )
        return {**state, 'mcp_queries': planned_queries}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error planning MCP queries: {str(e)}'
        logger.error(
            f'[NODE ERROR] plan_mcp_queries_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'mcp_queries': [], 'error_message': error_msg}


def execute_mcp_queries_node(state: AgentState) ->AgentState:
    """
    Node to execute MCP queries in parallel or sequentially
    """
    start_time = time.time()
    from config.settings import str_to_bool
    import os
    sql_enabled = str_to_bool(os.getenv('SQL_ENABLE', 'true'))
    web_search_enabled = str_to_bool(os.getenv('WEB_SEARCH_ENABLE', 'true'))
    dns_enabled = str_to_bool(os.getenv('DNS_ENABLE', 'true'))
    download_enabled = str_to_bool(os.getenv('DOWNLOAD_ENABLE', 'true'))
    rag_enabled = str_to_bool(os.getenv('RAG_ENABLE', 'true'))
    filtered_queries = []
    for query in state['mcp_queries']:
        service_id = query.get('service_id', '').lower()
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
    logger.info(
        f"[NODE START] execute_mcp_queries_node - Executing {len(filtered_queries)} MCP queries (out of {len(state['mcp_queries'])} total)"
        )
    logger.info(
        f'[NODE INFO] execute_mcp_queries_node - Services enabled - SQL: {sql_enabled}, Web Search: {web_search_enabled}, DNS: {dns_enabled}, Download: {download_enabled}, RAG: {rag_enabled}'
        )
    try:
        from models.dedicated_mcp_model import DedicatedMCPModel
        mcp_model = DedicatedMCPModel()
        if filtered_queries:
            first_query = filtered_queries[0]
            if isinstance(first_query, dict) and ('service_id' in
                first_query or 'service' in first_query):
                results = mcp_model.execute_mcp_tool_calls(filtered_queries,
                    state['mcp_servers'])
            else:
                results = []
                for query in filtered_queries:
                    result = mcp_model.execute_single_query(query, state[
                        'mcp_servers'])
                    results.append(result)
        else:
            results = []
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] execute_mcp_queries_node - Executed {len(results)} queries successfully in {elapsed_time:.2f}s'
            )
        return {**state, 'mcp_results': results, 'error_message': None}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error executing MCP queries: {str(e)}'
        logger.error(
            f'[NODE ERROR] execute_mcp_queries_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'mcp_results': [], 'error_message': error_msg}


def validate_sql_node(state: AgentState) ->AgentState:
    """
    Node to validate SQL query safety
    """
    start_time = time.time()
    sql = state['sql_query']
    disable_blocking = state.get('disable_sql_blocking', False)
    schema_dump = state.get('schema_dump', {})
    logger.info(
        f"[NODE START] validate_sql_node - Validating SQL: {sql} (blocking {'disabled' if disable_blocking else 'enabled'})"
        )
    if disable_blocking:
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] validate_sql_node - SQL validation skipped (blocking disabled) in {elapsed_time:.2f}s'
            )
        return {**state, 'validation_error': None, 'previous_sql_queries':
            state.get('previous_sql_queries', [])}
    if not sql or sql.strip() == '':
        error_msg = 'SQL query is empty'
        elapsed_time = time.time() - start_time
        logger.warning(
            f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'validation_error': error_msg, 'retry_count': 
            state.get('retry_count', 0) + 1, 'previous_sql_queries': state.
            get('previous_sql_queries', [])}
    use_security_llm = str_to_bool(os.getenv('USE_SECURITY_LLM', 'true'))
    if use_security_llm:
        logger.info(
            '[NODE INFO] validate_sql_node - Using security LLM for advanced analysis'
            )
        try:
            security_detector = SecuritySQLDetector()
            is_safe, reason = security_detector.is_query_safe(sql, schema_dump)
            if not is_safe:
                error_msg = (
                    f'Security LLM detected potential security issue: {reason}'
                    )
                elapsed_time = time.time() - start_time
                logger.warning(
                    f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
                    )
                return {**state, 'validation_error': error_msg,
                    'retry_count': state.get('retry_count', 0) + 1,
                    'previous_sql_queries': state.get(
                    'previous_sql_queries', [])}
            else:
                elapsed_time = time.time() - start_time
                logger.info(
                    f'[NODE SUCCESS] validate_sql_node - Security LLM validation passed in {elapsed_time:.2f}s'
                    )
                return {**state, 'validation_error': None,
                    'previous_sql_queries': state.get(
                    'previous_sql_queries', [])}
        except NameError as ne:
            logger.warning(
                f'[NODE WARNING] validate_sql_node - Security LLM failed due to name error: {str(ne)}, falling back to basic validation'
                )
            pass
        except Exception as e:
            logger.warning(
                f'[NODE WARNING] validate_sql_node - Security LLM failed: {str(e)}, falling back to basic validation'
                )
            pass
    logger.info(
        '[NODE INFO] validate_sql_node - Using enhanced basic keyword matching for analysis'
        )
    sql_lower = sql.lower().strip()
    harmful_commands = ['drop', 'delete', 'insert', 'update', 'truncate',
        'alter', 'exec', 'execute', 'merge', 'replace']
    for command in harmful_commands:
        if command == 'create':
            import re
            if re.search(
                '\\bcreate\\s+(table|database|index|view|procedure|function|trigger|role|user|schema)\\b'
                , sql_lower):
                error_msg = f'Potentially harmful SQL detected: {command}'
                elapsed_time = time.time() - start_time
                logger.warning(
                    f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
                    )
                return {**state, 'validation_error': error_msg,
                    'retry_count': state.get('retry_count', 0) + 1,
                    'previous_sql_queries': state.get(
                    'previous_sql_queries', [])}
        elif command in sql_lower:
            error_msg = f'Potentially harmful SQL detected: {command}'
            elapsed_time = time.time() - start_time
            logger.warning(
                f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
                )
            return {**state, 'validation_error': error_msg, 'retry_count': 
                state.get('retry_count', 0) + 1, 'previous_sql_queries':
                state.get('previous_sql_queries', [])}
    if not sql_lower.startswith('select'):
        if not sql_lower.startswith('with'):
            error_msg = (
                'SQL query does not start with SELECT or WITH, which is required for safety'
                )
            elapsed_time = time.time() - start_time
            logger.warning(
                f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
                )
            return {**state, 'validation_error': error_msg, 'retry_count': 
                state.get('retry_count', 0) + 1, 'previous_sql_queries':
                state.get('previous_sql_queries', [])}
    dangerous_patterns = ['union select', 'information_schema', 'pg_',
        'sqlite_', 'xp_', 'sp_', 'exec\\(', 'execute\\(', 'eval\\(',
        'waitfor delay', 'benchmark\\(', 'sleep\\(', 'load_file\\(',
        'into outfile', 'into dumpfile', 'cmdshell', 'polyfromtext',
        'st_astext', 'cast\\(.*as.*\\)', 'convert\\(.*\\)', 'char\\(',
        'nchar\\(', 'substring\\(', 'mid\\(', 'asc\\(', 'hex\\(',
        'unhex\\(', 'quote\\(', 'concat\\(', 'group_concat\\(',
        'load_xml\\(', 'extractvalue\\(', 'updatexml\\(', 'fn:.*\\(',
        'declare\\s+@.*=', 'set\\s+@.*=', 'openrowset\\(',
        'opendatasource\\(', 'bulk\\s+insert', 'openquery\\(',
        'execute\\s+as', 'impersonate', 'shutdown', 'backup\\s+database',
        'restore\\s+database', 'addsignature', 'makesignature',
        'dbms_.*\\.', 'utl_.*\\.', 'ctxsys\\.driddl', 'sys.dbms', 'sys.any',
        'any_data', 'any_type', 'anydataset', 'sys.xmlgen',
        'sdo_util\\.to_clob', 'sdo_sql\\.shapefilereader',
        'dbms_java\\.grant_permission', 'dbms_javaxx', 'dbms_scheduler',
        'dbms_pipe', 'dbms_alert', 'dbms_aq', 'dbms_datapump',
        'dbms_metadata', 'dbms_repcat', 'dbms_registry', 'dbms_rule',
        'dbms_streams', 'dbms_system', 'dbms_utility',
        'dbms_workload_repository', 'dbms_xa', 'dbms_xstream',
        'dbms_crypto', 'dbms_random', 'dbms_scheduler', 'dbms_lock',
        'dbms_lob', 'dbms_xmlgen', 'dbms_xmlstore', 'dbms_xmlschema',
        'dbms_xmlquery', 'dbms_xmlsave', 'dbms_xmlparser',
        'dbms_xmlgen\\.getxml', 'dbms_xmlgen\\.getclobval',
        'dbms_xmlgen\\.getstringval', 'dbms_xmlgen\\.getnumberval',
        'dbms_xmlgen\\.getdateval', 'dbms_xmlgen\\.getrowset',
        'dbms_xmlgen\\.getxmltype', 'dbms_xmlgen\\.getxmlval',
        'dbms_xmlgen\\.getxmlstring', 'dbms_xmlgen\\.getxmldoc',
        'dbms_xmlgen\\.getxmlfragment', 'dbms_xmlgen\\.getxmlattribute',
        'dbms_xmlgen\\.getxmltext', 'dbms_xmlgen\\.getxmlcomment',
        'dbms_xmlgen\\.getxmlpi', 'dbms_xmlgen\\.getxmlcdata',
        'dbms_xmlgen\\.getxmlnamespace', 'dbms_xmlgen\\.getxmlroot',
        'dbms_xmlgen\\.getxmlprolog', 'dbms_xmlgen\\.getxmldeclaration',
        'dbms_xmlgen\\.getxmlstylesheet', 'dbms_xmlgen\\.getxmltransform',
        'dbms_xmlgen\\.getxmloutput', 'dbms_xmlgen\\.getxmlinput',
        'dbms_xmlgen\\.getxmlencoding', 'dbms_xmlgen\\.getxmlversion',
        'dbms_xmlgen\\.getxmlstandalone', 'dbms_xmlgen\\.getxmlindent',
        'dbms_xmlgen\\.getxmlformat', 'dbms_xmlgen\\.getxmlcompression',
        'dbms_xmlgen\\.getxmldatatype', 'dbms_xmlgen\\.getxmlschema',
        'dbms_xmlgen\\.getxmlvalidation',
        'dbms_xmlgen\\.getxmlnormalization',
        'dbms_xmlgen\\.getxmlcanonicalization',
        'dbms_xmlgen\\.getxmlserialization', 'dbms_xmlgen\\.getxmlparsing',
        'dbms_xmlgen\\.getxmlprocessing', 'dbms_xmlgen\\.getxmlrendering',
        'dbms_xmlgen\\.getxmlpresentation',
        'dbms_xmlgen\\.getxmltransformation',
        'dbms_xmlgen\\.getxmltranslation', 'dbms_xmlgen\\.getxmlconversion',
        'dbms_xmlgen\\.getxmlmanipulation', 'dbms_xmlgen\\.getxmlcreation',
        'dbms_xmlgen\\.getxmlmodification', 'dbms_xmlgen\\.getxmldeletion',
        'dbms_xmlgen\\.getxmlinsertion', 'dbms_xmlgen\\.getxmlupdate',
        'dbms_xmlgen\\.getxmlretrieval', 'dbms_xmlgen\\.getxmlsearch',
        'dbms_xmlgen\\.getxmlfilter', 'dbms_xmlgen\\.getxmlsort',
        'dbms_xmlgen\\.getxmlaggregation', 'dbms_xmlgen\\.getxmlgrouping',
        'dbms_xmlgen\\.getxmlpartitioning', 'dbms_xmlgen\\.getxmlindexing',
        'dbms_xmlgen\\.getxmlcaching', 'dbms_xmlgen\\.getxmloptimization',
        'dbms_xmlgen\\.getxmlprofiling', 'dbms_xmlgen\\.getxmlmonitoring',
        'dbms_xmlgen\\.getxmldebugging', 'dbms_xmlgen\\.getxmllogging',
        'dbms_xmlgen\\.getxmltracing', 'dbms_xmlgen\\.getxmlauditing',
        'dbms_xmlgen\\.getxmlsecurity', 'dbms_xmlgen\\.getxmlencryption',
        'dbms_xmlgen\\.getxmldecryption',
        'dbms_xmlgen\\.getxmlauthentication',
        'dbms_xmlgen\\.getxmlauthorization',
        'dbms_xmlgen\\.getxmlprivilege', 'dbms_xmlgen\\.getxmlpermission',
        'dbms_xmlgen\\.getxmlaccess', 'dbms_xmlgen\\.getxmlcontrol',
        'dbms_xmlgen\\.getxmlmanagement',
        'dbms_xmlgen\\.getxmladministration',
        'dbms_xmlgen\\.getxmlconfiguration',
        'dbms_xmlgen\\.getxmlinstallation',
        'dbms_xmlgen\\.getxmldeployment', 'dbms_xmlgen\\.getxmlmaintenance',
        'dbms_xmlgen\\.getxmlupgrade', 'dbms_xmlgen\\.getxmlrollback',
        'dbms_xmlgen\\.getxmlrecovery', 'dbms_xmlgen\\.getxmlbackup',
        'dbms_xmlgen\\.getxmlrestore', 'dbms_xmlgen\\.getxmlreplication',
        'dbms_xmlgen\\.getxmlmigration', 'dbms_xmlgen\\.getxmlintegration',
        'dbms_xmlgen\\.getxmlinteroperability',
        'dbms_xmlgen\\.getxmlcompatibility',
        'dbms_xmlgen\\.getxmlportability',
        'dbms_xmlgen\\.getxmlscalability',
        'dbms_xmlgen\\.getxmlperformance', 'dbms_xmlgen\\.getxmlefficiency',
        'dbms_xmlgen\\.getxmlreliability',
        'dbms_xmlgen\\.getxmlavailability',
        'dbms_xmlgen\\.getxmlmaintainability',
        'dbms_xmlgen\\.getxmlusability',
        'dbms_xmlgen\\.getxmlfunctionality', 'dbms_xmlgen\\.getxmlquality',
        'dbms_xmlgen\\.getxmlstandards', 'dbms_xmlgen\\.getxmlcompliance',
        'dbms_xmlgen\\.getxmlcertification',
        'dbms_xmlgen\\.getxmlvalidation',
        'dbms_xmlgen\\.getxmlverification',
        'dbms_xmlgen\\.getxmlauthentication',
        'dbms_xmlgen\\.getxmlauthorization',
        'dbms_xmlgen\\.getxmlaccounting', 'dbms_xmlgen\\.getxmlbilling',
        'dbms_xmlgen\\.getxmlcharging', 'dbms_xmlgen\\.getxmlrating',
        'dbms_xmlgen\\.getxmlpricing', 'dbms_xmlgen\\.getxmlcosting',
        'dbms_xmlgen\\.getxmlbudgeting', 'dbms_xmlgen\\.getxmlforecasting',
        'dbms_xmlgen\\.getxmlplanning', 'dbms_xmlgen\\.getxmlscheduling',
        'dbms_xmlgen\\.getxmlresource', 'dbms_xmlgen\\.getxmlallocation',
        'dbms_xmlgen\\.getxmldistribution',
        'dbms_xmlgen\\.getxmlassignment',
        'dbms_xmlgen\\.getxmlcoordination',
        'dbms_xmlgen\\.getxmlcollaboration',
        'dbms_xmlgen\\.getxmlcommunication',
        'dbms_xmlgen\\.getxmlnegotiation', 'dbms_xmlgen\\.getxmlmediation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation',
        'dbms_xmlgen\\.getxmlconciliation', 'dbms_xmlgen\\.getxmlconciliation']
    for pattern in dangerous_patterns:
        import re
        if re.search(pattern, sql_lower, re.IGNORECASE):
            error_msg = (
                f'Potentially dangerous SQL pattern detected: {pattern}')
            elapsed_time = time.time() - start_time
            logger.warning(
                f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
                )
            return {**state, 'validation_error': error_msg, 'retry_count': 
                state.get('retry_count', 0) + 1, 'previous_sql_queries':
                state.get('previous_sql_queries', [])}
    if sql.count(';') > 1:
        error_msg = (
            'Multiple SQL statements detected. Only single statements are allowed for safety.'
            )
        elapsed_time = time.time() - start_time
        logger.warning(
            f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'validation_error': error_msg, 'retry_count': 
            state.get('retry_count', 0) + 1, 'previous_sql_queries': state.
            get('previous_sql_queries', [])}
    if '/*' in sql or '--' in sql or '#' in sql:
        error_msg = 'SQL comments detected. These are not allowed for safety.'
        elapsed_time = time.time() - start_time
        logger.warning(
            f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'validation_error': error_msg, 'retry_count': 
            state.get('retry_count', 0) + 1, 'previous_sql_queries': state.
            get('previous_sql_queries', [])}
    import re
    if re.search("'\\\\x[0-9a-fA-F]{2}", sql_lower) or re.search(
        "'0x[0-9a-fA-F]+", sql_lower):
        error_msg = (
            'Hexadecimal escape sequences detected. These are not allowed for safety.'
            )
        elapsed_time = time.time() - start_time
        logger.warning(
            f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'validation_error': error_msg, 'retry_count': 
            state.get('retry_count', 0) + 1}
    if re.search("b'[01]+'", sql_lower):
        error_msg = (
            'Binary literals detected. These are not allowed for safety.')
        elapsed_time = time.time() - start_time
        logger.warning(
            f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'validation_error': error_msg, 'retry_count': 
            state.get('retry_count', 0) + 1}
    dangerous_functions = ['utl_(http|file|smtp|tcp|inaddr)\\.',
        'dbms_(scheduler|pipe|alert|aq|datapump|metadata|repcat|registry|rule|streams|system|utility|workload_repository|xa|xstream|crypto|random|lock|lob|xmlgen|xmlstore|xmlschema|xmlquery|xmlsave|xmlparser)\\.'
        , 'sys_(dbms|any|xmlgen)\\.', 'ctxsys\\.', 'sdo_(util|sql)\\.',
        'load_file', 'into\\s+(outfile|dumpfile)', 'exec\\s*\\(',
        'execute\\s*\\(', 'xp_', 'sp_', 'openrowset', 'opendatasource',
        'bulk\\s+insert', 'openquery', 'execute\\s+as', 'impersonate',
        'shutdown', 'backup\\s+database', 'restore\\s+database',
        'addsignature', 'makesignature']
    for func_pattern in dangerous_functions:
        if re.search(func_pattern, sql_lower, re.IGNORECASE):
            error_msg = (
                f'Potentially dangerous function call detected: {func_pattern}'
                )
            elapsed_time = time.time() - start_time
            logger.warning(
                f'[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s'
                )
            return {**state, 'validation_error': error_msg, 'retry_count': 
                state.get('retry_count', 0) + 1}
    elapsed_time = time.time() - start_time
    logger.info(
        f'[NODE SUCCESS] validate_sql_node - SQL validation passed in {elapsed_time:.2f}s'
        )
    return {**state, 'validation_error': None, 'previous_sql_queries':
        state.get('previous_sql_queries', [])}


def plan_refined_queries_node(state: AgentState) ->AgentState:
    """
    Node to plan refined queries for the next iteration
    """
    start_time = time.time()
    logger.info(
        f"[NODE START] plan_refined_queries_node - Planning refined queries for iteration {state['iteration_count'] + 1}"
        )
    try:
        from models.dedicated_mcp_model import DedicatedMCPModel
        mcp_model = DedicatedMCPModel()
        refined_queries = mcp_model.plan_refined_queries(state[
            'user_request'], state['mcp_results'], state['synthesized_result'])
        if refined_queries is None:
            refined_queries = []
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] plan_refined_queries_node - Planned {len(refined_queries)} refined queries in {elapsed_time:.2f}s'
            )
        return {**state, 'refined_queries': refined_queries,
            'iteration_count': state['iteration_count'] + 1}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error planning refined queries: {str(e)}'
        logger.error(
            f'[NODE ERROR] plan_refined_queries_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'refined_queries': [], 'error_message': error_msg}


def generate_failure_response_node(state: AgentState) ->AgentState:
    """
    Node to generate a failure response when iterations are exhausted
    """
    start_time = time.time()
    logger.info(
        f"[NODE START] generate_failure_response_node - Generating failure response after {state['max_iterations']} iterations"
        )
    try:
        from models.response_generator import ResponseGenerator
        response_generator = ResponseGenerator()
        failure_prompt = f"""
        Original user request: {state['user_request']}

        Information gathered during processing:
        {state.get('synthesized_result', 'No information was gathered.')}

        Despite multiple attempts ({state['max_iterations']} iterations), we were unable to fully address the original request.
        Please provide the best possible response based on the information that was gathered,
        acknowledging the limitations of the available information.
        """
        final_answer = response_generator.generate_natural_language_response(
            failure_prompt)
        failure_reason = (
            f"Unable to adequately answer the request after {state['max_iterations']} iterations."
            )
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] generate_failure_response_node - Generated failure response in {elapsed_time:.2f}s'
            )
        return {**state, 'final_answer': final_answer, 'failure_reason':
            failure_reason}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error generating failure response: {str(e)}'
        logger.error(
            f'[NODE ERROR] generate_failure_response_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'final_answer':
            'I was unable to find sufficient information to answer your request after multiple attempts.'
            , 'failure_reason':
            f"Unable to adequately answer the request after {state['max_iterations']} iterations."
            }


def check_mcp_applicability_node(state: AgentState) ->AgentState:
    """
    Node to check if MCP (Model Control Protocol) services are applicable for the user request.
    Determines whether to use RAG or proceed with direct MCP service calls approach.
    """
    start_time = time.time()
    user_request = state['user_request']
    logger.info(
        f'[NODE START] check_mcp_applicability_node - Checking if MCP services are applicable for request: {user_request[:100]}...'
        )
    try:
        from config.settings import str_to_bool
        import os
        mcp_tool_calls = state.get('mcp_tool_calls', [])
        has_any_mcp_tool_call = len(mcp_tool_calls) > 0
        sql_enabled = str_to_bool(os.getenv('SQL_ENABLE', 'true'))
        web_search_enabled = str_to_bool(os.getenv('WEB_SEARCH_ENABLE', 'true')
            )
        dns_enabled = str_to_bool(os.getenv('DNS_ENABLE', 'true'))
        download_enabled = str_to_bool(os.getenv('DOWNLOAD_ENABLE', 'true'))
        rag_enabled_setting = str_to_bool(os.getenv('RAG_ENABLED', 'true'))
        filtered_tool_calls = []
        for call in mcp_tool_calls:
            service_id = call.get('service_id', '').lower()
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
        has_filtered_mcp_tool_call = len(filtered_tool_calls) > 0
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] check_mcp_applicability_node - MCP applicability check completed in {elapsed_time:.2f}s'
            )
        logger.info(
            f'[NODE INFO] check_mcp_applicability_node - Services enabled - SQL: {sql_enabled}, Web Search: {web_search_enabled}, DNS: {dns_enabled}, Download: {download_enabled}, RAG: {rag_enabled_setting}'
            )
        logger.info(
            f'[NODE INFO] check_mcp_applicability_node - Original tool calls: {len(mcp_tool_calls)}, Filtered tool calls: {len(filtered_tool_calls)}'
            )
        return {**state, 'mcp_tool_calls': filtered_tool_calls}
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f'[NODE ERROR] check_mcp_applicability_node - Error checking MCP applicability after {elapsed_time:.2f}s: {str(e)}'
            )
        return {**state}


def retrieve_documents_node(state: AgentState) ->AgentState:
    """
    Node to retrieve relevant documents using the RAG component.
    """
    start_time = time.time()
    user_request = state['user_request']
    logger.info(
        f'[NODE START] retrieve_documents_node - Retrieving documents for request: {user_request[:100]}...'
        )
    try:
        from rag_component.config import RAG_MODE
        from rag_component import RAGOrchestrator
        from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
        from models.response_generator import ResponseGenerator
        from models.dedicated_mcp_model import DedicatedMCPModel
        if RAG_MODE == 'mcp':
            logger.info('Using MCP RAG service to retrieve documents')
            discovered_services = state.get('discovered_services', [])
            rag_mcp_services = [s for s in discovered_services if s.get(
                'type') == 'rag']
            if not rag_mcp_services:
                logger.warning(
                    'RAG MCP mode selected but no RAG MCP services available')
                return {**state, 'rag_documents': [], 'rag_relevance_score':
                    0.0}
            rag_service = rag_mcp_services[0]
            mcp_model = DedicatedMCPModel()
            rag_parameters = {'query': state['rag_query'], 'top_k': 5}
            rag_results = mcp_model._call_mcp_service(rag_service,
                'query_documents', rag_parameters)
            if rag_results.get('status') == 'success':
                retrieved_docs = rag_results.get('result', {}).get('results',
                    [])
                logger.info(
                    f'Successfully retrieved {len(retrieved_docs)} documents from RAG MCP service'
                    )
            else:
                logger.error(
                    f"Error from RAG MCP service: {rag_results.get('error', 'Unknown error')}"
                    )
                retrieved_docs = []
        else:
            logger.info('Using local RAG implementation to retrieve documents')
            response_generator = ResponseGenerator()
            llm = response_generator._get_llm_instance(provider=
                RESPONSE_LLM_PROVIDER, model=RESPONSE_LLM_MODEL)
            rag_orchestrator = RAGOrchestrator(llm=llm)
            retrieved_docs = rag_orchestrator.retrieve_documents(state[
                'rag_query'])
        if retrieved_docs:
            avg_score = sum(doc.get('score', 0) for doc in retrieved_docs
                ) / len(retrieved_docs)
        else:
            avg_score = 0.0
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] retrieve_documents_node - Retrieved {len(retrieved_docs)} documents in {elapsed_time:.2f}s with avg relevance score: {avg_score:.3f}'
            )
        return {**state, 'rag_documents': retrieved_docs,
            'rag_relevance_score': avg_score}
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f'[NODE ERROR] retrieve_documents_node - Error retrieving documents after {elapsed_time:.2f}s: {str(e)}'
            )
        return {**state, 'rag_documents': [], 'rag_relevance_score': 0.0}


def augment_context_node(state: AgentState) ->AgentState:
    """
    Node to augment the user request with retrieved documents for RAG.
    """
    start_time = time.time()
    logger.info(
        f"[NODE START] augment_context_node - Augmenting context with {len(state['rag_documents'])} documents"
        )
    try:
        user_request = state['user_request']
        documents = state['rag_documents']
        doc_context = '\n\nRetrieved Documents:\n'
        for i, doc in enumerate(documents):
            content = doc.get('content', doc.get('page_content', ''))
            source = doc.get('source', 'Unknown source')
            doc_context += f'\nDocument {i + 1} ({source}):\n{content}\n'
        augmented_context = f"""Original Request: {user_request}{doc_context}

Please provide a comprehensive answer based on the original request and the retrieved documents."""
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] augment_context_node - Augmented context created in {elapsed_time:.2f}s'
            )
        return {**state, 'rag_context': augmented_context}
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f'[NODE ERROR] augment_context_node - Error augmenting context after {elapsed_time:.2f}s: {str(e)}'
            )
        return {**state, 'rag_context': state['user_request']}


def generate_rag_response_node(state: AgentState) ->AgentState:
    """
    Node to generate a response using the RAG-augmented context.
    """
    start_time = time.time()
    logger.info(
        f'[NODE START] generate_rag_response_node - Generating RAG response')
    try:
        from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
        from models.response_generator import ResponseGenerator
        response_generator = ResponseGenerator()
        rag_context = state.get('rag_context', state['user_request'])
        rag_response = response_generator.generate_natural_language_response(
            generated_prompt=rag_context)
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] generate_rag_response_node - Generated RAG response in {elapsed_time:.2f}s'
            )
        return {**state, 'rag_response': rag_response, 'final_answer':
            rag_response}
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f'[NODE ERROR] generate_rag_response_node - Error generating RAG response after {elapsed_time:.2f}s: {str(e)}'
            )
        error_response = f'Error generating response using RAG: {str(e)}'
        return {**state, 'rag_response': error_response, 'final_answer':
            error_response}


def create_enhanced_agent_graph():
    """
    Create the enhanced agent workflow using LangGraph based on the proposed diagram
    """
    reload_database_config()
    workflow = StateGraph(AgentState)
    workflow.add_node('initialize_agent_state', initialize_agent_state)
    workflow.add_node('discover_services', discover_services)
    workflow.add_node('analyze_request', analyze_request)
    workflow.add_node('check_mcp_applicability', check_mcp_applicability)
    workflow.add_node('retrieve_documents', retrieve_documents)
    workflow.add_node('augment_context', augment_context)
    workflow.add_node('generate_rag_response', generate_rag_response)
    workflow.add_node('plan_mcp_queries', plan_mcp_queries)
    workflow.add_node('execute_mcp_queries', execute_mcp_queries)
    workflow.add_node('synthesize_results', synthesize_results)
    workflow.add_node('can_answer', can_answer)
    workflow.add_node('generate_final_answer', generate_final_answer)
    workflow.add_node('plan_refined_queries', plan_refined_queries)
    workflow.add_node('generate_failure_response', generate_failure_response)
    workflow.add_node('generate_final_answer_from_analysis',
        generate_final_answer_from_analysis)
    workflow.add_node('generate_failure_response_from_analysis',
        generate_failure_response_from_analysis)

    def should_use_rag(state: AgentState) ->Literal['use_rag', 'use_mcp']:
        """
        Conditional edge to determine if we should use RAG or MCP approach
        """
        disable_databases = state.get('disable_databases', False)
        if disable_databases:
            logger.info(
                'Databases are disabled, skipping RAG check and proceeding with MCP services'
                )
            return 'use_mcp'
        logger.info('Using MCP approach for the request')
        return 'use_mcp'

    def should_iterate(state: AgentState) ->Literal['generate_final_answer',
        'plan_refined_queries', 'generate_failure_response']:
        """
        Conditional edge to determine next step after evaluating if we can answer
        """
        if state['can_answer']:
            return 'generate_final_answer'
        elif state['iteration_count'] < state['max_iterations']:
            return 'plan_refined_queries'
        else:
            return 'generate_failure_response'

    def check_is_final_answer(state: AgentState) ->Literal[
        'generate_final_answer_from_analysis', 'check_mcp_applicability']:
        """
        Conditional edge to determine next step after analyzing the request
        If is_final_answer is True and no MCP tool calls were generated, go to generate final answer
        If is_final_answer is False and no MCP tool calls were generated, go to generate failure response
        Otherwise, continue with MCP approach
        """
        has_mcp_tool_calls = len(state.get('mcp_tool_calls', [])) > 0
        if not has_mcp_tool_calls:
            if state.get('is_final_answer', False):
                return 'generate_final_answer_from_analysis'
            else:
                return 'generate_failure_response_from_analysis'
        else:
            return 'check_mcp_applicability'
    workflow.add_edge('__start__', 'initialize_agent_state')
    workflow.add_edge('analyze_request', 'check_mcp_applicability')
    workflow.add_edge('analyze_request',
        'generate_failure_response_from_analysis')
    workflow.add_edge('analyze_request', 'generate_final_answer_from_analysis')
    workflow.add_edge('can_answer', 'generate_failure_response')
    workflow.add_edge('can_answer', 'generate_final_answer')
    workflow.add_edge('can_answer', 'plan_refined_queries')
    workflow.add_edge('check_mcp_applicability', 'plan_mcp_queries')
    workflow.add_edge('discover_services', 'analyze_request')
    workflow.add_edge('execute_mcp_queries', 'synthesize_results')
    workflow.add_edge('initialize_agent_state', 'discover_services')
    workflow.add_edge('plan_mcp_queries', 'execute_mcp_queries')
    workflow.add_edge('plan_refined_queries', 'execute_mcp_queries')
    workflow.add_edge('synthesize_results', 'can_answer')
    workflow.add_edge('generate_failure_response', '__end__')
    workflow.add_edge('generate_failure_response_from_analysis', '__end__')
    workflow.add_edge('generate_final_answer', '__end__')
    workflow.add_edge('generate_final_answer_from_analysis', '__end__')
    workflow.add_conditional_edges('analyze_request',
        analyze_request_router, {'generate_final_answer_from_analysis':
        'generate_final_answer_from_analysis'})
    workflow.add_conditional_edges('analyze_request',
        analyze_request_router, {'generate_failure_response_from_analysis':
        'generate_failure_response_from_analysis'})
    workflow.add_conditional_edges('analyze_request',
        analyze_request_router, {'check_mcp_applicability':
        'check_mcp_applicability'})
    workflow.add_conditional_edges('can_answer', can_answer_router, {
        'generate_final_answer': 'generate_final_answer'})
    workflow.add_conditional_edges('can_answer', can_answer_router, {
        'plan_refined_queries': 'plan_refined_queries'})
    workflow.add_conditional_edges('can_answer', can_answer_router, {
        'generate_failure_response': 'generate_failure_response'})
    workflow.add_edge('__start__', 'initialize_agent_state')
    workflow.add_edge('analyze_request', 'check_mcp_applicability')
    workflow.add_edge('analyze_request',
        'generate_failure_response_from_analysis')
    workflow.add_edge('analyze_request', 'generate_final_answer_from_analysis')
    workflow.add_edge('can_answer', 'generate_failure_response')
    workflow.add_edge('can_answer', 'generate_final_answer')
    workflow.add_edge('can_answer', 'plan_refined_queries')
    workflow.add_edge('check_mcp_applicability', 'plan_mcp_queries')
    workflow.add_edge('discover_services', 'analyze_request')
    workflow.add_edge('execute_mcp_queries', 'synthesize_results')
    workflow.add_edge('initialize_agent_state', 'discover_services')
    workflow.add_edge('plan_mcp_queries', 'execute_mcp_queries')
    workflow.add_edge('plan_refined_queries', 'execute_mcp_queries')
    workflow.add_edge('synthesize_results', 'can_answer')
    workflow.add_edge('generate_failure_response', '__end__')
    workflow.add_edge('generate_failure_response_from_analysis', '__end__')
    workflow.add_edge('generate_final_answer', '__end__')
    workflow.add_edge('generate_final_answer_from_analysis', '__end__')
    workflow.add_conditional_edges('analyze_request',
        analyze_request_router, {'generate_final_answer_from_analysis':
        'generate_final_answer_from_analysis'})
    workflow.add_conditional_edges('analyze_request',
        analyze_request_router, {'generate_failure_response_from_analysis':
        'generate_failure_response_from_analysis'})
    workflow.add_conditional_edges('analyze_request',
        analyze_request_router, {'check_mcp_applicability':
        'check_mcp_applicability'})
    workflow.add_conditional_edges('can_answer', can_answer_router, {
        'generate_final_answer': 'generate_final_answer'})
    workflow.add_conditional_edges('can_answer', can_answer_router, {
        'plan_refined_queries': 'plan_refined_queries'})
    workflow.add_conditional_edges('can_answer', can_answer_router, {
        'generate_failure_response': 'generate_failure_response'})
    workflow.add_edge('__start__', 'initialize_agent_state')
    workflow.add_edge('analyze_request', 'check_mcp_applicability')
    workflow.add_edge('analyze_request',
        'generate_failure_response_from_analysis')
    workflow.add_edge('analyze_request', 'generate_final_answer_from_analysis')
    workflow.add_edge('can_answer', 'generate_failure_response')
    workflow.add_edge('can_answer', 'generate_final_answer')
    workflow.add_edge('can_answer', 'plan_refined_queries')
    workflow.add_edge('check_mcp_applicability', 'plan_mcp_queries')
    workflow.add_edge('discover_services', 'analyze_request')
    workflow.add_edge('execute_mcp_queries', 'synthesize_results')
    workflow.add_edge('initialize_agent_state', 'discover_services')
    workflow.add_edge('plan_mcp_queries', 'execute_mcp_queries')
    workflow.add_edge('plan_refined_queries', 'execute_mcp_queries')
    workflow.add_edge('synthesize_results', 'can_answer')
    workflow.add_edge('generate_failure_response', '__end__')
    workflow.add_edge('generate_failure_response_from_analysis', '__end__')
    workflow.add_edge('generate_final_answer', '__end__')
    workflow.add_edge('generate_final_answer_from_analysis', '__end__')
    workflow.set_entry_point('initialize_agent_state')
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
        log_entry = {'timestamp': datetime.now(), 'event': 'graph_start',
            'node': 'start', 'state_summary': {'request_length': len(state.
            get('user_request', '')), 'has_schema': bool(state.get(
            'schema_dump')), 'has_sql': bool(state.get('sql_query')),
            'retry_count': state.get('retry_count', 0)}}
        self.execution_log.append(log_entry)
        logger.info(
            f"[GRAPH START] Processing request: {state['user_request']}")

    def on_graph_end(self, state: AgentState):
        total_time = time.time() - self.start_time if self.start_time else 0
        log_entry = {'timestamp': datetime.now(), 'event': 'graph_end',
            'node': 'end', 'total_execution_time': total_time,
            'state_summary': {'has_sql': bool(state.get('sql_query')),
            'result_count': len(state.get('db_results', [])),
            'final_response_length': len(state.get('final_response', '')),
            'retry_count': state.get('retry_count', 0), 'errors': {
            'validation': state.get('validation_error'), 'execution': state
            .get('execution_error'), 'generation': state.get(
            'sql_generation_error')}}}
        self.execution_log.append(log_entry)
        logger.info(
            f"[GRAPH END] Completed in {total_time:.2f}s, retries: {state.get('retry_count', 0)}"
            )


def run_enhanced_agent(user_request: str, mcp_servers: List[Dict[str, Any]]
    =None, disable_sql_blocking: bool=False, disable_databases: bool=False,
    registry_url: str=None) ->Dict[str, Any]:
    """
    Convenience function to run the enhanced agent with a user request
    """
    from config.settings import MCP_REGISTRY_URL
    effective_registry_url = registry_url or MCP_REGISTRY_URL
    graph = create_enhanced_agent_graph()
    initial_state: AgentState = {'user_request': user_request,
        'mcp_queries': [], 'mcp_results': [], 'synthesized_result': '',
        'can_answer': False, 'iteration_count': 0, 'max_iterations': 3,
        'final_answer': '', 'error_message': None, 'mcp_servers': 
        mcp_servers or [], 'refined_queries': [], 'failure_reason': None,
        'schema_dump': {}, 'sql_query': '', 'db_results': [],
        'all_db_results': {}, 'table_to_db_mapping': {},
        'table_to_real_db_mapping': {}, 'response_prompt': '', 'messages':
        [], 'validation_error': None, 'retry_count': 0, 'execution_error':
        None, 'sql_generation_error': None, 'disable_sql_blocking':
        disable_sql_blocking, 'disable_databases': disable_databases,
        'query_type': 'initial', 'database_name': '',
        'previous_sql_queries': [], 'registry_url': effective_registry_url,
        'discovered_services': [], 'mcp_service_results': [],
        'use_mcp_results': False, 'mcp_tool_calls': [],
        'mcp_capable_response': '', 'return_mcp_results_to_llm': False,
        'is_final_answer': False, 'rag_documents': [], 'rag_context': '',
        'use_rag_flag': False, 'rag_relevance_score': 0.0, 'rag_query': '',
        'rag_response': ''}
    callback_handler = AgentMonitoringCallback()
    callback_handler.on_graph_start(initial_state)
    try:
        result = graph.invoke(initial_state, config={'configurable': {
            'thread_id': 'default'}, 'recursion_limit': 50})
    except Exception as e:
        error_msg = str(e)
        if 'Recursion limit' in error_msg:
            logger.error(
                f'Recursion limit reached: {error_msg}. Returning error response to prevent infinite loop.'
                )
            result = {'user_request': user_request, 'mcp_queries': [],
                'mcp_results': [], 'synthesized_result': '', 'can_answer': 
                False, 'iteration_count': 0, 'max_iterations': 3,
                'final_answer':
                'Error: The system encountered an issue while processing your request. This may be due to a complex query that caused a recursion limit. Please try simplifying your request.'
                , 'error_message':
                'Recursion limit reached during processing', 'mcp_servers':
                mcp_servers or [], 'refined_queries': [], 'failure_reason':
                'Recursion limit reached during processing', 'schema_dump':
                {}, 'sql_query': '', 'db_results': [], 'all_db_results': {},
                'table_to_db_mapping': {}, 'table_to_real_db_mapping': {},
                'response_prompt': '', 'messages': [], 'validation_error':
                'Recursion limit reached during processing', 'retry_count':
                0, 'execution_error':
                'Recursion limit reached during processing',
                'sql_generation_error':
                'Recursion limit reached during processing',
                'disable_sql_blocking': False, 'disable_databases': False,
                'query_type': 'initial', 'database_name': '',
                'previous_sql_queries': [], 'registry_url':
                effective_registry_url, 'discovered_services': [],
                'mcp_service_results': [], 'use_mcp_results': False,
                'mcp_tool_calls': [], 'mcp_capable_response': '',
                'return_mcp_results_to_llm': False, 'rag_documents': [],
                'rag_context': '', 'use_rag_flag': False,
                'rag_relevance_score': 0.0, 'rag_query': '', 'rag_response': ''
                }
        else:
            raise e
    callback_handler.on_graph_end(result)
    return {'original_request': user_request, 'final_answer': result.get(
        'final_answer'), 'synthesized_result': result.get(
        'synthesized_result'), 'mcp_results': result.get('mcp_results'),
        'can_answer': result.get('can_answer'), 'iteration_count': result.
        get('iteration_count'), 'error_message': result.get('error_message'
        ), 'failure_reason': result.get('failure_reason'), 'execution_log':
        [entry for entry in callback_handler.execution_log],
        'generated_sql': result.get('sql_query'), 'db_results': result.get(
        'db_results'), 'all_db_results': result.get('all_db_results'),
        'table_to_db_mapping': result.get('table_to_db_mapping'),
        'table_to_real_db_mapping': result.get('table_to_real_db_mapping'),
        'response_prompt': result.get('response_prompt'),
        'validation_error': result.get('validation_error'),
        'execution_error': result.get('execution_error'),
        'sql_generation_error': result.get('sql_generation_error'),
        'retry_count': result.get('retry_count'), 'query_type': result.get(
        'query_type'), 'previous_sql_queries': result.get(
        'previous_sql_queries'), 'disable_databases': result.get(
        'disable_databases'), 'return_mcp_results_to_llm': result.get(
        'return_mcp_results_to_llm')}


def synthesize_results_node(state: AgentState) ->AgentState:
    """
    Node to synthesize results from multiple MCP queries
    """
    start_time = time.time()
    logger.info(
        f"[NODE START] synthesize_results_node - Synthesizing {len(state['mcp_results'])} results"
        )
    try:
        from models.response_generator import ResponseGenerator
        response_generator = ResponseGenerator()
        if not state['mcp_results']:
            logger.info(
                '[NODE INFO] synthesize_results_node - No results to synthesize'
                )
            elapsed_time = time.time() - start_time
            logger.info(
                f'[NODE SUCCESS] synthesize_results_node - Synthesized results in {elapsed_time:.2f}s'
                )
            return {**state, 'synthesized_result':
                'No results were obtained from the MCP services.'}
        formatted_results = []
        for idx, result in enumerate(state['mcp_results']):
            formatted_result = f'Result {idx + 1}: '
            if result.get('status') == 'success':
                formatted_result += (
                    f"Success - {result.get('data', str(result))}")
            else:
                formatted_result += (
                    f"Error - {result.get('error', str(result))}")
            formatted_results.append(formatted_result)
        combined_results = '\n'.join(formatted_results)
        synthesis_prompt = f"""
        Original request: {state['user_request']}

        Results from MCP services:
        {combined_results}

        Please synthesize these results into a coherent response that addresses the original request.
        If the results are conflicting, please note the discrepancies.
        If the results are incomplete, please note what information is missing.
        """
        synthesized_result = (response_generator.
            generate_natural_language_response(synthesis_prompt))
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] synthesize_results_node - Synthesized results into response'
            )
        return {**state, 'synthesized_result': synthesized_result}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error synthesizing results: {str(e)}'
        logger.error(
            f'[NODE ERROR] synthesize_results_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'synthesized_result': '', 'error_message': error_msg}


def can_answer_node(state: AgentState) ->AgentState:
    """
    Node to determine if we can answer the user's request based on synthesized results
    """
    start_time = time.time()
    logger.info(
        f'[NODE START] can_answer_node - Evaluating if we can answer the request'
        )
    try:
        from models.dedicated_mcp_model import DedicatedMCPModel
        mcp_model = DedicatedMCPModel()
        can_answer = mcp_model.evaluate_if_can_answer(state['user_request'],
            state['synthesized_result'])
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] can_answer_node - Can answer: {can_answer} in {elapsed_time:.2f}s'
            )
        return {**state, 'can_answer': can_answer}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error evaluating if can answer: {str(e)}'
        logger.error(
            f'[NODE ERROR] can_answer_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'can_answer': False, 'error_message': error_msg}


def generate_final_answer_node(state: AgentState) ->AgentState:
    """
    Node to generate the final answer based on synthesized results
    """
    start_time = time.time()
    logger.info(
        f'[NODE START] generate_final_answer_node - Generating final answer')
    try:
        from models.response_generator import ResponseGenerator
        response_generator = ResponseGenerator()
        final_answer = response_generator.generate_natural_language_response(
            state['synthesized_result'])
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] generate_final_answer_node - Generated final answer'
            )
        return {**state, 'final_answer': final_answer}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error generating final answer: {str(e)}'
        logger.error(
            f'[NODE ERROR] generate_final_answer_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'final_answer':
            f'I encountered an error while generating a response: {str(e)}',
            'error_message': error_msg}


def generate_final_answer_from_analysis_node(state: AgentState) ->AgentState:
    """
    Node to generate final answer when LLM indicates is_final_answer=True but no MCP tool calls were generated.
    Uses all available information including previous responses and MCP results.
    """
    start_time = time.time()
    logger.info(
        f'[NODE START] generate_final_answer_from_analysis_node - Generating final answer from analysis with no MCP calls'
        )
    try:
        from models.response_generator import ResponseGenerator
        response_generator = ResponseGenerator()
        comprehensive_prompt = f"""
        Original user request: {state['user_request']}

        Information gathered during processing:
        - Previous MCP results: {state.get('mcp_results', [])}
        - Previous synthesized results: {state.get('synthesized_result', 'None')}
        - Previous tool calls: {state.get('mcp_tool_calls', [])}

        The LLM previously analyzed this request and indicated that no MCP services were needed
        and that this is a final answer. Please generate a comprehensive response based on all
        available information to address the original request.
        """
        final_answer = response_generator.generate_natural_language_response(
            comprehensive_prompt)
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] generate_final_answer_from_analysis_node - Generated final answer in {elapsed_time:.2f}s'
            )
        return {**state, 'final_answer': final_answer, 'can_answer': True}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f'Error generating final answer from analysis: {str(e)}'
        logger.error(
            f'[NODE ERROR] generate_final_answer_from_analysis_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'final_answer':
            f'I encountered an error while generating a response: {str(e)}',
            'error_message': error_msg}


def generate_failure_response_from_analysis_node(state: AgentState
    ) ->AgentState:
    """
    Node to generate failure response when LLM indicates is_final_answer=False and no MCP tool calls were generated.
    This means the LLM determined it cannot answer the question and no further MCP services are needed.
    """
    start_time = time.time()
    logger.info(
        f'[NODE START] generate_failure_response_from_analysis_node - Generating failure response from analysis with no MCP calls and is_final_answer=False'
        )
    try:
        from models.response_generator import ResponseGenerator
        response_generator = ResponseGenerator()
        failure_prompt = f"""
        Original user request: {state['user_request']}

        Information gathered during processing:
        - Previous MCP results: {state.get('mcp_results', [])}
        - Previous synthesized results: {state.get('synthesized_result', 'None')}
        - Previous tool calls: {state.get('mcp_tool_calls', [])}

        Despite analysis, no MCP services were identified that could help answer this request,
        and the LLM indicated that this is not a final answer. This suggests that the request
        cannot be adequately addressed with the available MCP services.

        Please provide a response acknowledging the limitation and suggesting possible alternatives
        or ways the user might rephrase their request.
        """
        final_answer = response_generator.generate_natural_language_response(
            failure_prompt)
        failure_reason = (
            'Unable to identify appropriate MCP services to answer the request, and LLM indicated this is not a final answer.'
            )
        elapsed_time = time.time() - start_time
        logger.info(
            f'[NODE SUCCESS] generate_failure_response_from_analysis_node - Generated failure response in {elapsed_time:.2f}s'
            )
        return {**state, 'final_answer': final_answer, 'failure_reason':
            failure_reason, 'can_answer': False}
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = (
            f'Error generating failure response from analysis: {str(e)}')
        logger.error(
            f'[NODE ERROR] generate_failure_response_from_analysis_node - {error_msg} after {elapsed_time:.2f}s'
            )
        return {**state, 'final_answer':
            'I was unable to find appropriate MCP services to answer your request.'
            , 'failure_reason':
            'Unable to identify appropriate MCP services to answer the request.'
            , 'error_message': error_msg}

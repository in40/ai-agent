"""
LangGraph implementation of the AI Agent with enhanced state management,
conditional logic, and error recovery capabilities.
"""

from typing import TypedDict, List, Dict, Any, Literal
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from utils.multi_database_manager import multi_db_manager as DatabaseManager, reload_database_config
from models.sql_generator import SQLGenerator
from models.sql_executor import SQLExecutor
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
    State definition for the LangGraph agent.
    """
    user_request: str
    schema_dump: Dict[str, Any]
    sql_query: str
    db_results: List[Dict[str, Any]]  # Results from all databases
    all_db_results: Dict[str, List[Dict[str, Any]]]  # Results grouped by database name
    table_to_db_mapping: Dict[str, str]  # Mapping from original table names to database names
    table_to_real_db_mapping: Dict[str, str]  # Mapping from original table names to real database names
    response_prompt: str  # Specialized prompt for response generation
    final_response: str
    messages: List[BaseMessage]
    validation_error: str
    retry_count: int
    execution_error: str
    sql_generation_error: str
    disable_sql_blocking: bool
    query_type: str  # Track whether this is an 'initial' query or 'wider_search' query
    database_name: str  # Name of the database to use for queries
    previous_sql_queries: List[str]  # History of previously generated SQL queries


def get_schema_node(state: AgentState) -> AgentState:
    """
    Node to retrieve database schema from all available databases
    """
    start_time = time.time()
    logger.info(f"[NODE START] get_schema_node - Processing request: {state['user_request']}")

    try:
        # Get all available database names
        all_databases = DatabaseManager.list_databases()

        # Collect schema dumps from all databases
        combined_schema_dump = {}
        table_to_db_mapping = {}  # Map original table names to database names
        table_to_real_db_mapping = {}  # Map original table names to real database names

        for db_name in all_databases:
            try:
                schema_dump = DatabaseManager.get_schema_dump(db_name, use_real_name=True)

                # Add all tables from this database to the combined schema
                for table_name, table_info in schema_dump.items():
                    # Store the original table name
                    combined_schema_dump[table_name] = table_info

                    # Store mapping from original table name to database
                    table_to_db_mapping[table_name] = db_name

                    # Store mapping from original table name to real database name
                    from config.database_aliases import get_db_alias_mapper
                    db_alias_mapper = get_db_alias_mapper()
                    real_name = db_alias_mapper.get_real_name(db_name)
                    if real_name:
                        table_to_real_db_mapping[table_name] = real_name
                    else:
                        table_to_real_db_mapping[table_name] = db_name  # Use alias if no real name mapping

                logger.info(f"[NODE INFO] get_schema_node - Retrieved schema with {len(schema_dump)} tables from '{db_name}' database")
            except Exception as e:
                logger.warning(f"[NODE WARNING] get_schema_node - Error retrieving schema from '{db_name}' database: {str(e)}")
                # Continue with other databases even if one fails

        elapsed_time = time.time() - start_time

        logger.info(f"[NODE SUCCESS] get_schema_node - Retrieved combined schema with {len(combined_schema_dump)} tables from {len(all_databases)} databases in {elapsed_time:.2f}s")
        return {
            **state,
            "schema_dump": combined_schema_dump,
            "table_to_db_mapping": table_to_db_mapping,  # Store the mapping for later use
            "table_to_real_db_mapping": table_to_real_db_mapping,  # Store the real database mapping for LLM use
            "sql_generation_error": None,  # Clear any previous errors
            "query_type": "initial",  # Set the query type to initial
            "database_name": "all_databases",  # Indicate that all databases are being used
            "previous_sql_queries": []  # Initialize with empty list of previous SQL queries
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] get_schema_node - Error retrieving schema from all databases after {elapsed_time:.2f}s: {str(e)}")
        return {
            **state,
            "schema_dump": {},
            "sql_generation_error": f"Error retrieving schema from all databases: {str(e)}",
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }


def generate_sql_node(state: AgentState) -> AgentState:
    """
    Node to generate SQL query
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_sql_node - Generating SQL for request: {state['user_request']}")

    try:
        sql_generator = SQLGenerator()

        # Check if there are previous errors to include in the request
        previous_errors = []
        if state.get("validation_error"):
            previous_errors.append(f"Validation error: {state['validation_error']}")
        if state.get("execution_error"):
            previous_errors.append(f"Execution error: {state['execution_error']}")
        if state.get("sql_generation_error"):
            previous_errors.append(f"Previous generation error: {state['sql_generation_error']}")

        # Include previous errors in the request if they exist
        user_request = state["user_request"]
        if previous_errors:
            error_context = "Previous errors encountered: " + "; ".join(previous_errors)
            user_request_with_errors = f"{user_request}\n\n{error_context}\n\nPlease generate a corrected SQL query that addresses these errors while still fulfilling the original request."
        else:
            user_request_with_errors = user_request

        # Get previous SQL queries from state, default to empty list if not present
        previous_sql_queries = state.get("previous_sql_queries", [])

        sql_query = sql_generator.generate_sql(
            user_request_with_errors,
            state["schema_dump"],
            previous_sql_queries=previous_sql_queries,
            table_to_db_mapping=state.get("table_to_db_mapping"),  # Pass the table-to-database mapping
            table_to_real_db_mapping=state.get("table_to_real_db_mapping")  # Pass the table-to-real-database mapping
        )
        elapsed_time = time.time() - start_time

        # Update the list of previous SQL queries
        previous_queries = state.get("previous_sql_queries", [])
        updated_previous_queries = previous_queries + [sql_query] if sql_query else previous_queries

        logger.info(f"[NODE SUCCESS] generate_sql_node - Generated SQL in {elapsed_time:.2f}s: {sql_query}")
        return {
            **state,
            "sql_query": sql_query,
            "sql_generation_error": None,  # Clear any previous errors
            "query_type": "initial",  # Set the query type to initial
            "previous_sql_queries": updated_previous_queries  # Update the history of SQL queries
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] generate_sql_node - Error generating SQL after {elapsed_time:.2f}s: {str(e)}")
        return {
            **state,
            "sql_query": "",
            "sql_generation_error": f"Error generating SQL: {str(e)}",
            "retry_count": state.get("retry_count", 0) + 1,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
                }
            else:
                # If security LLM says it's safe, skip basic validation
                elapsed_time = time.time() - start_time
                logger.info(f"[NODE SUCCESS] validate_sql_node - Security LLM validation passed in {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": None,
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
                }
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
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
                }
        elif command in sql_lower:
            error_msg = f"Potentially harmful SQL detected: {command}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
        "dbms_.*\\.",  # Oracle DBMS packages
        "utl_.*\\.",  # Oracle UTL packages
        "ctxsys\\.driddl",  # Oracle text index manipulation
        "sys.dbms",  # Oracle system package
        "sys.any",  # Oracle system types
        "any_data",  # Oracle system type
        "any_type",  # Oracle system type
        "anydataset",  # Oracle system type
        "sys.xmlgen",  # Oracle XML generation
        "sdo_util\\.to_clob",  # Oracle spatial utility
        "sdo_sql\\.shapefilereader",  # Oracle spatial utility
        "dbms_java\\.grant_permission",  # Oracle Java permissions
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
        "dbms_xmlgen",  # Oracle XML generation
        "dbms_xmlstore",  # Oracle XML storage
        "dbms_xmlschema",  # Oracle XML schema
        "dbms_xmlquery",  # Oracle XML querying
        "dbms_xmlsave",  # Oracle XML saving
        "dbms_xmlparser",  # Oracle XML parsing
        "dbms_xmlgen\\.getxml",  # Oracle XML generation
        "dbms_xmlgen\\.getclobval",  # Oracle XML generation
        "dbms_xmlgen\\.getstringval",  # Oracle XML generation
        "dbms_xmlgen\\.getnumberval",  # Oracle XML generation
        "dbms_xmlgen\\.getdateval",  # Oracle XML generation
        "dbms_xmlgen\\.getrowset",  # Oracle XML generation
        "dbms_xmlgen\\.getxmltype",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlval",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlstring",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldoc",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlfragment",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlattribute",  # Oracle XML generation
        "dbms_xmlgen\\.getxmltext",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcomment",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlpi",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcdata",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlnamespace",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlroot",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlprolog",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldeclaration",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlstylesheet",  # Oracle XML generation
        "dbms_xmlgen\\.getxmltransform",  # Oracle XML generation
        "dbms_xmlgen\\.getxmloutput",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlinput",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlencoding",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlversion",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlstandalone",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlindent",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlformat",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcompression",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldatatype",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlschema",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlvalidation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlnormalization",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcanonicalization",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlserialization",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlparsing",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlprocessing",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlrendering",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlpresentation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmltransformation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmltranslation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconversion",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmanipulation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcreation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmodification",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldeletion",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlinsertion",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlupdate",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlretrieval",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlsearch",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlfilter",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlsort",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlaggregation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlgrouping",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlpartitioning",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlindexing",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcaching",  # Oracle XML generation
        "dbms_xmlgen\\.getxmloptimization",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlprofiling",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmonitoring",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldebugging",  # Oracle XML generation
        "dbms_xmlgen\\.getxmllogging",  # Oracle XML generation
        "dbms_xmlgen\\.getxmltracing",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlauditing",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlsecurity",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlencryption",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldecryption",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlauthentication",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlauthorization",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlprivilege",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlpermission",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlaccess",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcontrol",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmanagement",  # Oracle XML generation
        "dbms_xmlgen\\.getxmladministration",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconfiguration",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlinstallation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldeployment",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmaintenance",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlupgrade",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlrollback",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlrecovery",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlbackup",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlrestore",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlreplication",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmigration",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlintegration",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlinteroperability",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcompatibility",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlportability",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlscalability",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlperformance",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlefficiency",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlreliability",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlavailability",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmaintainability",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlusability",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlfunctionality",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlquality",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlstandards",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcompliance",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcertification",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlvalidation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlverification",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlauthentication",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlauthorization",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlaccounting",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlbilling",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcharging",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlrating",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlpricing",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcosting",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlbudgeting",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlforecasting",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlplanning",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlscheduling",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlresource",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlallocation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmldistribution",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlassignment",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcoordination",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcollaboration",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlcommunication",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlnegotiation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlmediation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation",  # Oracle XML generation
        "dbms_xmlgen\\.getxmlconciliation"  # Oracle XML generation
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
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
            "retry_count": state.get("retry_count", 0) + 1,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }

    # Additional check: Ensure query doesn't contain binary literals that might be used for injection
    if re.search(r"b'[01]+'", sql_lower):
        error_msg = "Binary literals detected. These are not allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
                "retry_count": state.get("retry_count", 0) + 1,
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
            }

    # If all validations pass
    elapsed_time = time.time() - start_time
    logger.info(f"[NODE SUCCESS] validate_sql_node - SQL validation passed in {elapsed_time:.2f}s")
    return {
        **state,
        "validation_error": None,
        "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
    }


def execute_sql_node(state: AgentState) -> AgentState:
    """
    Node to execute SQL query on appropriate databases based on table-to-database mapping
    """
    start_time = time.time()
    logger.info(f"[NODE START] execute_sql_node - Executing SQL: {state['sql_query']}")

    try:
        # Get all available database names
        all_databases = DatabaseManager.list_databases()

        # Extract table names from the SQL query to determine which databases to use
        sql_executor = SQLExecutor()
        table_names = sql_executor._extract_table_names(state["sql_query"])

        # Determine which databases to query based on table-to-database mapping
        table_to_db_mapping = state.get("table_to_db_mapping", {})
        databases_to_query = set()

        # If we have table-to-database mapping, use it to determine which databases to query
        if table_to_db_mapping:
            for table_name in table_names:
                # Remove quotes from table name if present
                clean_table_name = table_name.strip('"\'')

                if clean_table_name in table_to_db_mapping:
                    databases_to_query.add(table_to_db_mapping[clean_table_name])
                else:
                    # If table is not in mapping, we need to check which databases actually have this table
                    # by looking at the schema of each database
                    found_in_databases = []
                    for db_name in all_databases:
                        try:
                            schema = DatabaseManager.get_schema_dump(db_name)
                            # Check if the table exists in this database (case-insensitive)
                            table_exists = any(t.lower() == clean_table_name.lower() for t in schema.keys())
                            if table_exists:
                                found_in_databases.append(db_name)
                        except Exception as e:
                            logger.warning(f"Could not check schema for database '{db_name}': {str(e)}")

                    if found_in_databases:
                        databases_to_query.update(found_in_databases)
                    else:
                        # If table is not found in any database, log a warning and continue with all databases
                        # This is a fallback, but ideally the table should exist somewhere
                        logger.warning(f"Table '{clean_table_name}' not found in any database schema. Querying all databases.")
                        databases_to_query = set(all_databases)

            # Check if we have tables from multiple databases - if so, we should query all databases
            if len(databases_to_query) > 1:
                logger.info(f"[NODE INFO] execute_sql_node - Cross-database query detected. Querying all databases: {list(all_databases)}")
                databases_to_query = set(all_databases)
        else:
            # If no mapping is available, query all databases
            databases_to_query = set(all_databases)

        logger.info(f"[NODE INFO] execute_sql_node - Querying databases: {list(databases_to_query)} for tables: {table_names}")

        # Execute the query on selected databases and collect results
        all_db_results = {}
        combined_results = []

        # Track execution errors to provide better feedback to the LLM
        execution_errors = []

        # If we're dealing with a cross-database query, execute on all databases using the special method
        if len(databases_to_query) > 1:
            logger.info(f"[NODE INFO] execute_sql_node - Executing cross-database query on all databases")
            try:
                # Use the special method to execute on appropriate databases
                results = sql_executor.execute_sql_and_get_results(state["sql_query"], "all_databases", table_to_db_mapping)

                # Since the results are already combined from multiple databases,
                # we just need to add them to the combined_results
                combined_results = results

                logger.info(f"[NODE INFO] execute_sql_node - Cross-database query executed, got {len(combined_results)} results")
            except Exception as e:
                error_msg = f"Cross-database query execution error: {str(e)}"
                execution_errors.append(error_msg)
                logger.error(f"[NODE ERROR] execute_sql_node - {error_msg}")
        else:
            # Execute on individual databases as before
            for db_name in databases_to_query:
                try:
                    results = sql_executor.execute_sql_and_get_results(state["sql_query"], db_name, table_to_db_mapping)

                    # Store results by database name
                    all_db_results[db_name] = results

                    # Add database identifier to each result row to distinguish sources
                    for result in results:
                        result["_source_database"] = db_name

                    # Combine results from all databases
                    combined_results.extend(results)

                    logger.info(f"[NODE INFO] execute_sql_node - Query executed on '{db_name}' database, got {len(results)} results")
                except Exception as e:
                    error_msg = f"SQL execution error on '{db_name}' database: {str(e)}"

                    # Add the error to the list of execution errors
                    execution_errors.append(error_msg)

                    # Check if the error is related to table existence or column existence
                    error_str = str(e).lower()
                    if "do not exist in the database" in error_str:
                        logger.warning(f"[NODE WARNING] execute_sql_node - {error_msg}")
                    elif "column" in error_str and "does not exist" in error_str:
                        logger.warning(f"[NODE WARNING] execute_sql_node - {error_msg}")
                        # Add more specific information about the column error
                        execution_errors.append(f"The query references a column that doesn't exist in the '{db_name}' database. Check the schema for this database to ensure all referenced columns exist.")
                    else:
                        logger.error(f"[NODE ERROR] execute_sql_node - {error_msg}")

                    # Continue with other databases even if one fails
                    all_db_results[db_name] = []  # Store empty results for failed database

        elapsed_time = time.time() - start_time

        # If there were execution errors, store them in the state
        if execution_errors:
            error_summary = "; ".join(execution_errors)
            logger.info(f"[NODE INFO] execute_sql_node - Summary of execution errors: {error_summary}")
            return {
                **state,
                "db_results": combined_results,
                "all_db_results": all_db_results,
                "execution_error": error_summary,  # Store execution errors for refinement
                "query_type": state.get("query_type", "initial"),  # Preserve the query type
                "database_name": ", ".join(databases_to_query),  # Indicate which databases were used
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
            }
        else:
            logger.info(f"[NODE SUCCESS] execute_sql_node - Query executed on {len(databases_to_query)} databases in {elapsed_time:.2f}s, got {len(combined_results)} total results")
            return {
                **state,
                "db_results": combined_results,
                "all_db_results": all_db_results,
                "execution_error": None,  # Clear any previous errors
                "query_type": state.get("query_type", "initial"),  # Preserve the query type
                "database_name": ", ".join(databases_to_query),  # Indicate which databases were used
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
            }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"SQL execution error across all databases: {str(e)}"
        logger.error(f"[NODE ERROR] execute_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "db_results": [],
            "all_db_results": {},
            "execution_error": error_msg,
            "validation_error": error_msg,  # Also set validation error to trigger retry
            "query_type": state.get("query_type", "initial"),  # Preserve the query type
            "database_name": state.get("database_name", "all_databases"),  # Preserve database name in state
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }


def refine_sql_node(state: AgentState) -> AgentState:
    """
    Node to refine SQL query based on execution results or errors
    """
    start_time = time.time()
    logger.info(f"[NODE START] refine_sql_node - Refining SQL for request: {state['user_request']}")

    try:
        # Get all errors that led to refinement
        all_errors = []
        if state.get("execution_error"):
            all_errors.append(f"Execution error: {state['execution_error']}")
        if state.get("validation_error"):
            all_errors.append(f"Validation error: {state['validation_error']}")
        if state.get("sql_generation_error"):
            all_errors.append(f"SQL generation error: {state['sql_generation_error']}")

        error_context = "; ".join(all_errors) if all_errors else "Unknown error occurred"

        # Get the original request and schema
        user_request = state["user_request"]
        schema_dump = state["schema_dump"]
        current_sql = state["sql_query"]
        current_query_type = state.get("query_type", "initial")  # Preserve the current query type

        # Get previous SQL queries from state to pass to the SQL generator
        previous_sql_queries = state.get("previous_sql_queries", [])

        # Prevent infinite loops by checking if we're retrying with an empty query
        if not current_sql or current_sql.strip() == "":
            # If the current SQL is empty, try to generate a new one from scratch
            sql_generator = SQLGenerator()
            refined_sql = sql_generator.generate_sql(
                user_request,
                schema_dump,
                previous_sql_queries=previous_sql_queries,
                table_to_db_mapping=state.get("table_to_db_mapping"),  # Pass the table-to-database mapping
                table_to_real_db_mapping=state.get("table_to_real_db_mapping")  # Pass the table-to-real-database mapping
            )
        else:
            # Create a prompt to refine the SQL query based on all errors
            refinement_prompt = f"""
            Original user request: {user_request}

            Current SQL query: {current_sql}

            Errors encountered: {error_context}

            Schema information:
            {format_schema_dump(schema_dump)}

            Please generate a corrected SQL query that addresses all the errors while still fulfilling the original request.
            Pay special attention to column names - make sure they exist in the tables as shown in the schema.
            Make sure the query follows all safety guidelines (only SELECT statements, no harmful commands, etc.).
            """

            # Use the SQL generator to create a refined query
            sql_generator = SQLGenerator()
            refined_sql = sql_generator.generate_sql(
                refinement_prompt,
                schema_dump,
                previous_sql_queries=previous_sql_queries,
                table_to_db_mapping=state.get("table_to_db_mapping"),  # Pass the table-to-database mapping
                table_to_real_db_mapping=state.get("table_to_real_db_mapping")  # Pass the table-to-real-database mapping
            )

        elapsed_time = time.time() - start_time

        # Update the list of previous SQL queries with the newly refined query
        previous_queries = state.get("previous_sql_queries", [])
        updated_previous_queries = previous_queries + [refined_sql] if refined_sql else previous_queries

        logger.info(f"[NODE SUCCESS] refine_sql_node - Refined SQL in {elapsed_time:.2f}s: {refined_sql[:100]}...")

        return {
            **state,
            "sql_query": refined_sql,
            "validation_error": None,  # Reset validation error
            "execution_error": None,   # Reset execution error
            "sql_generation_error": None,  # Reset generation error
            "query_type": current_query_type,  # Preserve the query type
            "previous_sql_queries": updated_previous_queries  # Update the history of SQL queries
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error refining SQL query: {str(e)}"
        logger.error(f"[NODE ERROR] refine_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "sql_generation_error": error_msg,
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }


def format_schema_dump(schema_dump):
    """
    Helper function to format the schema dump for the LLM
    """
    formatted = ""
    for table_name, table_info in schema_dump.items():
        # Handle both the old format (list of columns) and new format (dict with columns and comment)
        if isinstance(table_info, list):
            # Old format - backward compatibility
            columns = table_info
            table_comment = None
        else:
            # New format with comments
            columns = table_info.get('columns', [])
            table_comment = table_info.get('comment', None)

        formatted += f"\nTable: {table_name}"
        if table_comment:
            formatted += f" - Comment: {table_comment}"
        formatted += "\n"

        for col in columns:
            if isinstance(col, dict):
                # New format with comments
                col_info = f"  - {col['name']} ({col['type']}) - Nullable: {col['nullable']}"
                if col.get('comment'):
                    col_info += f" - Comment: {col['comment']}"
                formatted += col_info + "\n"
            else:
                # Old format - backward compatibility
                formatted += f"  - {col['name']} ({col['type']}) - Nullable: {col['nullable']}\n"
    return formatted


def security_check_after_refinement_node(state: AgentState) -> AgentState:
    """
    Node to perform security check on refined SQL query
    """
    start_time = time.time()
    sql = state["sql_query"]
    disable_blocking = state.get("disable_sql_blocking", False)
    schema_dump = state.get("schema_dump", {})
    current_query_type = state.get("query_type", "initial")  # Preserve the current query type

    logger.info(f"[NODE START] security_check_after_refinement_node - Security checking refined SQL: {sql} (blocking {'disabled' if disable_blocking else 'enabled'})")

    # If SQL blocking is disabled, skip security check and return success
    if disable_blocking:
        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] security_check_after_refinement_node - Security check skipped (blocking disabled) in {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": None,
            "query_type": current_query_type,  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }

    # Use the security LLM for advanced analysis if enabled
    use_security_llm = str_to_bool(os.getenv("USE_SECURITY_LLM", "true"))
    if use_security_llm:
        logger.info("[NODE INFO] security_check_after_refinement_node - Using security LLM for advanced analysis")
        try:
            security_detector = SecuritySQLDetector()
            is_safe, reason = security_detector.is_query_safe(sql, schema_dump)

            if not is_safe:
                error_msg = f"Security LLM detected potential security issue after refinement: {reason}"
                elapsed_time = time.time() - start_time
                logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": error_msg,
                    "retry_count": state.get("retry_count", 0) + 1,
                    "query_type": current_query_type,  # Preserve the query type
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
                }
            else:
                # If security LLM says it's safe, we can proceed
                elapsed_time = time.time() - start_time
                logger.info(f"[NODE SUCCESS] security_check_after_refinement_node - Security check passed in {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": None,
                    "query_type": current_query_type,  # Preserve the query type
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
                }
        except Exception as e:
            logger.warning(f"[NODE WARNING] security_check_after_refinement_node - Security LLM failed: {str(e)}, falling back to basic validation")
            # If security LLM fails, fall back to basic validation
            pass

    # Fallback to basic keyword matching if security LLM is disabled or failed
    logger.info("[NODE INFO] security_check_after_refinement_node - Using basic keyword matching for analysis")

    # Check for potentially harmful SQL commands
    sql_lower = sql.lower()
    harmful_commands = ["drop", "delete", "insert", "update", "truncate", "alter", "exec", "execute"]

    for command in harmful_commands:
        # Skip 'create' if it's part of a column name like 'created_at'
        if command == "create":
            # Check if 'create' appears as a standalone command (not part of a column name)
            # Look for 'create' followed by a space or semicolon (indicating a command)
            import re
            if re.search(r'\bcreate\s+(table|database|index|view|procedure|function|trigger)\b', sql_lower):
                error_msg = f"Potentially harmful SQL detected after refinement: {command}"
                elapsed_time = time.time() - start_time
                logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": error_msg,
                    "retry_count": state.get("retry_count", 0) + 1,
                    "query_type": current_query_type,  # Preserve the query type
                    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
                }
        elif command in sql_lower:
            error_msg = f"Potentially harmful SQL detected after refinement: {command}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
                "query_type": current_query_type,  # Preserve the query type
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
            }

    # Additional validation: Check if query starts with SELECT
    if not sql_lower.strip().startswith('select'):
        error_msg = "Refined SQL query does not start with SELECT, which is required for safety"
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1,
            "query_type": current_query_type,  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
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
    ]

    for pattern in dangerous_patterns:
        if pattern in sql_lower:
            error_msg = f"Potentially dangerous SQL pattern detected after refinement: {pattern}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
                "query_type": current_query_type,  # Preserve the query type
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
            }

    # Check for multiple statements (semicolon-separated)
    if sql.count(';') > 1:
        error_msg = "Multiple SQL statements detected after refinement. Only single statements are allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1,
            "query_type": current_query_type,  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }

    # Check for comment sequences that might be used to bypass filters
    if "/*" in sql or "--" in sql or "#" in sql:
        error_msg = "SQL comments detected after refinement. These are not allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1,
            "query_type": current_query_type,  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }

    # If all validations pass
    elapsed_time = time.time() - start_time
    logger.info(f"[NODE SUCCESS] security_check_after_refinement_node - Security check passed in {elapsed_time:.2f}s")
    return {
        **state,
        "validation_error": None,
        "query_type": current_query_type,  # Preserve the query type
        "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
    }


def generate_prompt_node(state: AgentState) -> AgentState:
    """
    Node to generate specialized prompt for the response LLM
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_prompt_node - Generating specialized prompt for request: {state['user_request']}")

    try:
        prompt_generator = PromptGenerator()

        # Generate a specialized prompt for the response LLM based on user request and database results
        response_prompt = prompt_generator.generate_prompt_for_response_llm(
            state["user_request"],
            state["db_results"]
        )

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] generate_prompt_node - Generated specialized prompt in {elapsed_time:.2f}s")
        return {
            **state,
            "response_prompt": response_prompt,  # Store the generated prompt for the next step
            "query_type": state.get("query_type", "initial"),  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating specialized prompt: {str(e)}"
        logger.error(f"[NODE ERROR] generate_prompt_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "final_response": f"Error generating response: {str(e)}",
            "query_type": state.get("query_type", "initial"),  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }


def generate_wider_search_query_node(state: AgentState) -> AgentState:
    """
    Node to generate wider search query when initial query returns no results
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_wider_search_query_node - Generating wider search query for request: {state['user_request']}")

    try:
        # Use the prompt generator to create a wider search strategy
        prompt_generator = PromptGenerator()

        # Check if there are previous errors to include in the request
        previous_errors = []
        if state.get("validation_error"):
            previous_errors.append(f"Validation error: {state['validation_error']}")
        if state.get("execution_error"):
            previous_errors.append(f"Execution error: {state['execution_error']}")
        if state.get("sql_generation_error"):
            previous_errors.append(f"Previous generation error: {state['sql_generation_error']}")

        # Include previous errors in the wider search context if they exist
        error_context = ""
        if previous_errors:
            error_context = "\n\nPrevious errors encountered: " + "; ".join(previous_errors)

        # Create context for wider search
        wider_search_context = f"""
        Original user request: {state['user_request']}

        Initial SQL query: {state['sql_query']}

        Database schema:
        {format_schema_dump(state['schema_dump'])}{error_context}

        Initial query returned no results. Please suggest alternative search strategies or queries that might yield relevant data based on the schema and the original user request.
        """

        # Get previous SQL queries from state to pass to the wider search generator
        previous_sql_queries = state.get("previous_sql_queries", [])

        # Generate wider search prompt using the specialized wider search generator
        wider_search_prompt = prompt_generator.generate_wider_search_prompt(
            wider_search_context,
            schema_dump=state['schema_dump'],
            db_mapping=state.get('table_to_db_mapping'),
            previous_sql_queries=previous_sql_queries
        )

        # Debug: Log the type and content of wider_search_prompt
        logger.debug(f"wider_search_prompt type: {type(wider_search_prompt)}, content: {repr(wider_search_prompt)}")

        # Use the SQL generator to create a new query based on the wider search suggestions
        sql_generator = SQLGenerator()

        # Prepare the combined prompt for SQL generation
        combined_prompt = wider_search_prompt + f"\n\nBased on these suggestions, generate a new SQL query for the request: {state['user_request']}"

        # Debug: Log the type and content of combined_prompt
        logger.debug(f"combined_prompt type: {type(combined_prompt)}, content: {repr(combined_prompt)}")

        new_sql_query = sql_generator.generate_sql(
            combined_prompt,
            state["schema_dump"],
            table_to_db_mapping=state.get("table_to_db_mapping"),  # Pass the table-to-database mapping
            table_to_real_db_mapping=state.get("table_to_real_db_mapping")  # Pass the table-to-real-database mapping
        )

        elapsed_time = time.time() - start_time

        # Update the list of previous SQL queries with the newly generated query
        previous_queries = state.get("previous_sql_queries", [])
        updated_previous_queries = previous_queries + [new_sql_query] if new_sql_query else previous_queries

        logger.info(f"[NODE SUCCESS] generate_wider_search_query_node - Generated wider search query in {elapsed_time:.2f}s: {new_sql_query}")
        return {
            **state,
            "sql_query": new_sql_query,  # Update the SQL query with the wider search query
            "query_type": "wider_search",  # Set the query type to wider_search
            "retry_count": state.get("retry_count", 0) + 1,  # Increment retry count to prevent infinite loops
            "previous_sql_queries": updated_previous_queries  # Update the history of SQL queries
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating wider search query: {str(e)}"
        logger.error(f"[NODE ERROR] generate_wider_search_query_node - {error_msg} after {elapsed_time:.2f}s")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Instead of returning an error response, return the original query to break the cycle
        # This prevents the infinite loop when wider search generation fails
        return {
            **state,
            "final_response": "I couldn't find any results for your query. The database doesn't contain the information requested.",
            "query_type": "wider_search",  # Mark as wider search to indicate we tried
            "retry_count": state.get("retry_count", 0) + 1,  # Increment retry count to prevent infinite loops
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }


def execute_wider_search_node(state: AgentState) -> AgentState:
    """
    Node to execute the wider search query on all available databases
    """
    start_time = time.time()
    logger.info(f"[NODE START] execute_wider_search_node - Executing wider search query: {state['sql_query']}")

    try:
        # Get all available database names
        all_databases = DatabaseManager.list_databases()

        # Extract table names from the SQL query to determine if it's a cross-database query
        sql_executor = SQLExecutor()
        table_names = sql_executor._extract_table_names(state["sql_query"])

        # Determine if this is a cross-database query
        table_to_db_mapping = state.get("table_to_db_mapping", {})
        databases_with_tables = set()

        if table_to_db_mapping:
            for table_name in table_names:
                clean_table_name = table_name.strip('"\'')

                if clean_table_name in table_to_db_mapping:
                    databases_with_tables.add(table_to_db_mapping[clean_table_name])
                else:
                    # If table is not in mapping, check which databases have it
                    for db_name in all_databases:
                        try:
                            schema = DatabaseManager.get_schema_dump(db_name)
                            if any(clean_table_name.lower() == schema_table_name.lower() for schema_table_name in schema.keys()):
                                databases_with_tables.add(db_name)
                                break
                        except Exception:
                            continue

        # Execute the query based on whether it's a cross-database query
        all_db_results = {}
        combined_results = []

        # Track execution errors to provide better feedback to the LLM
        execution_errors = []

        if len(databases_with_tables) > 1:
            # This is a cross-database query, execute using the special method
            logger.info(f"[NODE INFO] execute_wider_search_node - Cross-database wider search query detected")
            try:
                # Use the special method to execute on appropriate databases
                results = sql_executor.execute_sql_and_get_results(state["sql_query"], "all_databases", state.get("table_to_db_mapping"))

                # Since the results are already combined from multiple databases,
                # we just need to add them to the combined_results
                combined_results = results

                logger.info(f"[NODE INFO] execute_wider_search_node - Cross-database wider search query executed, got {len(combined_results)} results")
            except Exception as e:
                error_msg = f"Cross-database wider search execution error: {str(e)}"
                execution_errors.append(error_msg)
                logger.error(f"[NODE ERROR] execute_wider_search_node - {error_msg}")
        else:
            # Execute on individual databases as before
            for db_name in all_databases:
                try:
                    results = sql_executor.execute_sql_and_get_results(state["sql_query"], db_name, state.get("table_to_db_mapping"))

                    # Store results by database name
                    all_db_results[db_name] = results

                    # Add database identifier to each result row to distinguish sources
                    for result in results:
                        result["_source_database"] = db_name

                    # Combine results from all databases
                    combined_results.extend(results)

                    logger.info(f"[NODE INFO] execute_wider_search_node - Wider search query executed on '{db_name}' database, got {len(results)} results")
                except Exception as e:
                    error_msg = f"Wider search execution error on '{db_name}' database: {str(e)}"

                    # Add the error to the list of execution errors
                    execution_errors.append(error_msg)

                    # Check if the error is related to table existence or column existence
                    error_str = str(e).lower()
                    if "do not exist in the database" in error_str:
                        logger.warning(f"[NODE WARNING] execute_wider_search_node - {error_msg}")
                    elif "column" in error_str and "does not exist" in error_str:
                        logger.warning(f"[NODE WARNING] execute_wider_search_node - {error_msg}")
                        # Add more specific information about the column error
                        execution_errors.append(f"The query references a column that doesn't exist in the '{db_name}' database. Check the schema for this database to ensure all referenced columns exist.")
                    else:
                        logger.error(f"[NODE ERROR] execute_wider_search_node - {error_msg}")

                    # Continue with other databases even if one fails
                    all_db_results[db_name] = []  # Store empty results for failed database

        elapsed_time = time.time() - start_time

        # If there were execution errors, store them in the state
        if execution_errors:
            error_summary = "; ".join(execution_errors)
            logger.info(f"[NODE INFO] execute_wider_search_node - Summary of execution errors: {error_summary}")
            return {
                **state,
                "db_results": combined_results,
                "all_db_results": all_db_results,
                "execution_error": error_summary,  # Store execution errors for refinement
                "query_type": "wider_search",  # Set the query type to wider_search
                "database_name": "all_databases",  # Indicate that all databases were used
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
            }
        else:
            logger.info(f"[NODE SUCCESS] execute_wider_search_node - Wider search query executed on {len(all_databases)} databases in {elapsed_time:.2f}s, got {len(combined_results)} total results")
            return {
                **state,
                "db_results": combined_results,
                "all_db_results": all_db_results,
                "execution_error": None,  # Clear any previous errors
                "query_type": "wider_search",  # Set the query type to wider_search
                "database_name": "all_databases",  # Indicate that all databases were used
                "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
            }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Wider search execution error across all databases: {str(e)}"
        logger.error(f"[NODE ERROR] execute_wider_search_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "db_results": [],
            "all_db_results": {},
            "execution_error": error_msg,
            "query_type": "wider_search",  # Set the query type to wider_search
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }


def generate_response_node(state: AgentState) -> AgentState:
    """
    Node to generate natural language response using specialized LLM model
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_response_node - Generating response for request: {state['user_request']}")

    try:
        # Use the specialized LLM model to generate the final response
        response_generator = ResponseGenerator()

        # Generate the final response using the specialized prompt
        final_response = response_generator.generate_natural_language_response(
            state.get("response_prompt", "")  # Use the prompt generated in the previous step
        )

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] generate_response_node - Generated response in {elapsed_time:.2f}s: {final_response}")
        return {
            **state,
            "final_response": final_response,
            "query_type": state.get("query_type", "initial"),  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating response: {str(e)}"
        logger.error(f"[NODE ERROR] generate_response_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "final_response": f"Error generating response: {str(e)}",
            "query_type": state.get("query_type", "initial"),  # Preserve the query type
            "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
        }


def should_validate_sql(state: AgentState) -> Literal["safe", "unsafe"]:
    """
    Conditional edge to determine if SQL is safe to execute
    """
    if state.get("validation_error"):
        return "unsafe"
    return "safe"


def should_retry(state: AgentState) -> Literal["yes", "no"]:
    """
    Conditional edge to determine if we should retry SQL generation
    """
    # Check if we have errors and haven't exceeded retry limit
    has_error = (
        state.get("validation_error") or
        state.get("execution_error") or
        state.get("sql_generation_error")
    )

    # Use the same max_retries value for consistency
    max_retries = 5
    if has_error and state.get("retry_count", 0) < max_retries:
        logger.info(f"Retrying with retry count: {state.get('retry_count', 0)}")
        return "yes"
    return "no"


def should_refine_or_respond(state: AgentState) -> Literal["refine", "respond"]:
    """
    Conditional edge to determine if we should refine SQL or generate response
    """
    # Check if we have errors and haven't exceeded retry limit
    has_error = (
        state.get("validation_error") or
        state.get("execution_error") or
        state.get("sql_generation_error")
    )

    # Increase max retries to allow for more attempts, but still have a limit
    max_retries = 5
    if has_error and state.get("retry_count", 0) < max_retries:
        logger.info(f"Refining SQL with retry count: {state.get('retry_count', 0)}")
        return "refine"
    return "respond"


def should_validate_after_security_check(state: AgentState) -> Literal["refine", "respond"]:
    """
    Conditional edge to determine if we should validate SQL after security check or generate response
    """
    # Check if we have validation errors after security check and haven't exceeded retry limit
    has_validation_error = state.get("validation_error")

    if has_validation_error and state.get("retry_count", 0) < 3:
        logger.info(f"Validating SQL after security check with retry count: {state.get('retry_count', 0)}")
        return "refine"  # Go to validation after security failure
    return "respond"  # Proceed to response if security check passed


def should_execute_wider_search(state: AgentState) -> Literal["wider_search", "respond"]:
    """
    Conditional edge to determine if we should execute wider search when initial query returns no results
    """
    # Check if the database results are empty
    db_results = state.get("db_results", [])

    # Check if we've already tried wider search and are coming back to initial query execution
    # If query_type is 'wider_search', it means we've already tried the wider search approach
    current_query_type = state.get("query_type", "initial")

    # Check if we've exceeded the retry count to prevent infinite loops
    max_attempts = 5
    if not db_results and current_query_type == "initial" and state.get("retry_count", 0) < max_attempts:
        logger.info("Initial query returned no results, proceeding with wider search strategy")
        return "wider_search"
    else:
        logger.info(f"Initial query returned {len(db_results)} results or max attempts reached, proceeding directly to response generation")
        return "respond"


def create_enhanced_agent_graph():
    """
    Create the enhanced agent workflow using LangGraph
    """
    # Reload database configuration to ensure latest settings are used
    reload_database_config()

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("get_schema", get_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("refine_sql", refine_sql_node)
    workflow.add_node("generate_wider_search_query", generate_wider_search_query_node)  # New node for generating wider search query
    workflow.add_node("execute_wider_search", execute_wider_search_node)  # New node for executing wider search
    workflow.add_node("generate_prompt", generate_prompt_node)  # New node for generating specialized prompt
    workflow.add_node("generate_response", generate_response_node)

    # Define edges
    workflow.add_edge("get_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")

    # Create a conditional function to route to the appropriate execution node based on query type
    def route_after_validation(state: AgentState) -> Literal["execute_sql", "execute_wider_search", "refine_sql"]:
        """
        Conditional edge to determine where to go after validation based on query type
        """
        if state.get("validation_error"):
            return "refine_sql"  # Go to refine if validation failed
        elif state.get("query_type") == "wider_search":
            return "execute_wider_search"  # Go to execute wider search if this is a wider search query
        else:
            return "execute_sql"  # Otherwise, go to execute initial SQL

    # Conditional edges for validation
    workflow.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute_sql": "execute_sql",  # Go to execute initial SQL
            "execute_wider_search": "execute_wider_search",  # Go to execute wider search
            "refine_sql": "refine_sql"  # Go to refine if unsafe
        }
    )

    # Conditional edges for wider search decision after initial execution
    workflow.add_conditional_edges(
        "execute_sql",
        should_execute_wider_search,
        {
            "wider_search": "generate_wider_search_query",  # Go to wider search if initial query returned no results
            "respond": "generate_prompt"  # Go to generate prompt before response if initial query returned results
        }
    )

    # Add the new security check node
    workflow.add_node("security_check_after_refinement", security_check_after_refinement_node)

    # Conditional edges after refinement (before security check)
    workflow.add_conditional_edges(
        "refine_sql",
        should_refine_or_respond,
        {
            "refine": "security_check_after_refinement",  # Go to security check after refinement
            "respond": "execute_sql"  # Execute the refined SQL query
        }
    )

    # Conditional edges after security check
    workflow.add_conditional_edges(
        "security_check_after_refinement",
        should_validate_after_security_check,  # Use specific function for security check validation
        {
            "refine": "validate_sql",  # Go to validation after security check if refinement needed
            "respond": "execute_sql"  # Execute the SQL query after security check passes
        }
    )

    # Edges for wider search flow - need to check if wider search query generation was successful
    def route_after_wider_search_generation(state: AgentState) -> Literal["validate_sql", "generate_response"]:
        """
        Conditional edge to determine where to go after wider search query generation
        """
        # If final_response is set, it means the wider search generation failed
        if state.get("final_response") and "couldn't find any results" in state.get("final_response", ""):
            return "generate_response"  # Go directly to response generation
        else:
            return "validate_sql"  # Validate the wider search query

    workflow.add_conditional_edges(
        "generate_wider_search_query",
        route_after_wider_search_generation,
        {
            "validate_sql": "validate_sql",  # Validate the wider search query
            "generate_response": "generate_response"  # Go directly to response if wider search failed
        }
    )

    # Create a specific conditional function for wider search execution
    def should_continue_wider_search(state: AgentState) -> Literal["refine", "wider_search", "respond"]:
        """
        Conditional edge to determine next step after executing wider search
        """
        # Check if we have execution errors and haven't exceeded retry limit
        has_execution_error = state.get("execution_error")
        if has_execution_error and state.get("retry_count", 0) < 3:
            logger.info(f"Refining after wider search execution error with retry count: {state.get('retry_count', 0)}")
            return "refine"

        # Check if the wider search results are empty and we haven't exceeded retry limit
        db_results = state.get("db_results", [])
        # Increase the retry limit to allow for more attempts, but add a max limit to prevent infinite loops
        max_attempts = 5  # Maximum number of attempts for wider search
        if not db_results and state.get("retry_count", 0) < max_attempts:
            logger.info(f"Wider search returned no results, proceeding with another wider search strategy. Attempt: {state.get('retry_count', 0) + 1}/{max_attempts}")
            return "wider_search"
        else:
            logger.info(f"Wider search returned {len(db_results)} results, proceeding to response generation")
            return "respond"

    # Conditional edges after wider search execution
    workflow.add_conditional_edges(
        "execute_wider_search",
        should_continue_wider_search,
        {
            "refine": "refine_sql",  # Go to refine if wider search execution failed
            "wider_search": "generate_wider_search_query",  # If still no results, try another wider search
            "respond": "generate_prompt"  # If results found, proceed to generate prompt
        }
    )

    # Add edge from generate_prompt to generate_response
    workflow.add_edge("generate_prompt", "generate_response")
    workflow.add_edge("generate_response", END)

    # Set entry point
    workflow.set_entry_point("get_schema")

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
                "retry_count": state.get("retry_count", 0),
                "previous_sql_query_count": len(state.get("previous_sql_queries", []))
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
                "previous_sql_query_count": len(state.get("previous_sql_queries", [])),
                "errors": {
                    "validation": state.get("validation_error"),
                    "execution": state.get("execution_error"),
                    "generation": state.get("sql_generation_error")
                }
            }
        }
        self.execution_log.append(log_entry)
        logger.info(f"[GRAPH END] Completed in {total_time:.2f}s, retries: {state.get('retry_count', 0)}")


def run_enhanced_agent(user_request: str, disable_sql_blocking: bool = None) -> Dict[str, Any]:
    """
    Convenience function to run the enhanced agent with a user request
    """
    # Use the configuration value if disable_sql_blocking is not explicitly provided
    if disable_sql_blocking is None:
        # TERMINATE_ON_POTENTIALLY_HARMFUL_SQL means we should block harmful SQL,
        # so if it's True, disable_sql_blocking should be False, and vice versa
        disable_sql_blocking = not TERMINATE_ON_POTENTIALLY_HARMFUL_SQL

    # Create the graph
    graph = create_enhanced_agent_graph()

    # Define initial state
    initial_state: AgentState = {
        "user_request": user_request,
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "all_db_results": {},
        "table_to_db_mapping": {},
        "table_to_real_db_mapping": {},
        "response_prompt": "",  # Specialized prompt for response generation
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": disable_sql_blocking,
        "query_type": "initial",  # Set initial query type
        "previous_sql_queries": []  # Initialize with empty list of previous SQL queries
    }

    # Create monitoring callback
    callback_handler = AgentMonitoringCallback()
    callback_handler.on_graph_start(initial_state)

    # Run the graph
    result = graph.invoke(initial_state)

    callback_handler.on_graph_end(result)

    return {
        "original_request": user_request,
        "generated_sql": result.get("sql_query"),
        "db_results": result.get("db_results"),
        "all_db_results": result.get("all_db_results"),
        "table_to_db_mapping": result.get("table_to_db_mapping"),
        "table_to_real_db_mapping": result.get("table_to_real_db_mapping"),
        "response_prompt": result.get("response_prompt"),  # Include the specialized prompt
        "final_response": result.get("final_response"),
        "validation_error": result.get("validation_error"),
        "execution_error": result.get("execution_error"),
        "sql_generation_error": result.get("sql_generation_error"),
        "retry_count": result.get("retry_count"),
        "execution_log": [entry for entry in callback_handler.execution_log],  # Include execution log
        "query_type": result.get("query_type"),  # Include query type in the result
        "previous_sql_queries": result.get("previous_sql_queries")  # Include the history of SQL queries
    }


# Mark the current task as completed and move to the next one
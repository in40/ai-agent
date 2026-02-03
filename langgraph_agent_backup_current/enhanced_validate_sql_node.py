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

# Define the AgentState type here or import it from the main module
AgentState = Dict[str, Any]

def validate_sql_node(state: AgentState) -> AgentState:
    """
    Node to validate SQL query safety
    """
    start_time = time.time()
    sql = state["sql_query"]
    disable_blocking = state.get("disable_sql_blocking", False)
    schema_dump = state.get("schema_dump", {})

    logger.info(f"[NODE START] validate_sql_node - Validating SQL: {sql[:100]}... (blocking {'disabled' if disable_blocking else 'enabled'})")

    # If SQL blocking is disabled, skip all validations and return success
    if disable_blocking:
        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] validate_sql_node - SQL validation skipped (blocking disabled) in {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": None
        }

    # Basic validation: Check if query is empty
    if not sql or sql.strip() == "":
        error_msg = "SQL query is empty"
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
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
                    "retry_count": state.get("retry_count", 0) + 1
                }
            else:
                # If security LLM says it's safe, skip basic validation
                elapsed_time = time.time() - start_time
                logger.info(f"[NODE SUCCESS] validate_sql_node - Security LLM validation passed in {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": None
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
                    "retry_count": state.get("retry_count", 0) + 1
                }
        elif command in sql_lower:
            error_msg = f"Potentially harmful SQL detected: {command}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1
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
                "retry_count": state.get("retry_count", 0) + 1
            }

    # Check for dangerous patterns that might indicate SQL injection
    dangerous_patterns = [
        r"union\s+select",  # Could indicate SQL injection
        r"information_schema",  # Could be used to extract schema info
        r"pg_",  # PostgreSQL system tables/functions
        r"sqlite_",  # SQLite system tables/functions
        r"xp_",  # SQL Server extended procedures
        r"sp_",  # SQL Server stored procedures
        r"exec\s*\(",  # Execution functions
        r"execute\s*\(",  # Execution functions
        r"eval\s*\(",  # Evaluation functions
        r"waitfor\s+delay",  # Time-based attacks
        r"benchmark\s*\(",  # Performance-based attacks
        r"sleep\s*\(",  # Time-based attacks
        r"load_file\s*\(",  # MySQL file access
        r"into\s+outfile",  # MySQL file write
        r"into\s+dumpfile",  # MySQL file write
        r"cmdshell",  # SQL Server command execution
        r"polyfromtext",  # Potential geography function abuse
        r"st_astext",  # Potential geography function abuse
        r"cast\s*\([^)]+\s+as",  # Potential casting for injection
        r"convert\s*\(",  # Potential conversion for injection
        r"char\s*\(",  # Character code manipulation
        r"nchar\s*\(",  # Unicode character code manipulation
        r"substring\s*\(",  # String manipulation for extraction
        r"mid\s*\(",  # String manipulation for extraction
        r"asc\s*\(",  # ASCII value extraction
        r"hex\s*\(",  # Hexadecimal manipulation
        r"unhex\s*\(",  # Hexadecimal manipulation
        r"quote\s*\(",  # Quote manipulation
        r"concat\s*\(",  # String concatenation for injection
        r"group_concat\s*\(",  # Aggregation for data extraction
        r"load_xml\s*\(",  # XML loading for injection
        r"extractvalue\s*\(",  # XML extraction for injection
        r"updatexml\s*\(",  # XML update for injection
        r"fn:\w+",  # XPath function calls
        r"declare\s+@\w+\s*=",  # T-SQL variable declaration
        r"set\s+@\w+\s*=",  # T-SQL variable assignment
        r"openrowset\s*\(",  # T-SQL external data access
        r"opendatasource\s*\(",  # T-SQL external data access
        r"bulk\s+insert",  # Bulk data insertion
        r"openquery\s*\(",  # T-SQL remote query
        r"execute\s+as",  # T-SQL impersonation
        r"impersonate",  # Impersonation attempts
        r"shutdown",  # Database shutdown attempts
        r"backup\s+database",  # Database backup attempts
        r"restore\s+database",  # Database restore attempts
        r"addsignature",  # Signature addition
        r"makesignature",  # Signature creation
        r"dbms_\w+\.",  # Oracle DBMS packages
        r"utl_\w+\.",  # Oracle UTL packages
        r"ctxsys\.driddl",  # Oracle text index manipulation
        r"sys\.dbms",  # Oracle system package
        r"sys\.any",  # Oracle system types
        r"any_data",  # Oracle system type
        r"any_type",  # Oracle system type
        r"anydataset",  # Oracle system type
        r"sys\.xmlgen",  # Oracle XML generation
        r"sdo_util\.to_clob",  # Oracle spatial utility
        r"sdo_sql\.shapefilereader",  # Oracle spatial utility
        r"dbms_java\.grant_permission",  # Oracle Java permissions
        r"dbms_javaxx",  # Oracle Java permissions
        r"dbms_scheduler",  # Oracle job scheduling
        r"dbms_pipe",  # Oracle inter-session communication
        r"dbms_alert",  # Oracle alert system
        r"dbms_aq",  # Oracle queuing
        r"dbms_datapump",  # Oracle data pump
        r"dbms_metadata",  # Oracle metadata extraction
        r"dbms_repcat",  # Oracle replication
        r"dbms_registry",  # Oracle registry
        r"dbms_rule",  # Oracle rules engine
        r"dbms_streams",  # Oracle streaming
        r"dbms_system",  # Oracle system operations
        r"dbms_utility",  # Oracle utility functions
        r"dbms_workload_repository",  # Oracle workload repository
        r"dbms_xa",  # Oracle distributed transactions
        r"dbms_xstream",  # Oracle XStream
        r"dbms_crypto",  # Oracle cryptography
        r"dbms_random",  # Oracle random generation
        r"dbms_lock",  # Oracle locking mechanisms
        r"dbms_lob",  # Oracle LOB operations
        r"dbms_xmlgen",  # Oracle XML generation
        r"dbms_xmlstore",  # Oracle XML storage
        r"dbms_xmlschema",  # Oracle XML schema
        r"dbms_xmlquery",  # Oracle XML querying
        r"dbms_xmlsave",  # Oracle XML saving
        r"dbms_xmlparser",  # Oracle XML parsing
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
                "retry_count": state.get("retry_count", 0) + 1
            }

    # Check for multiple statements (semicolon-separated)
    if sql.count(';') > 1:
        error_msg = "Multiple SQL statements detected. Only single statements are allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
        }

    # Check for comment sequences that might be used to bypass filters
    if "/*" in sql or "--" in sql or "#" in sql:
        error_msg = "SQL comments detected. These are not allowed for safety."
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
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
        "validation_error": None
    }
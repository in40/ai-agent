"""
LangGraph implementation of the AI Agent with enhanced state management,
conditional logic, and error recovery capabilities.
"""

from typing import TypedDict, List, Dict, Any, Literal
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from utils.database import DatabaseManager
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
    db_results: List[Dict[str, Any]]
    final_response: str
    messages: List[BaseMessage]
    validation_error: str
    retry_count: int
    execution_error: str
    sql_generation_error: str
    disable_sql_blocking: bool


def get_schema_node(state: AgentState) -> AgentState:
    """
    Node to retrieve database schema
    """
    start_time = time.time()
    logger.info(f"[NODE START] get_schema_node - Processing request: {state['user_request'][:50]}...")

    try:
        db_manager = DatabaseManager()
        schema_dump = db_manager.get_schema_dump()
        elapsed_time = time.time() - start_time

        logger.info(f"[NODE SUCCESS] get_schema_node - Retrieved schema with {len(schema_dump)} tables in {elapsed_time:.2f}s")
        return {
            **state,
            "schema_dump": schema_dump,
            "sql_generation_error": None  # Clear any previous errors
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] get_schema_node - Error retrieving schema after {elapsed_time:.2f}s: {str(e)}")
        return {
            **state,
            "schema_dump": {},
            "sql_generation_error": f"Error retrieving schema: {str(e)}"
        }


def generate_sql_node(state: AgentState) -> AgentState:
    """
    Node to generate SQL query
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_sql_node - Generating SQL for request: {state['user_request'][:50]}...")

    try:
        sql_generator = SQLGenerator()
        sql_query = sql_generator.generate_sql(
            state["user_request"],
            state["schema_dump"]
        )
        elapsed_time = time.time() - start_time

        logger.info(f"[NODE SUCCESS] generate_sql_node - Generated SQL in {elapsed_time:.2f}s: {sql_query[:100]}...")
        return {
            **state,
            "sql_query": sql_query,
            "sql_generation_error": None  # Clear any previous errors
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] generate_sql_node - Error generating SQL after {elapsed_time:.2f}s: {str(e)}")
        return {
            **state,
            "sql_query": "",
            "sql_generation_error": f"Error generating SQL: {str(e)}",
            "retry_count": state.get("retry_count", 0) + 1
        }


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

    # Fallback to basic keyword matching if security LLM is disabled or failed
    logger.info("[NODE INFO] validate_sql_node - Using basic keyword matching for analysis")

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
    if not sql_lower.strip().startswith('select'):
        error_msg = "SQL query does not start with SELECT, which is required for safety"
        elapsed_time = time.time() - start_time
        logger.warning(f"[NODE WARNING] validate_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": error_msg,
            "retry_count": state.get("retry_count", 0) + 1
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

    # If all validations pass
    elapsed_time = time.time() - start_time
    logger.info(f"[NODE SUCCESS] validate_sql_node - SQL validation passed in {elapsed_time:.2f}s")
    return {
        **state,
        "validation_error": None
    }


def execute_sql_node(state: AgentState) -> AgentState:
    """
    Node to execute SQL query
    """
    start_time = time.time()
    logger.info(f"[NODE START] execute_sql_node - Executing SQL: {state['sql_query'][:100]}...")

    try:
        sql_executor = SQLExecutor(DatabaseManager())
        results = sql_executor.execute_sql_and_get_results(state["sql_query"])
        elapsed_time = time.time() - start_time

        logger.info(f"[NODE SUCCESS] execute_sql_node - Query executed in {elapsed_time:.2f}s, got {len(results)} results")
        return {
            **state,
            "db_results": results,
            "execution_error": None  # Clear any previous errors
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"SQL execution error: {str(e)}"
        logger.error(f"[NODE ERROR] execute_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "db_results": [],
            "execution_error": error_msg,
            "validation_error": error_msg  # Also set validation error to trigger retry
        }


def refine_sql_node(state: AgentState) -> AgentState:
    """
    Node to refine SQL query based on execution results or errors
    """
    start_time = time.time()
    logger.info(f"[NODE START] refine_sql_node - Refining SQL for request: {state['user_request'][:50]}...")

    try:
        # Get the error that led to refinement
        error_context = state.get("execution_error") or state.get("validation_error") or state.get("sql_generation_error")

        # Get the original request and schema
        user_request = state["user_request"]
        schema_dump = state["schema_dump"]
        current_sql = state["sql_query"]

        # Prevent infinite loops by checking if we're retrying with an empty query
        if not current_sql or current_sql.strip() == "":
            # If the current SQL is empty, try to generate a new one from scratch
            sql_generator = SQLGenerator()
            refined_sql = sql_generator.generate_sql(user_request, schema_dump)
        else:
            # Create a prompt to refine the SQL query based on the error
            refinement_prompt = f"""
            Original user request: {user_request}

            Current SQL query: {current_sql}

            Error encountered: {error_context}

            Schema information:
            {format_schema_dump(schema_dump)}

            Please generate a corrected SQL query that addresses the error while still fulfilling the original request.
            Make sure the query follows all safety guidelines (only SELECT statements, no harmful commands, etc.).
            """

            # Use the SQL generator to create a refined query
            sql_generator = SQLGenerator()
            refined_sql = sql_generator.generate_sql(refinement_prompt, schema_dump)

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] refine_sql_node - Refined SQL in {elapsed_time:.2f}s: {refined_sql[:100]}...")

        return {
            **state,
            "sql_query": refined_sql,
            "validation_error": None,  # Reset validation error
            "execution_error": None,   # Reset execution error
            "sql_generation_error": None  # Reset generation error
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error refining SQL query: {str(e)}"
        logger.error(f"[NODE ERROR] refine_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "sql_generation_error": error_msg
        }


def format_schema_dump(schema_dump):
    """
    Helper function to format the schema dump for the LLM
    """
    formatted = ""
    for table_name, columns in schema_dump.items():
        formatted += f"\nTable: {table_name}\n"
        for col in columns:
            formatted += f"  - {col['name']} ({col['type']}) - Nullable: {col['nullable']}\n"
    return formatted


def generate_response_node(state: AgentState) -> AgentState:
    """
    Node to generate natural language response
    """
    start_time = time.time()
    logger.info(f"[NODE START] generate_response_node - Generating response for request: {state['user_request'][:50]}...")

    try:
        prompt_generator = PromptGenerator()
        response_generator = ResponseGenerator()

        response_prompt = prompt_generator.generate_prompt_for_response_llm(
            state["user_request"],
            state["db_results"]
        )

        final_response = response_generator.generate_natural_language_response(
            response_prompt
        )

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] generate_response_node - Generated response in {elapsed_time:.2f}s: {final_response[:100]}...")
        return {
            **state,
            "final_response": final_response
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating response: {str(e)}"
        logger.error(f"[NODE ERROR] generate_response_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "final_response": f"Error generating response: {str(e)}"
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

    if has_error and state.get("retry_count", 0) < 3:
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

    if has_error and state.get("retry_count", 0) < 3:
        logger.info(f"Refining SQL with retry count: {state.get('retry_count', 0)}")
        return "refine"
    return "respond"


def create_enhanced_agent_graph():
    """
    Create the enhanced agent workflow using LangGraph
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("get_schema", get_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("refine_sql", refine_sql_node)
    workflow.add_node("generate_response", generate_response_node)

    # Define edges
    workflow.add_edge("get_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")

    # Conditional edges for validation
    workflow.add_conditional_edges(
        "validate_sql",
        should_validate_sql,
        {
            "safe": "execute_sql",
            "unsafe": "refine_sql"  # Go to refine if unsafe
        }
    )

    # Conditional edges for retries after execution
    workflow.add_conditional_edges(
        "execute_sql",
        should_refine_or_respond,
        {
            "refine": "refine_sql",  # Go to refine if execution failed
            "respond": "generate_response"
        }
    )

    # Conditional edges after refinement
    workflow.add_conditional_edges(
        "refine_sql",
        should_refine_or_respond,
        {
            "refine": "validate_sql",  # Go back to validation after refinement
            "respond": "generate_response"
        }
    )

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
                "retry_count": state.get("retry_count", 0)
            }
        }
        self.execution_log.append(log_entry)
        logger.info(f"[GRAPH START] Processing request: {state['user_request'][:50]}...")

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
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 0,
        "disable_sql_blocking": disable_sql_blocking
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
        "final_response": result.get("final_response"),
        "validation_error": result.get("validation_error"),
        "execution_error": result.get("execution_error"),
        "sql_generation_error": result.get("sql_generation_error"),
        "retry_count": result.get("retry_count"),
        "execution_log": [entry for entry in callback_handler.execution_log]  # Include execution log
    }


# Mark the current task as completed and move to the next one
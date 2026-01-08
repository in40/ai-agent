# LangGraph: Enhancing the AI Agent Architecture

## Introduction to LangGraph

LangGraph is an extension of LangChain that provides tools for building stateful, multi-step AI applications. Unlike simple LangChain chains (which are linear), LangGraph allows for complex workflows with conditional logic, loops, and state management.

## Key Differences: LangChain vs LangGraph

| Aspect | LangChain (Current Implementation) | LangGraph (Enhanced Implementation) |
|--------|-----------------------------------|-------------------------------------|
| Structure | Linear chains | Graph-based workflows |
| State | Stateless | Stateful |
| Control Flow | Sequential | Conditional, loops, parallel execution |
| Complexity | Simple operations | Complex, multi-step processes |
| Error Handling | Limited | Comprehensive with recovery mechanisms |
| Validation | Basic | Sophisticated with iterative refinement |
| Monitoring | Minimal | Detailed with execution tracking |
| Search Strategies | Single query approach | Wider search strategies when initial queries return no results |
| Prompt Generation | Direct response generation | Specialized prompt generation for response LLM |

## Current Architecture Limitations (Addressed)

The original implementation had several limitations that LangGraph now addresses:

1. **Linear Processing**: The workflow is now graph-based with conditional logic
2. **No Error Recovery**: Implemented automatic retry and refinement mechanisms
3. **No Iterative Refinement**: Added SQL refinement based on execution results
4. **No Validation Loop**: Implemented comprehensive validation with feedback loops
5. **Limited Monitoring**: Added detailed logging and execution tracking
6. **Single Query Approach**: Added wider search strategies when initial queries return no results
7. **Direct Response Generation**: Added specialized prompt generation for better response quality

## Enhanced LangGraph Implementation

### 1. State Definition

```python
from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    user_request: str
    schema_dump: Dict[str, Any]
    sql_query: str
    db_results: List[Dict[str, Any]]
    response_prompt: str  # Specialized prompt for response generation
    final_response: str
    messages: List[BaseMessage]
    validation_error: str
    execution_error: str
    sql_generation_error: str
    retry_count: int
    disable_sql_blocking: bool
    query_type: str  # Track whether this is an 'initial' query or 'wider_search' query
```

### 2. Node Definitions

#### Get Schema Node
```python
def get_schema_node(state: AgentState) -> AgentState:
    """Node to retrieve database schema with enhanced error handling"""
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
            "sql_generation_error": None,
            "query_type": "initial"  # Set the query type to initial
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"[NODE ERROR] get_schema_node - Error retrieving schema after {elapsed_time:.2f}s: {str(e)}")
        return {
            **state,
            "schema_dump": {},
            "sql_generation_error": f"Error retrieving schema: {str(e)}"
        }
```

#### Generate SQL Node
```python
def generate_sql_node(state: AgentState) -> AgentState:
    """Node to generate SQL query with enhanced error handling"""
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
            "sql_generation_error": None,  # Clear any previous errors
            "query_type": "initial"  # Set the query type to initial
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
```

#### Validate SQL Node
```python
def validate_sql_node(state: AgentState) -> AgentState:
    """Node to validate SQL query safety with comprehensive checks"""
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
```

#### Execute SQL Node
```python
def execute_sql_node(state: AgentState) -> AgentState:
    """Node to execute SQL query with enhanced error handling"""
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
            "execution_error": None,  # Clear any previous errors
            "query_type": state.get("query_type", "initial")  # Preserve the query type
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"SQL execution error: {str(e)}"
        logger.error(f"[NODE ERROR] execute_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "db_results": [],
            "execution_error": error_msg,
            "validation_error": error_msg,  # Also set validation error to trigger retry
            "query_type": state.get("query_type", "initial")  # Preserve the query type
        }
```

#### Refine SQL Node
```python
def refine_sql_node(state: AgentState) -> AgentState:
    """Node to refine SQL query based on execution results or errors"""
    start_time = time.time()
    logger.info(f"[NODE START] refine_sql_node - Refining SQL for request: {state['user_request'][:50]}...")

    try:
        # Get the error that led to refinement
        error_context = state.get("execution_error") or state.get("validation_error") or state.get("sql_generation_error")

        # Get the original request and schema
        user_request = state["user_request"]
        schema_dump = state["schema_dump"]
        current_sql = state["sql_query"]
        current_query_type = state.get("query_type", "initial")  # Preserve the current query type

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
            "sql_generation_error": None,  # Reset generation error
            "query_type": current_query_type  # Preserve the query type
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error refining SQL query: {str(e)}"
        logger.error(f"[NODE ERROR] refine_sql_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "sql_generation_error": error_msg
        }
```

#### Security Check After Refinement Node
```python
def security_check_after_refinement_node(state: AgentState) -> AgentState:
    """Node to perform security check on refined SQL query"""
    start_time = time.time()
    sql = state["sql_query"]
    disable_blocking = state.get("disable_sql_blocking", False)
    schema_dump = state.get("schema_dump", {})
    current_query_type = state.get("query_type", "initial")  # Preserve the current query type

    logger.info(f"[NODE START] security_check_after_refinement_node - Security checking refined SQL: {sql[:100]}... (blocking {'disabled' if disable_blocking else 'enabled'})")

    # If SQL blocking is disabled, skip security check and return success
    if disable_blocking:
        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] security_check_after_refinement_node - Security check skipped (blocking disabled) in {elapsed_time:.2f}s")
        return {
            **state,
            "validation_error": None,
            "query_type": current_query_type  # Preserve the query type
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
                    "query_type": current_query_type  # Preserve the query type
                }
            else:
                # If security LLM says it's safe, we can proceed
                elapsed_time = time.time() - start_time
                logger.info(f"[NODE SUCCESS] security_check_after_refinement_node - Security check passed in {elapsed_time:.2f}s")
                return {
                    **state,
                    "validation_error": None,
                    "query_type": current_query_type  # Preserve the query type
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
                    "query_type": current_query_type  # Preserve the query type
                }
        elif command in sql_lower:
            error_msg = f"Potentially harmful SQL detected after refinement: {command}"
            elapsed_time = time.time() - start_time
            logger.warning(f"[NODE WARNING] security_check_after_refinement_node - {error_msg} after {elapsed_time:.2f}s")
            return {
                **state,
                "validation_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
                "query_type": current_query_type  # Preserve the query type
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
            "query_type": current_query_type  # Preserve the query type
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
                "query_type": current_query_type  # Preserve the query type
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
            "query_type": current_query_type  # Preserve the query type
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
            "query_type": current_query_type  # Preserve the query type
        }

    # If all validations pass
    elapsed_time = time.time() - start_time
    logger.info(f"[NODE SUCCESS] security_check_after_refinement_node - Security check passed in {elapsed_time:.2f}s")
    return {
        **state,
        "validation_error": None,
        "query_type": current_query_type  # Preserve the query type
    }
```

#### Generate Wider Search Query Node
```python
def generate_wider_search_query_node(state: AgentState) -> AgentState:
    """Node to generate wider search query when initial query returns no results"""
    start_time = time.time()
    logger.info(f"[NODE START] generate_wider_search_query_node - Generating wider search query for request: {state['user_request'][:50]}...")

    try:
        # Use the prompt generator to create a wider search strategy
        prompt_generator = PromptGenerator()

        # Create context for wider search
        wider_search_context = f"""
        Original user request: {state['user_request']}

        Initial SQL query: {state['sql_query']}

        Database schema:
        {format_schema_dump(state['schema_dump'])}

        Initial query returned no results. Please suggest alternative search strategies or queries that might yield relevant data based on the schema and the original user request.
        """

        # Generate wider search prompt using the specialized wider search generator
        wider_search_prompt = prompt_generator.generate_wider_search_prompt(wider_search_context)

        # Use the SQL generator to create a new query based on the wider search suggestions
        sql_generator = SQLGenerator()
        new_sql_query = sql_generator.generate_sql(
            wider_search_prompt + f"\n\nBased on these suggestions, generate a new SQL query for the request: {state['user_request']}",
            state["schema_dump"]
        )

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] generate_wider_search_query_node - Generated wider search query in {elapsed_time:.2f}s: {new_sql_query[:100]}...")
        return {
            **state,
            "sql_query": new_sql_query,  # Update the SQL query with the wider search query
            "query_type": "wider_search",  # Set the query type to wider_search
            "retry_count": state.get("retry_count", 0) + 1  # Increment retry count to prevent infinite loops
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating wider search query: {str(e)}"
        logger.error(f"[NODE ERROR] generate_wider_search_query_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "final_response": f"Error generating wider search query: {str(e)}",
            "retry_count": state.get("retry_count", 0) + 1  # Increment retry count to prevent infinite loops
        }
```

#### Execute Wider Search Node
```python
def execute_wider_search_node(state: AgentState) -> AgentState:
    """Node to execute the wider search query"""
    start_time = time.time()
    logger.info(f"[NODE START] execute_wider_search_node - Executing wider search query: {state['sql_query'][:100]}...")

    try:
        sql_executor = SQLExecutor(DatabaseManager())
        results = sql_executor.execute_sql_and_get_results(state["sql_query"])
        elapsed_time = time.time() - start_time

        logger.info(f"[NODE SUCCESS] execute_wider_search_node - Wider search query executed in {elapsed_time:.2f}s, got {len(results)} results")
        return {
            **state,
            "db_results": results,
            "execution_error": None,  # Clear any previous errors
            "query_type": "wider_search"  # Set the query type to wider_search
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Wider search execution error: {str(e)}"
        logger.error(f"[NODE ERROR] execute_wider_search_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "db_results": [],
            "execution_error": error_msg,
            "query_type": "wider_search"  # Set the query type to wider_search
        }
```

#### Generate Prompt Node
```python
def generate_prompt_node(state: AgentState) -> AgentState:
    """Node to generate specialized prompt for the response LLM"""
    start_time = time.time()
    logger.info(f"[NODE START] generate_prompt_node - Generating specialized prompt for request: {state['user_request'][:50]}...")

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
            "query_type": state.get("query_type", "initial")  # Preserve the query type
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating specialized prompt: {str(e)}"
        logger.error(f"[NODE ERROR] generate_prompt_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "final_response": f"Error generating response: {str(e)}",
            "query_type": state.get("query_type", "initial")  # Preserve the query type
        }
```

#### Generate Response Node
```python
def generate_response_node(state: AgentState) -> AgentState:
    """Node to generate natural language response using specialized LLM model"""
    start_time = time.time()
    logger.info(f"[NODE START] generate_response_node - Generating response for request: {state['user_request'][:50]}...")

    try:
        # Use the specialized LLM model to generate the final response
        response_generator = ResponseGenerator()

        # Generate the final response using the specialized prompt
        final_response = response_generator.generate_natural_language_response(
            state.get("response_prompt", "")  # Use the prompt generated in the previous step
        )

        elapsed_time = time.time() - start_time
        logger.info(f"[NODE SUCCESS] generate_response_node - Generated response in {elapsed_time:.2f}s: {final_response[:100]}...")
        return {
            **state,
            "final_response": final_response,
            "query_type": state.get("query_type", "initial")  # Preserve the query type
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error generating response: {str(e)}"
        logger.error(f"[NODE ERROR] generate_response_node - {error_msg} after {elapsed_time:.2f}s")
        return {
            **state,
            "final_response": f"Error generating response: {str(e)}",
            "query_type": state.get("query_type", "initial")  # Preserve the query type
        }
```

### 3. Conditional Logic

#### Validation Decision
```python
def should_validate_sql(state: AgentState) -> Literal["safe", "unsafe"]:
    """Conditional edge to determine if SQL is safe to execute"""
    if state.get("validation_error"):
        return "unsafe"
    return "safe"
```

#### Refinement Decision
```python
def should_refine_or_respond(state: AgentState) -> Literal["refine", "respond"]:
    """Conditional edge to determine if we should refine SQL or generate response"""
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
```

#### Route After Validation Decision
```python
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
```

#### Execute Wider Search Decision
```python
def should_execute_wider_search(state: AgentState) -> Literal["wider_search", "respond"]:
    """
    Conditional edge to determine if we should execute wider search when initial query returns no results
    """
    # Check if the database results are empty
    db_results = state.get("db_results", [])

    if not db_results:
        logger.info("Initial query returned no results, proceeding with wider search strategy")
        return "wider_search"
    else:
        logger.info(f"Initial query returned {len(db_results)} results, proceeding directly to response generation")
        return "respond"
```

#### Continue Wider Search Decision
```python
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
    if not db_results and state.get("retry_count", 0) < 3:
        logger.info("Wider search returned no results, proceeding with another wider search strategy")
        return "wider_search"
    else:
        logger.info(f"Wider search returned {len(db_results)} results, proceeding to response generation")
        return "respond"
```

### 4. Enhanced Workflow Diagram

```
                    ┌─────────────────┐
                    │   get_schema    │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  generate_sql   │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  validate_sql   │
                    └─────────┬───────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
           ┌─────────────────┐   ┌─────────────────┐
           │  execute_sql    │   │  refine_sql     │
           └─────────┬───────┘   └─────────┬───────┘
                     │                     │
                     │                     │
                     │         ┌───────────┘
                     │         │
                     ▼         ▼
           ┌─────────────────┐ │
           │ should_execute_ │ │
           │ _wider_search   │◄┘
           └─────────┬───────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ generate_wider_ │  │ generate_prompt │
    │ _search_query   │  │                 │
    └─────────┬───────┘  └─────────┬───────┘
              │                     │
              │         ┌───────────┘
              │         │
              ▼         ▼
    ┌─────────────────┐ │
    │ execute_wider_  │ │
    │ _search         │◄┘
    └─────────┬───────┘
              │
              ▼
    ┌─────────────────┐
    │ should_continue_│
    │ _wider_search   │
    └─────────┬───────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────────┐  ┌─────────────────┐
│generate_resp│  │  refine_sql     │
│             │  │                 │
└─────────────┘  └─────────────────┘
         │                  │
         └──────────────────┘
                    │
                    ▼
           ┌────────────┐
           │   END      │
           └────────────┘
```

### 5. Specialized LLM Model for Final Response Generation

The enhanced LangGraph implementation includes a two-step process for generating the final response:

1. **Specialized Prompt Generation**: The `generate_prompt_node` creates a tailored prompt for the response LLM based on the user's original request and the database query results. This specialized prompt guides the response LLM on how to format and structure the answer appropriately.

2. **Final Response Generation**: The `generate_response_node` uses a specialized LLM model to generate the natural language response based on the specialized prompt created in the previous step. This ensures that the final response is well-structured, accurate, and in natural language that is easy for the user to understand.

This two-step approach allows for better control over the response generation process and enables the use of different LLM models optimized for different tasks (one for prompt creation and another for response generation).

## Benefits of Enhanced LangGraph Implementation

### 1. Error Handling and Recovery
- Automatic retry mechanisms when SQL generation fails
- Graceful degradation when database queries fail
- Feedback loops to improve query generation
- Prevention of infinite loops during refinement

### 2. Validation and Safety
- Built-in validation steps before executing SQL
- Conditional logic to prevent harmful queries
- Iterative refinement of queries based on errors
- Comprehensive checks for SQL injection patterns
- Option to disable SQL blocking for trusted environments
- Advanced security LLM analysis to reduce false positives
- Context-aware security analysis that considers database schema
- Configurable security policies via environment variables
- Support for both basic keyword matching and advanced LLM-based analysis
- Security check after refinement to ensure refined queries are safe

### 3. State Management
- Persistent state across multiple steps
- Ability to track retry counts and validation errors
- Audit trail of all processing steps
- Detailed execution logs for monitoring
- Query type tracking to differentiate between initial and wider search queries

### 4. Flexibility
- Easy addition of new processing steps
- Conditional execution based on results
- Parallel processing capabilities
- Configurable retry limits

### 5. Wider Search Strategies
- Automatic fallback to wider search when initial queries return no results
- Generation of alternative queries based on schema and original request
- Iterative refinement of wider search strategies
- Prevention of infinite loops during wider search

### 6. Monitoring and Observability
- Detailed logging with timing information
- Execution tracking with timestamps
- Error categorization and reporting
- Performance metrics for each node

## Implementation Considerations

### 1. Migration Strategy
- Keep existing LangChain components as nodes
- Gradually migrated to graph structure
- Maintained backward compatibility during transition

### 2. Performance
- Added timing measurements for performance analysis
- Optimized validation checks to minimize overhead
- Implemented proper state management

### 3. Monitoring
- Enhanced logging for graph execution
- Step-by-step tracking of state changes
- Performance metrics for each node

## Testing

A comprehensive test suite has been created to validate all components:
- Individual node testing
- Integration testing of the full graph
- Error handling scenario testing
- Edge case validation
- Wider search strategy testing
- Security analysis testing

## Conclusion

The enhanced LangGraph implementation transforms the original linear workflow into a more intelligent, adaptive system capable of handling complex scenarios and edge cases more effectively. The graph-based approach enables:

- Better error handling and recovery mechanisms
- Conditional logic for validation and safety
- Iterative refinement of SQL queries
- More sophisticated state management
- Comprehensive monitoring and logging
- Prevention of infinite loops during error recovery
- Advanced security analysis with both basic keyword matching and LLM-based approaches
- Configurable security policies to balance safety and usability
- Support for multiple LLM providers (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)
- Wider search strategies when initial queries return no results
- Specialized prompt generation for improved response quality
- Query type tracking to differentiate between initial and wider search queries

This implementation provides a robust foundation for building production-ready AI agents with advanced capabilities for database querying and natural language processing.
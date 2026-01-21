# Retry Mechanism and Error Handling Documentation

## Overview

The system implements a sophisticated retry mechanism and comprehensive error handling system to ensure robust operation and graceful degradation when issues occur. The system handles three main types of errors: validation errors, execution errors, and SQL generation errors.

## Error Types

### 1. Validation Errors
- Occur when SQL queries fail security or syntax validation
- Checked by `validate_sql_node` and `security_check_after_refinement_node`
- Include detection of harmful commands, dangerous patterns, and invalid syntax

### 2. Execution Errors
- Occur when SQL queries fail to execute against the database
- May be due to table/column mismatches, permission issues, or database connectivity problems
- Captured during query execution in `execute_sql_node` and `execute_wider_search_node`

### 3. SQL Generation Errors
- Occur when the SQL generation process fails
- May be due to LLM errors, schema parsing issues, or other generation problems
- Captured during SQL generation in `generate_sql_node` and `refine_sql_node`

## Retry Mechanism

### Retry Limits
The system implements configurable retry limits to prevent infinite loops:
- Default maximum retry attempts: 10
- Applied consistently across all retry scenarios
- Tracks retry count in the state to enforce limits

### Conditional Retry Logic

#### should_retry Function
Determines if the system should retry SQL generation based on error presence and retry count:

```python
def should_retry(state: AgentState) -> Literal["yes", "no"]:
    # Check if we have errors and haven't exceeded retry limit
    has_error = (
        state.get("validation_error") or
        state.get("execution_error") or
        state.get("sql_generation_error")
    )

    # Use the same max_retries value for consistency
    max_retries = 10  # Updated to 10 attempts as per requirement
    if has_error and state.get("retry_count", 0) < max_retries:
        logger.info(f"Retrying with retry count: {state.get('retry_count', 0)}")
        return "yes"
    return "no"
```

#### should_refine_or_respond Function
Decides between refining SQL or generating response based on error status:

```python
def should_refine_or_respond(state: AgentState) -> Literal["refine", "respond"]:
    # Check if we have errors and haven't exceeded retry limit
    has_error = (
        state.get("validation_error") or
        state.get("execution_error") or
        state.get("sql_generation_error")
    )

    # Increase max retries to allow for more attempts, but still have a limit
    max_retries = 10  # Updated to 10 attempts as per requirement
    if has_error and state.get("retry_count", 0) < max_retries:
        logger.info(f"Refining SQL with retry count: {state.get('retry_count', 0)}")
        return "refine"
    return "respond"
```

#### should_execute_wider_search Function
Manages retry logic for wider search scenarios:

```python
def should_execute_wider_search(state: AgentState) -> Literal["wider_search", "respond"]:
    # Check if the database results are empty
    db_results = state.get("db_results", [])

    # Check if we have execution errors
    has_execution_error = bool(state.get("execution_error"))

    # Check if we've already tried wider search and are coming back to initial query execution
    # If query_type is 'wider_search', it means we've already tried the wider search approach
    current_query_type = state.get("query_type", "initial")

    # Check if we've exceeded the retry count to prevent infinite loops
    max_attempts = 10  # Increase to 10 attempts as per requirement

    # If there are execution errors, always go to wider search regardless of results
    if has_execution_error:
        logger.info("Execution errors detected, proceeding with wider search strategy to fix errors")
        return "wider_search"
    elif not db_results and current_query_type == "initial" and state.get("retry_count", 0) < max_attempts:
        logger.info("Initial query returned no results, proceeding with wider search strategy")
        return "wider_search"
    else:
        logger.info(f"Initial query returned {len(db_results)} results or max attempts reached, proceeding directly to response generation")
        return "respond"
```

#### should_continue_wider_search Function
Manages retry logic specifically for wider search execution:

```python
def should_continue_wider_search(state: AgentState) -> Literal["refine", "wider_search", "respond"]:
    # Check if we have execution errors
    has_execution_error = state.get("execution_error")

    # Check if the wider search results are empty
    db_results = state.get("db_results", [])
    no_results = not db_results

    # Check if we've exceeded the retry count to prevent infinite loops
    max_attempts = 10  # Maximum number of attempts for wider search as per requirement

    # If there are execution errors, continue with wider search until no errors found
    if has_execution_error and state.get("retry_count", 0) < max_attempts:
        logger.info(f"Execution errors found after wider search, proceeding with another wider search strategy to fix errors. Attempt: {state.get('retry_count', 0) + 1}/{max_attempts}")
        return "wider_search"
    # If no results returned and we haven't exceeded max attempts, continue with wider search
    elif no_results and state.get("retry_count", 0) < max_attempts:
        logger.info(f"Wider search returned no results, proceeding with another wider search strategy. Attempt: {state.get('retry_count', 0) + 1}/{max_attempts}")
        return "wider_search"
    else:
        logger.info(f"Wider search returned {len(db_results)} results or max attempts reached, proceeding to response generation")
        return "respond"
```

## Error Handling Workflow

### 1. Initial Error Detection
Errors are detected at multiple points in the workflow:
- During SQL generation in `generate_sql_node`
- During validation in `validate_sql_node`
- During execution in `execute_sql_node`
- During wider search in `generate_wider_search_query_node` and `execute_wider_search_node`

### 2. Error Accumulation
The system accumulates different types of errors:

```python
# Get all errors that led to refinement
all_errors = []
if state.get("execution_error"):
    all_errors.append(f"Execution error: {state['execution_error']}")
if state.get("validation_error"):
    all_errors.append(f"Validation error: {state['validation_error']}")
if state.get("sql_generation_error"):
    all_errors.append(f"SQL generation error: {state['sql_generation_error']}")

error_context = "; ".join(all_errors) if all_errors else "Unknown error occurred"
```

### 3. Error-Informed Refinement
When errors occur, the system creates a refinement prompt that includes all error information:

```python
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
```

### 4. Retry Counter Management
The system carefully manages the retry counter to prevent infinite loops:

```python
return {
    **state,
    "sql_query": refined_sql,
    "validation_error": None,  # Reset validation error
    "execution_error": None,   # Reset execution error
    "sql_generation_error": None,  # Reset generation error
    "query_type": current_query_type,  # Preserve the query type
    "retry_count": state.get("retry_count", 0) + 1  # Increment retry count
}
```

## Error Recovery Strategies

### 1. SQL Refinement
When validation or execution errors occur, the system refines the SQL query using error context:

```python
def refine_sql_node(state: AgentState) -> AgentState:
    # Get all errors that led to refinement
    all_errors = []
    if state.get("execution_error"):
        all_errors.append(f"Execution error: {state['execution_error']}")
    if state.get("validation_error"):
        all_errors.append(f"Validation error: {state['validation_error']}")
    if state.get("sql_generation_error"):
        all_errors.append(f"SQL generation error: {state['sql_generation_error']}")

    error_context = "; ".join(all_errors) if all_errors else "Unknown error occurred"

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
        table_to_db_mapping=state.get("table_to_db_mapping"),
        table_to_real_db_mapping=state.get("table_to_real_db_mapping")
    )
```

### 2. Wider Search Activation
When initial queries return no results, the system activates wider search strategies:

```python
def should_execute_wider_search(state: AgentState) -> Literal["wider_search", "respond"]:
    # If there are execution errors, always go to wider search regardless of results
    if has_execution_error:
        logger.info("Execution errors detected, proceeding with wider search strategy to fix errors")
        return "wider_search"
    elif not db_results and current_query_type == "initial" and state.get("retry_count", 0) < max_attempts:
        logger.info("Initial query returned no results, proceeding with wider search strategy")
        return "wider_search"
    else:
        logger.info(f"Initial query returned {len(db_results)} results or max attempts reached, proceeding directly to response generation")
        return "respond"
```

### 3. Fallback Mechanisms
The system includes fallback mechanisms when primary approaches fail:

```python
# In generate_wider_search_query_node, if wider search generation fails:
return {
    **state,
    "final_response": "I couldn't find any results for your query. The database doesn't contain the information requested.",
    "query_type": "wider_search",  # Mark as wider search to indicate we tried
    "retry_count": state.get("retry_count", 0) + 1,  # Increment retry count to prevent infinite loops
    "previous_sql_queries": state.get("previous_sql_queries", [])  # Preserve the history of SQL queries
}
```

## Monitoring and Logging

The system includes comprehensive monitoring and logging for error handling:

```python
class AgentMonitoringCallback:
    def on_graph_start(self, state: AgentState):
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
```

## Benefits of the Error Handling System

1. **Robust Operation**: Continues functioning even when individual components fail
2. **Graceful Degradation**: Provides meaningful responses when complete solutions aren't possible
3. **Learning from Errors**: Uses error context to improve subsequent attempts
4. **Prevention of Infinite Loops**: Implements retry limits to prevent resource exhaustion
5. **Comprehensive Coverage**: Handles multiple types of errors across the workflow
6. **Transparent Operation**: Logs all error handling activities for debugging and monitoring
7. **Flexible Recovery**: Employs multiple recovery strategies depending on error type
8. **Context Preservation**: Maintains important state information during error recovery
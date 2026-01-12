# State Management and Conditional Logic Documentation

## State Definition

The system uses a comprehensive state structure defined as follows:

```python
class AgentState(TypedDict):
    user_request: str                           # Original user request in natural language
    schema_dump: Dict[str, Any]                 # Combined schema from all databases
    sql_query: str                              # Current SQL query being processed
    db_results: List[Dict[str, Any]]            # Combined results from all databases
    all_db_results: Dict[str, List[Dict[str, Any]]]  # Results grouped by database name
    table_to_db_mapping: Dict[str, str]         # Maps table names to database names
    table_to_real_db_mapping: Dict[str, str]    # Maps table names to real database names
    response_prompt: str                        # Specialized prompt for response generation
    final_response: str                         # Final natural language response
    messages: List[BaseMessage]                 # LangChain message history
    validation_error: str                       # Error from SQL validation
    retry_count: int                            # Number of retry attempts
    execution_error: str                        # Error from SQL execution
    sql_generation_error: str                   # Error from SQL generation
    disable_sql_blocking: bool                  # Flag to disable SQL security blocking
    query_type: str                             # Type of query ('initial' or 'wider_search')
    database_name: str                          # Name of database used for queries
    previous_sql_queries: List[str]             # History of all previously generated SQL queries
```

## State Management Principles

### 1. Persistent State Updates
Each node in the workflow updates the state with relevant information while preserving existing data:

```python
return {
    **state,                                    # Preserve all existing state
    "sql_query": refined_sql,                  # Add/update specific field
    "validation_error": None,                  # Reset validation error
    "execution_error": None,                   # Reset execution error
    "sql_generation_error": None,              # Reset generation error
    "query_type": current_query_type,          # Preserve the query type
    "previous_sql_queries": updated_previous_queries  # Update the history of SQL queries
}
```

### 2. Query History Tracking
The system maintains a history of all previously generated SQL queries to ensure:
- Continuity in query generation
- Prevention of repeated failed approaches
- Better context for decision-making

```python
# Update the list of previous SQL queries with the newly refined query
previous_queries = state.get("previous_sql_queries", [])
updated_previous_queries = previous_queries + [refined_sql] if refined_sql else previous_queries
```

### 3. Error Propagation and Handling
Errors are preserved in the state and used to guide the workflow:

```python
if state.get("validation_error"):
    return "unsafe"  # Route to refinement
return "safe"        # Route to execution
```

## Conditional Logic Functions

### 1. should_validate_sql
Determines if SQL is safe to execute based on validation status:

```python
def should_validate_sql(state: AgentState) -> Literal["safe", "unsafe"]:
    if state.get("validation_error"):
        return "unsafe"
    return "safe"
```

### 2. should_retry
Determines if the system should retry SQL generation based on error presence and retry count:

```python
def should_retry(state: AgentState) -> Literal["yes", "no"]:
    has_error = (
        state.get("validation_error") or
        state.get("execution_error") or
        state.get("sql_generation_error")
    )

    max_retries = 10  # Updated to 10 attempts as per requirement
    if has_error and state.get("retry_count", 0) < max_retries:
        logger.info(f"Retrying with retry count: {state.get('retry_count', 0)}")
        return "yes"
    return "no"
```

### 3. should_refine_or_respond
Decides between refining SQL or generating response based on error status:

```python
def should_refine_or_respond(state: AgentState) -> Literal["refine", "respond"]:
    has_error = (
        state.get("validation_error") or
        state.get("execution_error") or
        state.get("sql_generation_error")
    )

    max_retries = 10  # Updated to 10 attempts as per requirement
    if has_error and state.get("retry_count", 0) < max_retries:
        logger.info(f"Refining SQL with retry count: {state.get('retry_count', 0)}")
        return "refine"
    return "respond"
```

### 4. should_validate_after_security_check
Handles validation after security check:

```python
def should_validate_after_security_check(state: AgentState) -> Literal["refine", "respond"]:
    has_validation_error = state.get("validation_error")

    if has_validation_error and state.get("retry_count", 0) < 10:  # Updated to 10 attempts
        logger.info(f"Validating SQL after security check with retry count: {state.get('retry_count', 0)}")
        return "refine"  # Go to validation after security failure
    return "respond"  # Proceed to response if security check passed
```

### 5. should_execute_wider_search
Triggers wider search when initial query returns no results:

```python
def should_execute_wider_search(state: AgentState) -> Literal["wider_search", "respond"]:
    db_results = state.get("db_results", [])
    has_execution_error = bool(state.get("execution_error"))
    current_query_type = state.get("query_type", "initial")
    max_attempts = 10  # Increase to 10 attempts as per requirement

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

### 6. route_after_validation
Routes to appropriate execution node based on validation and query type:

```python
def route_after_validation(state: AgentState) -> Literal["execute_sql", "execute_wider_search", "refine_sql"]:
    if state.get("validation_error"):
        return "refine_sql"  # Go to refine if validation failed
    elif state.get("query_type") == "wider_search":
        return "execute_wider_search"  # Go to execute wider search if this is a wider search query
    else:
        return "execute_sql"  # Otherwise, go to execute initial SQL
```

### 7. should_continue_wider_search
Determines next step after executing wider search:

```python
def should_continue_wider_search(state: AgentState) -> Literal["refine", "wider_search", "respond"]:
    has_execution_error = state.get("execution_error")
    db_results = state.get("db_results", [])
    no_results = not db_results
    max_attempts = 10  # Maximum number of attempts for wider search

    if has_execution_error and state.get("retry_count", 0) < max_attempts:
        logger.info(f"Execution errors found after wider search, proceeding with another wider search strategy to fix errors. Attempt: {state.get('retry_count', 0) + 1}/{max_attempts}")
        return "wider_search"
    elif no_results and state.get("retry_count", 0) < max_attempts:
        logger.info(f"Wider search returned no results, proceeding with another wider search strategy. Attempt: {state.get('retry_count', 0) + 1}/{max_attempts}")
        return "wider_search"
    else:
        logger.info(f"Wider search returned {len(db_results)} results or max attempts reached, proceeding to response generation")
        return "respond"
```

## State Transitions

The system implements a complex state transition system with multiple pathways:

1. **Normal Path**: Get Schema → Generate SQL → Validate SQL → Execute SQL → Generate Prompt → Generate Response

2. **Error Recovery Path**: Validation Error → Refine SQL → Security Check → Execute SQL

3. **Wider Search Path**: No Results → Generate Wider Search Query → Validate → Execute Wider Search → Generate Prompt → Generate Response

4. **Retry Loop**: When errors occur, the system can loop back to earlier stages up to the maximum retry count

## Key State Management Patterns

### 1. Immutable State Updates
Each node returns a new state dictionary rather than modifying the existing state directly:

```python
return {
    **state,  # Preserve all existing state
    "field_name": new_value  # Update specific field
}
```

### 2. Error Accumulation
Errors from multiple sources are accumulated and preserved in the state:

```python
all_errors = []
if state.get("execution_error"):
    all_errors.append(f"Execution error: {state['execution_error']}")
if state.get("validation_error"):
    all_errors.append(f"Validation error: {state['validation_error']}")
if state.get("sql_generation_error"):
    all_errors.append(f"SQL generation error: {state['sql_generation_error']}")
```

### 3. Conditional Routing
The workflow uses conditional functions to determine the next node based on the current state:

```python
workflow.add_conditional_edges(
    "validate_sql",
    route_after_validation,
    {
        "execute_sql": "execute_sql",           # Go to execute initial SQL
        "execute_wider_search": "execute_wider_search",  # Go to execute wider search
        "refine_sql": "refine_sql"             # Go to refine if unsafe
    }
)
```

This comprehensive state management system enables the LangGraph agent to handle complex workflows with multiple error recovery paths while maintaining context and preventing infinite loops through retry limits.
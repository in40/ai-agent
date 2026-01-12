# Wider Search Functionality Documentation

## Overview

The wider search functionality is a key feature of the LangGraph-based AI agent that automatically activates when initial SQL queries return no results. This system intelligently suggests alternative search strategies based on schema analysis and previous attempts to find relevant data.

## Trigger Conditions

The wider search functionality activates under the following conditions:

1. **No Results from Initial Query**: When the initial SQL query execution returns an empty result set
2. **Execution Errors**: When the initial query encounters execution errors that suggest the approach might need refinement
3. **Maximum Attempts Not Reached**: When the retry count is below the maximum threshold (currently 10 attempts)

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

## Wider Search Components

### 1. Generate Wider Search Query Node

This node analyzes the original request, initial query, schema information, and previous attempts to generate alternative search strategies:

```python
def generate_wider_search_query_node(state: AgentState) -> AgentState:
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
```

### 2. Execute Wider Search Node

This node executes the wider search query across all available databases:

```python
def execute_wider_search_node(state: AgentState) -> AgentState:
    # Get all available database names
    all_databases = DatabaseManager.list_databases()

    # Extract table names from the SQL query to determine if it's a cross-database query
    sql_executor = SQLExecutor()
    table_names = sql_executor._extract_table_names(state["sql_query"])

    # Execute the query based on whether it's a cross-database query
    all_db_results = {}
    combined_results = []

    # Track execution errors to provide better feedback to the LLM
    execution_errors = []

    if len(databases_with_tables) > 1:
        # This is a cross-database query, execute using the special method
        results = sql_executor.execute_sql_and_get_results(state["sql_query"], "all_databases", state.get("table_to_db_mapping"))
        combined_results = results
    else:
        # Execute on individual databases as before
        for db_name in all_databases:
            results = sql_executor.execute_sql_and_get_results(state["sql_query"], db_name, state.get("table_to_db_mapping"))
            # Store results by database name
            all_db_results[db_name] = results
            # Combine results from all databases
            combined_results.extend(results)
```

## Wider Search Strategies

The wider search functionality employs several strategies to find relevant data:

### 1. Schema-Based Analysis
- Examines all available tables and columns in the database schema
- Identifies tables that might contain relevant information based on naming conventions and column descriptions
- Looks for tables with correlating columns/data across different databases

### 2. Partial Matching
- Uses LIKE operators with wildcards for partial matches when exact matches fail
- Implements broader search patterns to capture similar data

### 3. Related Table Exploration
- Searches in related tables that might contain relevant information
- Uses JOIN operations to connect related tables across databases when appropriate

### 4. Broader Category Search
- Uses broader categories or classifications when specific values don't yield results
- Applies more general search criteria based on the schema structure

### 5. Full-Text Search
- Leverages full-text search capabilities when available in the database
- Uses advanced search techniques to find relevant data patterns

### 6. Alternative Search Terms
- Suggests alternative search terms based on the schema and column names
- Makes reasonable assumptions based on available data structures

## Integration with Previous Attempts

The wider search functionality integrates with the system's history of previous attempts:

```python
# Generate wider search prompt using the specialized wider search generator
wider_search_prompt = prompt_generator.generate_wider_search_prompt(
    wider_search_context,
    schema_dump=state['schema_dump'],
    db_mapping=state.get('table_to_db_mapping'),
    previous_sql_queries=previous_sql_queries  # Pass previous queries to avoid repetition
)
```

This ensures that:
- Approaches already attempted are not repeated
- Insights from previous failures inform new strategies
- The system learns from past attempts to improve future queries

## Conditional Logic for Wider Search

The system uses specific conditional logic to manage the wider search flow:

```python
def route_after_wider_search_generation(state: AgentState) -> Literal["validate_sql", "generate_response"]:
    # If final_response is set, it means the wider search generation failed
    if state.get("final_response") and "couldn't find any results" in state.get("final_response", ""):
        return "generate_response"  # Go directly to response generation
    else:
        return "validate_sql"  # Validate the wider search query
```

And to determine continuation:

```python
def should_continue_wider_search(state: AgentState) -> Literal["refine", "wider_search", "respond"]:
    # Check if we have execution errors
    has_execution_error = state.get("execution_error")

    # Check if the wider search results are empty
    db_results = state.get("db_results", [])
    no_results = not db_results

    # Check if we've exceeded the retry count to prevent infinite loops
    max_attempts = 10  # Maximum number of attempts for wider search

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

## Wider Search Prompt Template

The wider search functionality uses a specialized prompt template that includes:

- Original user request
- Initial SQL query that returned no results
- Complete database schema
- Previous SQL queries to avoid repetition
- Specific instructions for alternative search strategies

The prompt emphasizes:
- Looking for correlating columns/data across different databases
- Using JOIN when data required is in more than one table
- Prioritizing JOIN over other techniques
- Making reasonable assumptions based on schema
- Using real tables and columns in suggestions
- Avoiding invented tables/columns

## Error Handling in Wider Search

The wider search functionality includes robust error handling:

- Execution errors are captured and analyzed
- Failed wider search attempts are logged
- The system distinguishes between query execution errors and empty results
- Automatic fallback to response generation when wider search fails repeatedly
- Retry limits to prevent infinite loops

## Benefits of Wider Search

1. **Improved Data Discovery**: Finds relevant data even when initial queries fail
2. **Intelligent Alternatives**: Suggests logical alternatives based on schema analysis
3. **Learning from Failures**: Avoids repeating unsuccessful approaches
4. **Comprehensive Coverage**: Explores multiple databases and tables systematically
5. **Automatic Activation**: Seamlessly activates when needed without user intervention
6. **Retry Management**: Balances persistence with resource efficiency through retry limits
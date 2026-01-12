# SQL Generation and Wider Search System

## Overview
This system is a sophisticated LangGraph-based AI agent that processes natural language requests into SQL queries and executes them across multiple databases. The system features enhanced state management, conditional logic, and error recovery capabilities.

The architecture consists of multiple interconnected components:
1. **SQL Generator** (`sql_generator.txt`) - generates SQL queries based on natural language requests
2. **Wider Search Generator** (`wider_search_generator.txt`) - suggests alternative search strategies when initial queries return no results
3. **SQL Executor** - executes queries across multiple databases using table-to-database mappings
4. **Security SQL Detector** - validates queries for potential security issues
5. **Prompt Generator** - creates specialized prompts for response generation
6. **Response Generator** - produces natural language responses from query results

## Key Features

### Enhanced State Management
The system maintains comprehensive state information including:
- User request and schema information
- Generated SQL queries and execution results
- Table-to-database mappings for multi-database support
- Specialized prompts for response generation
- Validation and execution errors
- Retry counts and execution logs
- **History of ALL previously generated SQL queries** to ensure continuity and prevent repeated failed approaches

### Multi-Database Support
- Retrieves schema information from all available databases
- Creates mappings between table names and database names
- Executes queries on appropriate databases based on table-to-database mapping
- Supports cross-database queries when needed

### Advanced Error Handling and Recovery
- Comprehensive SQL validation with both basic keyword matching and advanced LLM-based security analysis
- Multiple retry attempts with refinement of queries based on error feedback
- Detailed error categorization (validation, execution, generation)
- Automatic retry limits to prevent infinite loops

### Wider Search Capability
- Automatically triggers alternative search strategies when initial queries return no results
- Generates wider search queries based on schema analysis and previous attempts
- Continues searching until results are found or maximum attempts reached

### Security Features
- Dual-layer security checking (basic validation + LLM-based analysis)
- Blocking of potentially harmful SQL commands
- Protection against SQL injection patterns
- Configurable security settings

## Implementation Details

### State Definition
The system uses the following state structure:
```python
class AgentState(TypedDict):
    user_request: str
    schema_dump: Dict[str, Any]
    sql_query: str
    db_results: List[Dict[str, Any]]
    all_db_results: Dict[str, List[Dict[str, Any]]]
    table_to_db_mapping: Dict[str, str]
    table_to_real_db_mapping: Dict[str, str]
    response_prompt: str
    final_response: str
    messages: List[BaseMessage]
    validation_error: str
    retry_count: int
    execution_error: str
    sql_generation_error: str
    disable_sql_blocking: bool
    query_type: str
    database_name: str
    previous_sql_queries: List[str]
```

### Workflow Nodes
The system implements the following nodes in the LangGraph workflow:

1. **get_schema_node** - Retrieves database schema from all available databases
2. **generate_sql_node** - Generates SQL query based on user request and schema
3. **validate_sql_node** - Validates SQL query safety using multiple methods
4. **execute_sql_node** - Executes SQL query on appropriate databases
5. **refine_sql_node** - Refines SQL query based on execution results or errors
6. **security_check_after_refinement_node** - Performs security check on refined queries
7. **generate_wider_search_query_node** - Generates alternative queries when initial results are empty
8. **execute_wider_search_node** - Executes wider search queries
9. **generate_prompt_node** - Creates specialized prompt for response generation
10. **generate_response_node** - Generates natural language response

### Conditional Logic
The system uses several conditional functions to determine workflow paths:
- `should_validate_sql` - Routes to refinement if validation fails
- `should_retry` - Determines if another attempt should be made
- `should_refine_or_respond` - Decides between refining SQL or generating response
- `should_validate_after_security_check` - Routes after security validation
- `should_execute_wider_search` - Triggers wider search when initial query returns no results

### SQL Generation and Refinement
- The SQL Generator receives the history of ALL previously generated SQL queries to ensure continuity and prevent repetition of failed approaches
- When queries fail validation or execution, the system refines them based on error feedback
- The system considers previous errors when generating new queries
- Each generated query is added to the history for future reference

### Wider Search Implementation
- When initial queries return no results, the system automatically engages wider search strategies
- The wider search generator analyzes the schema and suggests alternative approaches
- Multiple attempts are made with different strategies until results are found or maximum attempts reached
- The system maintains the history of all attempts to avoid repeating unsuccessful approaches

### Security Validation
- Two-tier validation system: basic keyword matching and advanced LLM-based analysis
- Checks for potentially harmful SQL commands (DROP, DELETE, INSERT, UPDATE, etc.)
- Validates against dangerous patterns that might indicate SQL injection
- Ensures queries start with SELECT or WITH for safety
- Configurable security settings via environment variables

### Retry Mechanism
- Configurable retry limits (default: 10 attempts)
- Different retry logic for different types of errors
- Automatic increment of retry counter to prevent infinite loops
- Distinction between initial queries and wider search attempts

## Integration Notes
When using this system:
1. The system automatically manages the history of all generated SQL queries
2. Multi-database support is handled transparently through table-to-database mappings
3. Security validation occurs at multiple points in the workflow
4. Error handling and recovery are built into the workflow
5. The wider search functionality activates automatically when needed

## Backup Files
Original versions of the prompt files are saved with `.original` extension for reference.
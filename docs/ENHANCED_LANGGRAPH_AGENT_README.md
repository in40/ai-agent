# Enhanced LangGraph AI Agent

This project implements an enhanced AI agent using LangGraph for complex database query processing with natural language interface.

## Features

- **Natural Language to SQL Conversion**: Convert user requests into SQL queries
- **Advanced Validation**: Comprehensive safety checks on generated SQL with optional LLM-based analysis
- **Error Recovery**: Automatic retry and refinement mechanisms
- **State Management**: Persistent state across multiple processing steps
- **Monitoring**: Detailed logging and execution tracking
- **Safety**: Multiple layers of protection against harmful SQL
- **Configurable SQL Blocking**: Option to disable SQL blocking for trusted environments
- **Advanced Security LLM Analysis**: Uses an LLM to reduce false positives in security detection (e.g., distinguishing 'created_at' column from CREATE command)
- **Multi-Provider LLM Support**: Supports various LLM providers including OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, and Ollama
- **Wider Search Strategies**: Automatically tries alternative search strategies when initial queries return no results
- **Specialized Prompt Generation**: Creates tailored prompts for response LLM based on user request and database results
- **Query Type Tracking**: Tracks whether queries are initial or wider search queries for better processing
- **Recursion Limits**: Implements recursion limits to prevent infinite loops during processing
- **Previous SQL Query History**: Maintains a history of all previously generated SQL queries to prevent repetition of failed approaches and provide context for subsequent query generations
- **Database Alias to Real Name Mapping**: Maps database aliases used internally to real database names for LLMs, ensuring accurate query generation
- **MCP (Model Context Protocol) Integration**:
  - Discover and interact with MCP services via registry
  - Generate and execute tool calls to MCP services
  - Dedicated MCP model for optimized MCP-related queries
  - Separate configuration for MCP-specific tasks
  - MCP service result integration with database query results
  - Ability to return MCP results directly to LLM for processing
- **MCP Search Server**: MCP-compliant service for web search queries via Brave Search API, allowing LLM models to perform web searches for current information
- **Configurable Component Disabling**: Option to disable database operations, prompt generation, or response generation for performance optimization

## Architecture

The agent follows a graph-based workflow with the following nodes:

1. **get_schema**: Retrieves database schema information from all available databases
2. **discover_services**: Discovers MCP services from the registry
3. **query_mcp_services**: Queries MCP services for information before attempting SQL database queries
4. **generate_sql**: Creates SQL queries from natural language requests
5. **validate_sql**: Performs safety and validation checks (with optional advanced LLM-based analysis)
6. **execute_sql**: Executes the SQL query against all databases
7. **refine_sql**: Improves queries based on errors or feedback
8. **security_check_after_refinement**: Performs security check on refined SQL query
9. **generate_wider_search_query**: Generates alternative queries when initial query returns no results
10. **execute_wider_search**: Executes the wider search query
11. **generate_prompt**: Creates specialized prompts for response generation
12. **generate_response**: Creates natural language responses from results
13. **execute_mcp_tool_calls_and_return**: Executes MCP tool calls and returns results when both prompt and response generation are disabled
14. **return_mcp_response_to_llm**: Returns MCP responses directly to the LLM model when initiated by the LLM
15. **await_mcp_response**: Awaits MCP response from the LLM model that was called with the MCP results

## Usage

### Basic Usage

```python
from langgraph_agent import run_enhanced_agent

# Process a natural language request
result = run_enhanced_agent("Show me all users from the database")

print("Generated SQL:", result["generated_sql"])
print("Results:", result["db_results"])
print("Response:", result["final_response"])
print("Execution log:", result["execution_log"])
print("Query type:", result["query_type"])  # Either "initial" or "wider_search"
```

### Advanced Usage

```python
from langgraph_agent import create_enhanced_agent_graph, AgentState

# Create the graph
graph = create_enhanced_agent_graph()

# Define initial state
initial_state: AgentState = {
    "user_request": "Get all users from the database",
    "schema_dump": {},
    "sql_query": "",
    "db_results": [],
    "response_prompt": "",  # Specialized prompt for response generation
    "final_response": "",
    "messages": [],
    "validation_error": None,
    "execution_error": None,
    "sql_generation_error": None,
    "retry_count": 0,
    "disable_sql_blocking": False,
    "query_type": "initial"  # Either "initial" or "wider_search"
}

# Run the graph
result = graph.invoke(initial_state)
```

## Configuration

The agent uses the same configuration as the original AI agent, with components for:
- Database connections
- SQL generation (using LLMs)
- Response generation (using LLMs)
- Prompt management
- Security analysis (using LLMs)

See the main project README for configuration details.

## Testing

Run the comprehensive test suite:

```bash
python test_enhanced_langgraph_agent.py
```

## Components

### AgentState

The state structure contains:
- `user_request`: The original natural language request
- `schema_dump`: Database schema information
- `sql_query`: The generated SQL query
- `db_results`: Results from the database query
- `all_db_results`: Results grouped by database name
- `table_to_db_mapping`: Mapping from original table names to database names
- `table_to_real_db_mapping`: Mapping from original table names to real database names
- `response_prompt`: Specialized prompt for response generation
- `final_response`: Natural language response to the user
- `messages`: List of messages for the LLM
- `validation_error`: Any validation errors
- `execution_error`: Any execution errors
- `sql_generation_error`: Any SQL generation errors
- `retry_count`: Number of retry attempts
- `disable_sql_blocking`: Whether to disable SQL blocking
- `disable_databases`: Flag to disable all database operations
- `query_type`: Type of query ("initial" or "wider_search")
- `database_name`: Name of the database to use for queries
- `previous_sql_queries`: History of all previously generated SQL queries to prevent repetition of failed approaches
- `registry_url`: URL of the MCP service registry
- `discovered_services`: List of discovered MCP services
- `mcp_service_results`: Results from MCP service queries
- `use_mcp_results`: Flag to indicate if MCP results should be prioritized
- `mcp_tool_calls`: Tool calls generated by the MCP-capable model
- `mcp_capable_response`: Response from the MCP-capable model when models are disabled
- `return_mcp_results_to_llm`: Flag to indicate if MCP results should be returned to LLM for further processing

### Conditional Logic

The system implements several conditional functions to route execution:

- **should_skip_database_operations**: Determines if database operations should be skipped based on the `disable_databases` flag
- **should_generate_sql_after_mcp_query**: Routes to appropriate nodes based on MCP service results and database availability
- **route_after_validation**: Routes to appropriate execution node based on query type and validation results
- **should_execute_wider_search**: Determines if wider search should be performed when initial query returns no results
- **should_refine_or_respond**: Determines if SQL should be refined or response generated based on errors and retry count
- **should_validate_after_security_check**: Determines if validation should occur after security check or proceed to response
- **should_continue_wider_search**: Determines next step after executing wider search based on results and errors
- **should_skip_prompt_and_response_generation**: Skips prompt/response generation when both are disabled
- **route_after_mcp_execution**: Routes MCP results to user or back to LLM for processing

### Error Handling

The system handles four types of errors:
1. **Validation errors**: Issues with SQL safety
2. **Execution errors**: Problems executing the query
3. **Generation errors**: Issues generating SQL or responses
4. **Security check errors**: Issues with advanced security analysis

Each error type triggers appropriate recovery mechanisms.

## Monitoring

Detailed logs are available for each node execution:
- `[NODE START]` - When a node begins processing
- `[NODE SUCCESS]` - When a node completes successfully
- `[NODE ERROR]` - When a node encounters an error
- `[NODE WARNING]` - When a node generates a warning
- `[GRAPH START]` - When the graph begins execution
- `[GRAPH END]` - When the graph completes execution

## Safety Features

1. **SQL Validation**: Checks for harmful commands and patterns
2. **SELECT-Only Policy**: Ensures queries start with SELECT
3. **Pattern Detection**: Identifies potential SQL injection attempts
4. **Statement Limiting**: Restricts to single statements
5. **Comment Filtering**: Blocks SQL comments that could be used maliciously
6. **Advanced Security LLM Analysis**: Uses an LLM to reduce false positives in security detection (e.g., distinguishing 'created_at' column from CREATE command)
7. **Configurable SQL Blocking**: Option to disable SQL blocking for trusted environments
8. **Context-Aware Analysis**: Security LLM considers database schema context to better distinguish between legitimate column names and harmful commands
9. **Security Check After Refinement**: Validates refined queries for security issues
10. **Retry Limits**: Prevents infinite loops during error recovery

## Wider Search Strategies

When initial queries return no results, the system automatically employs wider search strategies:

1. **Generate Wider Search Query**: Creates alternative queries based on schema and original request
2. **Execute Wider Search**: Runs the alternative query against the database
3. **Iterative Refinement**: If wider search also yields no results, continues with additional strategies
4. **Fallback Analysis**: Performs additional analysis on schema to find relevant data

## Specialized Prompt Generation

The system includes a specialized prompt generation step that:
- Creates tailored prompts for the response LLM based on user request and database results
- Formats database results in a way that's optimal for natural language generation
- Incorporates context from the original request to ensure relevance
- Helps the response LLM generate more accurate and contextual responses

## Performance Considerations

- Each node is timed for performance analysis
- Retry limits prevent infinite loops
- Recursion limits prevent infinite processing loops during graph execution
- Schema caching reduces database load
- Error handling prevents cascading failures
- Wider search strategies are limited to prevent excessive database queries
- Previous SQL query history prevents repetition of failed approaches

## Workflow

The agent follows this workflow:

1. User submits a natural language request
2. The `get_schema` node retrieves database schema information from all available databases
3. The `discover_services` node discovers MCP services from the registry
4. The `query_mcp_services` node queries MCP services for information before attempting SQL database queries
5. Based on MCP results and database availability, the system routes to appropriate nodes:
   - If databases are disabled and MCP tool calls exist → `execute_mcp_tool_calls_and_return`
   - If databases are disabled and MCP results are sufficient → `generate_prompt`
   - If databases are enabled and MCP results should go to LLM → `return_mcp_response_to_llm`
   - Otherwise → `generate_sql`
6. The `generate_sql` node creates a SQL query from the request and schema
7. The `validate_sql` node performs safety checks (with optional advanced LLM-based analysis)
8. Based on validation results and query type, the system routes to:
   - If validation failed → `refine_sql`
   - If query type is 'wider_search' → `execute_wider_search`
   - Otherwise → `execute_sql`
9. The `execute_sql` node executes the query against all databases
10. If initial query returns no results or has execution errors, the system may route to:
   - `generate_wider_search_query` and `execute_wider_search` for alternative strategies
   - Otherwise → `generate_prompt`
11. If validation or execution fails, the `refine_sql` node improves the query
12. The `security_check_after_refinement` node validates refined queries for security issues
13. Based on security check results, the system routes to:
   - If security check failed → `validate_sql` (for further refinement)
   - Otherwise → `execute_sql` (to execute the secured refined query)
14. The `generate_prompt` node creates a specialized prompt for response generation
15. If both prompt and response generation are disabled, the system routes to `execute_mcp_tool_calls_and_return`
16. Otherwise, the `generate_response` node creates a natural language response from results
17. If MCP results need to be returned to LLM, the system goes through `return_mcp_response_to_llm` and `await_mcp_response`
18. The final response is returned to the user

## Troubleshooting

If you encounter issues:

1. Check the logs for detailed error information
2. Verify database connectivity
3. Ensure LLM configurations are correct
4. Review the execution log for the sequence of operations
5. Check that the database schema is accessible
6. If using wider search strategies, verify that schema information is complete
7. For security analysis issues, ensure the security LLM is properly configured

## Contributing

Contributions are welcome! Please submit pull requests with:
- Comprehensive tests
- Updated documentation
- Clear explanations of changes
- Adherence to existing code style
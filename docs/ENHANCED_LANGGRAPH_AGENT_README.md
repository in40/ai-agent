# Enhanced LangGraph AI Agent with MCP Architecture

This project implements an enhanced AI agent using LangGraph with a primary focus on Model Context Protocol (MCP) services, with optional database query processing capabilities.

## Features

- **MCP-First Architecture**: Primary interaction through Model Context Protocol services with optional database integration
- **Service Discovery**: Automatic discovery and interaction with MCP services via registry
- **Flexible Tool Integration**: Support for various types of services (RAG, Search, SQL, DNS, etc.)
- **Dynamic Tool Calling**: Generates and executes appropriate tool calls based on user requests
- **Error Recovery**: Automatic retry and refinement mechanisms
- **State Management**: Persistent state across multiple processing steps
- **Monitoring**: Detailed logging and execution tracking
- **Safety**: Multiple layers of protection for SQL queries when enabled
- **Configurable SQL Blocking**: Option to disable SQL blocking for trusted environments
- **Advanced Security LLM Analysis**: Uses an LLM to reduce false positives in security detection (e.g., distinguishing 'created_at' column from CREATE command)
- **Multi-Provider LLM Support**: Supports various LLM providers including OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, and Ollama
- **Wider Search Strategies**: Automatically tries alternative search strategies when initial queries return no results
- **Specialized Prompt Generation**: Creates tailored prompts for response LLM based on user request and service results
- **Query Type Tracking**: Tracks whether queries are initial or wider search queries for better processing
- **Recursion Limits**: Implements recursion limits to prevent infinite loops during processing
- **Previous Query History**: Maintains a history of all previously generated queries to prevent repetition of failed approaches and provide context for subsequent query generations
- **MCP (Model Context Protocol) Integration**:
  - Discover and interact with MCP services via registry
  - Generate and execute tool calls to MCP services
  - Dedicated MCP model for optimized MCP-related queries
  - Separate configuration for MCP-specific tasks
  - MCP service result integration with database query results when both are enabled
  - Ability to return MCP results directly to LLM for processing
- **MCP Services Ecosystem**:
  - RAG Service: Provides document retrieval and ingestion capabilities
  - Search Service: Enables web search functionality via Brave Search API
  - SQL Service: Handles database query generation and execution (when enabled)
  - DNS Service: Resolves hostnames to IP addresses
  - Extensible architecture for adding new MCP services
- **Configurable Component Disabling**: Option to disable database operations, prompt generation, or response generation for performance optimization

## Architecture

The agent follows a graph-based workflow with the following nodes:

1. **get_schema**: Retrieves database schema information from all available databases (when databases are enabled)
2. **discover_services**: Discovers MCP services from the registry
3. **query_mcp_services**: Queries MCP services for information before attempting database queries
4. **generate_sql**: Creates SQL queries from natural language requests (when databases are enabled)
5. **validate_sql**: Performs safety and validation checks (with optional advanced LLM-based analysis)
6. **execute_sql**: Executes the SQL query against all databases (when databases are enabled)
7. **refine_sql**: Improves queries based on errors or feedback
8. **security_check_after_refinement**: Performs security check on refined SQL query
9. **generate_wider_search_query**: Generates alternative queries when initial query returns no results
10. **execute_wider_search**: Executes the wider search query (when databases are enabled)
11. **generate_prompt**: Creates specialized prompts for response generation
12. **generate_response**: Creates natural language responses from results
13. **execute_mcp_tool_calls_and_return**: Executes MCP tool calls and returns results when both prompt and response generation are disabled
14. **return_mcp_response_to_llm**: Returns MCP responses directly to the LLM model when initiated by the LLM
15. **await_mcp_response**: Awaits MCP response from the LLM model that was called with the MCP results

### Conditional Logic:
- **should_skip_database_operations**: Determines if database operations should be skipped based on the `disable_databases` flag
- **should_generate_sql_after_mcp_query**: Routes to appropriate nodes based on MCP service results and database availability
- **route_after_validation**: Routes to appropriate execution node based on query type and validation results
- **should_execute_wider_search**: Determines if wider search should be performed when initial query returns no results
- **should_refine_or_respond**: Determines if SQL should be refined or response generated based on errors and retry count
- **should_validate_after_security_check**: Determines if validation should occur after security check or proceed to response
- **should_continue_wider_search**: Determines next step after executing wider search based on results and errors
- **should_skip_prompt_and_response_generation**: Skips prompt/response generation when both are disabled
- **route_after_mcp_execution**: Routes MCP results to user or back to LLM for processing

## Detailed Node Descriptions

### get_schema Node
Retrieves database schema information from all available databases when database operations are enabled. This information is used by subsequent nodes to generate appropriate SQL queries.

### discover_services Node
Discovers available MCP services from the registry server. This information is used to determine what services are available for handling the user request.

### query_mcp_services Node
Queries MCP services for information before attempting database queries. This node uses a dedicated MCP model to generate appropriate tool calls based on the user request and discovered services.

### generate_sql Node
Creates SQL queries from natural language requests using the database schema information. This node is only active when database operations are enabled.

### validate_sql Node
Performs safety and validation checks on generated SQL queries. Includes optional advanced LLM-based analysis to reduce false positives.

### execute_sql Node
Executes the SQL query against all available databases. This node is only active when database operations are enabled.

### refine_sql Node
Improves SQL queries based on errors or feedback from previous attempts. This node helps recover from query generation errors.

### security_check_after_refinement Node
Performs security validation on refined SQL queries to ensure they are safe to execute.

### generate_wider_search_query Node
Generates alternative queries when initial queries return no results. This helps find relevant information when the initial approach fails.

### execute_wider_search Node
Executes wider search queries against databases. This node is only active when database operations are enabled.

### generate_prompt Node
Creates specialized prompts for the response generation LLM based on user request and service results.

### generate_response Node
Creates natural language responses from the collected results and information.

### execute_mcp_tool_calls_and_return Node
Executes MCP tool calls and returns results directly when both prompt and response generation are disabled.

### return_mcp_response_to_llm Node
Returns MCP service results directly to the LLM model when initiated by the LLM.

### await_mcp_response Node
Awaits MCP response from the LLM model that was called with the MCP results.

## Workflow

The agent follows this workflow:

1. User submits a natural language request
2. The `discover_services` node discovers MCP services from the registry
3. The `query_mcp_services` node queries MCP services for information before attempting database queries (if enabled)
4. If databases are enabled, the `get_schema` node retrieves database schema information from all available databases
5. Based on MCP results and database availability, the system routes to appropriate nodes:
   - If databases are disabled and MCP tool calls exist → `execute_mcp_tool_calls_and_return`
   - If databases are disabled and MCP results are sufficient → `generate_prompt`
   - If databases are enabled and MCP results should go to LLM → `return_mcp_response_to_llm`
   - If databases are enabled and MCP results are not sufficient → `generate_sql`
   - Otherwise → `generate_prompt` (when only MCP results are available)
6. The `generate_sql` node creates a SQL query from the request and schema (when databases are enabled)
7. The `validate_sql` node performs safety checks (with optional advanced LLM-based analysis)
8. Based on validation results and query type, the system routes to:
   - If validation failed → `refine_sql`
   - If query type is 'wider_search' → `execute_wider_search`
   - Otherwise → `execute_sql`
9. The `execute_sql` node executes the query against all databases (when databases are enabled)
10. If initial query returns no results or has execution errors, the system may route to:
    - `generate_wider_search_query` and `execute_wider_search` for alternative strategies
    - Otherwise → `generate_prompt`
11. If validation or execution fails, the `refine_sql` node improves the query
12. The `security_check_after_refinement` node validates refined queries for security issues
13. Based on security check results, the system routes to:
    - If security check failed → `validate_sql` (for further refinement)
    - Otherwise → `execute_sql` (to execute the secured refined query)
14. The `generate_prompt` node creates a specialized prompt for response generation, incorporating both MCP service results and database results (when both are available)
15. If both prompt and response generation are disabled, the system routes to `execute_mcp_tool_calls_and_return`
16. Otherwise, the `generate_response` node creates a natural language response from results
17. If MCP results need to be returned to LLM, the system goes through `return_mcp_response_to_llm` and `await_mcp_response`
18. The final response is returned to the user

## Troubleshooting

If you encounter issues:

1. Check the logs for detailed error information
2. Verify database connectivity (if using database features)
3. Ensure LLM configurations are correct
4. Review the execution log for the sequence of operations
5. Check that the database schema is accessible (if using database features)
6. If using wider search strategies, verify that schema information is complete
7. For security analysis issues, ensure the security LLM is properly configured
8. For MCP integration issues, verify registry URL and service availability
9. If experiencing recursion limit errors, simplify your request or check for complex query patterns

## Contributing

Contributions are welcome! Please submit pull requests with:
- Comprehensive tests
- Updated documentation
- Clear explanations of changes
- Adherence to existing code style
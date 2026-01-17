# AI Agent for Natural Language to SQL Queries

This AI agent processes natural language requests from users, converts them to SQL queries, executes them against a database, and returns natural language responses. The system is built with an enhanced LangGraph-based architecture for complex workflows with sophisticated error handling and recovery mechanisms.

## Architecture

The AI agent consists of 5 main components:

1. **Database Manager**: Handles connections to databases (PostgreSQL, MySQL, etc.) and retrieves schema information
2. **SQL Generator**: Uses an LLM to convert natural language requests to SQL queries
3. **SQL Executor**: Safely executes SQL queries against the database with security validation
4. **Prompt Generator**: Creates detailed prompts for the response LLM based on query results
5. **Response Generator**: Uses an LLM to create natural language responses

## Enhanced LangGraph Architecture

The enhanced version of the agent uses LangGraph to provide:
- Stateful workflow management with comprehensive state tracking
- Conditional logic for validation and error handling
- Iterative refinement of SQL queries with security validation after refinement
- Advanced error recovery mechanisms with configurable retry limits
- Detailed execution monitoring and logging
- Wider search strategies when initial queries return no results
- Multi-provider LLM support (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)
- Multi-database support with schema aggregation
- MCP (Model Context Protocol) integration for external service interaction

### LangGraph Nodes:
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

## Key Features

### Multi-Database Support
- Connect to multiple databases simultaneously
- Aggregate schema information from all databases
- Execute queries across all databases and combine results
- Map original table names to their respective databases
- Cross-database query execution support

### Advanced Security Analysis
- Basic keyword matching for harmful SQL commands
- Advanced LLM-based security analysis to reduce false positives
- Context-aware analysis that considers database schema
- Configurable security policies via environment variables
- Support for both basic keyword matching and advanced LLM-based analysis
- Security validation after query refinement

### Wider Search Strategies
- Automatic fallback to wider search when initial queries return no results
- Generation of alternative queries based on schema and original request
- Iterative refinement of wider search strategies
- Prevention of infinite loops during wider search with configurable limits

### Enhanced Error Handling
- Automatic retry mechanisms when SQL generation fails (up to 10 attempts)
- Graceful degradation when database queries fail
- Feedback loops to improve query generation
- Prevention of infinite loops during refinement
- Comprehensive error tracking across all node executions

### Database Alias to Real Name Mapping
- Maps database aliases used internally to real database names for LLMs
- Ensures LLMs receive accurate database names for better query generation
- Automatically extracts real names from database URLs
- Supports manual mapping via environment variables
- Maintains backward compatibility with existing configurations

### Previous SQL Query History
- Maintains a history of all previously generated SQL queries
- Prevents repetition of failed approaches
- Provides context for subsequent query generations
- Improves convergence on successful queries

### MCP (Model Context Protocol) Integration
- Discover and interact with MCP services via registry
- Generate and execute tool calls to MCP services
- Dedicated MCP model for optimized MCP-related queries
- Separate configuration for MCP-specific tasks
- Fallback to original MCP model if dedicated model unavailable
- MCP service result integration with database query results
- Ability to return MCP results directly to LLM for processing

### MCP Search Server
- MCP-compliant service for web search queries via Brave Search API
- Allows LLM models to perform web searches for current information
- Follows the same architecture patterns as other MCP services
- Provides clean API for search queries with standardized response format

### Default Model Configuration
- Simplified configuration when using the same model for all tasks
- Reduces the number of environment variables to manage
- Provides a fallback when specific configurations are not set
- Supports disabling specific model components to optimize performance

### Configurable Component Disabling
- Option to disable database operations entirely
- Option to disable prompt generation for performance optimization
- Option to disable response generation for performance optimization
- Option to disable SQL blocking for trusted environments

## Workflow

### Enhanced LangGraph Architecture:
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

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure the application:
   You can either use the interactive configuration script or manually set up your environment:

   Using the configuration script:
   ```bash
   python setup_config.py
   ```

   Or manually set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database URL and API keys
   ```

3. For multi-database support, configure additional databases using environment variables:
   ```
   DB_{NAME}_TYPE=postgresql
   DB_{NAME}_USERNAME=username
   DB_{NAME}_PASSWORD=password
   DB_{NAME}_HOSTNAME=localhost
   DB_{NAME}_PORT=5432
   DB_{NAME}_NAME=database_name
   ```

   Or use direct URL:
   ```
   DB_{NAME}_URL=postgresql://username:password@hostname:port/database_name
   ```

4. Run the AI agent:
   ```bash
   python main.py
   ```

## Usage

You can run the AI agent in interactive mode or pass a request directly:

```bash
# Interactive mode
python main.py

# Direct request
python main.py --request "Show me all users from New York"
```

## Configuration

The agent can be configured via environment variables in the `.env` file:

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string for default database
- `DB_{NAME}_URL`: Connection string for additional databases (e.g., `DB_ANALYTICS_URL`)
- `DB_{NAME}_TYPE`: Database type (postgresql, mysql, sqlite, etc.)
- `DB_{NAME}_USERNAME`: Database username
- `DB_{NAME}_PASSWORD`: Database password
- `DB_{NAME}_HOSTNAME`: Database hostname
- `DB_{NAME}_PORT`: Database port
- `DB_{NAME}_NAME`: Database name
- `DISABLE_DATABASES`: Flag to disable all database operations (default: false)
- `DEFAULT_DATABASE_ENABLED`: Flag to specifically enable/disable the default database (default: true)

### LLM Configuration
- `SQL_LLM_MODEL`: Model to use for SQL generation (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `RESPONSE_LLM_MODEL`: Model to use for response generation (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `PROMPT_LLM_MODEL`: Model to use for prompt generation (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `SECURITY_LLM_MODEL`: Model to use for security analysis (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `SQL_LLM_PROVIDER`: Provider for SQL generation (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama, default)
- `RESPONSE_LLM_PROVIDER`: Provider for response generation
- `PROMPT_LLM_PROVIDER`: Provider for prompt generation
- `SECURITY_LLM_PROVIDER`: Provider for security analysis
- `SQL_LLM_HOSTNAME`: Hostname for SQL LLM service (for non-OpenAI providers)
- `SQL_LLM_PORT`: Port for SQL LLM service (for non-OpenAI providers)
- `SQL_LLM_API_PATH`: API path for SQL LLM service (for non-OpenAI providers)
- `RESPONSE_LLM_HOSTNAME`: Hostname for response LLM service (for non-OpenAI providers)
- `RESPONSE_LLM_PORT`: Port for response LLM service (for non-OpenAI providers)
- `RESPONSE_LLM_API_PATH`: API path for response LLM service (for non-OpenAI providers)
- `PROMPT_LLM_HOSTNAME`: Hostname for prompt LLM service (for non-OpenAI providers)
- `PROMPT_LLM_PORT`: Port for prompt LLM service (for non-OpenAI providers)
- `PROMPT_LLM_API_PATH`: API path for prompt LLM service (for non-OpenAI providers)
- `SECURITY_LLM_HOSTNAME`: Hostname for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_PORT`: Port for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_API_PATH`: API path for security LLM service (for non-OpenAI providers)

### Default Model Configuration
- `DEFAULT_LLM_PROVIDER`: Provider to use when specific configurations are not provided (e.g., 'LM Studio', 'OpenAI', 'Ollama', 'default')
- `DEFAULT_LLM_MODEL`: Model name to use as default
- `DEFAULT_LLM_HOSTNAME`: Hostname of the default LLM service
- `DEFAULT_LLM_PORT`: Port of the default LLM service
- `DEFAULT_LLM_API_PATH`: API path for the default LLM service

### API Keys
- `OPENAI_API_KEY`: API key for OpenAI services
- `GIGACHAT_CREDENTIALS`: Your GigaChat authorization credentials
- `GIGACHAT_SCOPE`: The scope for your GigaChat API access (default: GIGACHAT_API_PERS)

### Security Configuration
- `SECURITY_LLM_MODEL`: Model to use for security analysis (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `USE_SECURITY_LLM`: Whether to use the advanced security LLM analysis (default: true)
- `TERMINATE_ON_POTENTIALLY_HARMFUL_SQL`: Whether to block potentially harmful SQL (default: true)

### Logging Configuration
- `ENABLE_SCREEN_LOGGING`: Enable detailed logging output (default: false)

### Model Component Disabling
- `DISABLE_PROMPT_GENERATION`: Skip the prompt generation LLM to optimize performance
- `DISABLE_RESPONSE_GENERATION`: Skip the response generation LLM to optimize performance

### MCP Configuration
- `MCP_LLM_PROVIDER`: Provider for MCP service queries (default: LM Studio)
- `MCP_LLM_MODEL`: Model for MCP service queries (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `MCP_LLM_HOSTNAME`: Hostname for MCP LLM service (default: localhost)
- `MCP_LLM_PORT`: Port for MCP LLM service (default: 1234)
- `MCP_LLM_API_PATH`: API path for MCP LLM service (default: /v1)
- `REGISTRY_URL`: URL of the MCP registry server (can be passed via command line as well)

### Dedicated MCP Model Configuration
- `DEDICATED_MCP_LLM_PROVIDER`: Provider for dedicated MCP-related queries (default: LM Studio)
- `DEDICATED_MCP_LLM_MODEL`: Model for dedicated MCP-related queries (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `DEDICATED_MCP_LLM_HOSTNAME`: Hostname for dedicated MCP LLM service (default: localhost)
- `DEDICATED_MCP_LLM_PORT`: Port for dedicated MCP LLM service (default: 1234)
- `DEDICATED_MCP_LLM_API_PATH`: API path for dedicated MCP LLM service (default: /v1)

## Security

- SQL queries are validated to prevent harmful commands (no DROP, DELETE, INSERT, UPDATE, etc.)
- Only SELECT and WITH queries are allowed by default
- Connection parameters are loaded from environment variables
- Advanced security LLM analysis to reduce false positives
- Multiple layers of protection against SQL injection
- Configurable security policies via environment variables
- Security check after refinement to ensure refined queries are safe
- Protection against SQL injection through pattern detection and comment filtering

### Advanced Security LLM Analysis

The agent now includes an advanced security analysis feature that uses an LLM to detect potentially harmful SQL queries while reducing false positives. This addresses issues where legitimate column names like `created_at` were incorrectly flagged as harmful due to containing substrings like "create".

The security LLM analysis:
- Distinguishes between legitimate column/table names and actual malicious commands
- Reduces false positives compared to simple keyword matching
- Provides contextual analysis based on the database schema
- Offers confidence levels for security assessments
- Supports multiple LLM providers for security analysis (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)

By default, the security LLM is enabled. You can disable it by setting `USE_SECURITY_LLM=false`.

### Disabling SQL Blocking

To disable the SQL blocking feature, you can:

1. Pass `disable_sql_blocking=True` when calling `run_enhanced_agent()`:
   ```python
   result = run_enhanced_agent("Your request", disable_sql_blocking=True)
   ```

2. Set the environment variable `USE_SECURITY_LLM=false`:
   ```bash
   export USE_SECURITY_LLM=false
   ```

**Warning:** Disabling SQL blocking can pose security risks and should only be done in trusted environments.

## GigaChat Integration

The project now supports GigaChat models with OAuth token-based authentication:

### GigaChat Specific Variables
- `GIGACHAT_CREDENTIALS`: Your GigaChat authorization credentials
- `GIGACHAT_SCOPE`: The scope for your API access (default: `GIGACHAT_API_PERS`)
  - `GIGACHAT_API_PERS` - Personal API access
  - `GIGACHAT_API_B2B` - Business-to-business API access
  - `GIGACHAT_API_CORP` - Corporate API access
- `GIGACHAT_ACCESS_TOKEN`: Pre-generated access token (optional, if using credentials instead)
- `GIGACHAT_VERIFY_SSL_CERTS`: Whether to verify SSL certificates (default: `true`). Set to `false` to disable SSL verification for self-signed certificates.

### Model Provider Configuration
Set the provider to `GigaChat` for any of the model components:
- `SQL_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for SQL generation
- `RESPONSE_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for response generation
- `PROMPT_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for prompt generation
- `SECURITY_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for security analysis

## Schema Export with Comments

The system now supports exporting database schema comments (for tables, columns, etc.) to help LLM models better understand the context of the database structure. This improves the accuracy and relevance of SQL queries generated by the AI agent.

### PostgreSQL Implementation
- Uses `pg_catalog.pg_description` to retrieve table and column comments
- Joins with `pg_catalog.pg_statio_all_tables` to link comments to tables and columns
- Table comments are retrieved separately from column comments
- Column comments are retrieved alongside column metadata

### SQLite Implementation
- Extracts column comments from CREATE TABLE statements using regex patterns
- Attempts to extract table comments from the end of CREATE TABLE statements (though SQLite typically strips these)
- Since SQLite doesn't have native comment support, this implementation extracts comments from the original DDL if they exist

## Monitoring and Observability

Detailed logs are available for each node execution:
- `[NODE START]` - When a node begins processing
- `[NODE SUCCESS]` - When a node completes successfully
- `[NODE ERROR]` - When a node encounters an error
- `[NODE WARNING]` - When a node generates a warning
- `[GRAPH START]` - When the graph begins execution
- `[GRAPH END]` - When the graph completes execution
- `[TIME]` - Execution time measurements for performance analysis

## Performance Considerations

- Each node is timed for performance analysis
- Retry limits prevent infinite loops (maximum 10 attempts)
- Schema caching reduces database load
- Error handling prevents cascading failures
- Wider search strategies are limited to prevent excessive database queries
- Multi-database schema aggregation is cached for efficiency
- Configurable component disabling for performance optimization

## Troubleshooting

If you encounter issues:

1. Check the logs for detailed error information
2. Verify database connectivity
3. Ensure LLM configurations are correct
4. Review the execution log for the sequence of operations
5. Check that the database schema is accessible
6. If using wider search strategies, verify that schema information is complete
7. For security analysis issues, ensure the security LLM is properly configured
8. For multi-database issues, verify that all database configurations are correct
9. For MCP integration issues, verify registry URL and service availability
10. If experiencing recursion limit errors, simplify your request or check for complex query patterns
# AI Agent for Natural Language to SQL Queries

This AI agent processes natural language requests from users, converts them to SQL queries, executes them against a database, and returns natural language responses. The system is built with both a traditional linear architecture and an enhanced LangGraph-based architecture for complex workflows.

## Architecture

The AI agent consists of 5 main components:

1. **Database Manager**: Handles connections to databases (PostgreSQL, MySQL, etc.) and retrieves schema information
2. **SQL Generator**: Uses an LLM to convert natural language requests to SQL queries
3. **SQL Executor**: Safely executes SQL queries against the database with security validation
4. **Prompt Generator**: Creates detailed prompts for the response LLM based on query results
5. **Response Generator**: Uses an LLM to create natural language responses

## Enhanced LangGraph Architecture

The enhanced version of the agent uses LangGraph to provide:
- Stateful workflow management
- Conditional logic for validation and error handling
- Iterative refinement of SQL queries
- Advanced error recovery mechanisms
- Detailed execution monitoring and logging

### LangGraph Nodes:
1. **get_schema**: Retrieves database schema information
2. **generate_sql**: Creates SQL queries from natural language requests
3. **validate_sql**: Performs safety and validation checks (with optional advanced LLM-based analysis)
4. **execute_sql**: Executes the SQL query against the database
5. **refine_sql**: Improves queries based on errors or feedback
6. **generate_response**: Creates natural language responses from results

## Workflow

### Traditional Architecture:
1. User submits a natural language request
2. The agent retrieves the database schema
3. The first LLM generates a SQL query based on the request and schema
4. The SQL query is validated for safety
5. The SQL query is executed against the database
6. The second LLM creates a detailed prompt for the response LLM
7. The third LLM generates a natural language response based on the database results
8. The response is returned to the user

### Enhanced LangGraph Architecture:
1. User submits a natural language request
2. The `get_schema` node retrieves database schema information
3. The `generate_sql` node creates a SQL query from the request and schema
4. The `validate_sql` node performs safety checks (with optional advanced LLM-based analysis)
5. If validation passes, the `execute_sql` node executes the query
6. If validation or execution fails, the `refine_sql` node improves the query
7. The `generate_response` node creates a natural language response from results
8. The response is returned to the user

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

3. Run the AI agent:
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

## Security

- SQL queries are validated to prevent harmful commands (no DROP, DELETE, INSERT, etc.)
- Only SELECT queries are allowed by default
- Connection parameters are loaded from environment variables
- Advanced security LLM analysis to reduce false positives

## SQL Blocking Feature

By default, the agent includes SQL validation to block potentially harmful SQL queries. This includes:
- Blocking commands like DROP, DELETE, INSERT, UPDATE, TRUNCATE, ALTER, EXEC, EXECUTE (CREATE is allowed in certain contexts like views)
- Requiring queries to start with SELECT for safety
- Blocking dangerous patterns that might indicate SQL injection
- Preventing multiple statements and SQL comments

### Advanced Security LLM Analysis

The agent now includes an advanced security analysis feature that uses an LLM to detect potentially harmful SQL queries while reducing false positives. This addresses issues where legitimate column names like `created_at` were incorrectly flagged as harmful due to containing substrings like "create".

The security LLM analysis:
- Distinguishes between legitimate column/table names and actual malicious commands
- Reduces false positives compared to simple keyword matching
- Provides contextual analysis based on the database schema
- Offers confidence levels for security assessments

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

## Configuration

The agent can be configured via environment variables in the `.env` file:

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: API key for OpenAI services
- `SQL_LLM_MODEL`: Model to use for SQL generation (default: gpt-3.5-turbo)
- `RESPONSE_LLM_MODEL`: Model to use for response generation (default: gpt-4)
- `PROMPT_LLM_MODEL`: Model to use for prompt generation (default: gpt-3.5-turbo)
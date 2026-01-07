# AI Agent for Natural Language to SQL Queries

This AI agent processes natural language requests from users, converts them to SQL queries, executes them against a PostgreSQL database, and returns natural language responses.

## Architecture

The AI agent consists of 5 main components:

1. **Database Manager**: Handles connections to PostgreSQL and retrieves schema information
2. **SQL Generator**: Uses an LLM to convert natural language requests to SQL queries
3. **SQL Executor**: Safely executes SQL queries against the database
4. **Prompt Generator**: Creates detailed prompts for the response LLM based on query results
5. **Response Generator**: Uses an LLM to create natural language responses

## Workflow

1. User submits a natural language request
2. The agent retrieves the database schema
3. The first LLM generates a SQL query based on the request and schema
4. The SQL query is executed against the database
5. The second LLM creates a detailed prompt for the response LLM
6. The third LLM generates a natural language response based on the database results
7. The response is returned to the user

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

## Configuration

The agent can be configured via environment variables in the `.env` file:

- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: API key for OpenAI services
- `SQL_LLM_MODEL`: Model to use for SQL generation (default: gpt-3.5-turbo)
- `RESPONSE_LLM_MODEL`: Model to use for response generation (default: gpt-4)
- `PROMPT_LLM_MODEL`: Model to use for prompt generation (default: gpt-3.5-turbo)
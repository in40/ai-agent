# SQL MCP Server

The SQL MCP Server is an MCP (Multi-Agent Communication Protocol) service that provides SQL generation and execution capabilities to other services in the system.

## Overview

The SQL MCP Server handles database-related operations including:
- SQL query generation based on natural language requests
- SQL query execution against configured databases
- Schema retrieval and validation
- SQL safety validation

## Architecture

The server follows the MCP pattern and includes:
- An HTTP API for receiving requests
- Integration with the service registry
- SQL generation and execution components
- Database management utilities

## Configuration

The server can be configured using environment variables:

- `SQL_MCP_HOST`: Host address to bind to (default: 127.0.0.1)
- `SQL_MCP_PORT`: Port to listen on (default: 8092)
- `SQL_MCP_REGISTRY_URL`: URL of the MCP registry server (default: http://127.0.0.1:8080)
- `SQL_MCP_LOG_LEVEL`: Logging level (default: INFO)

## Usage

### Starting the Server

```bash
python -m sql_mcp_server.sql_mcp_server --host 127.0.0.1 --port 8092 --registry-url http://127.0.0.1:8080
```

### Available Endpoints

The server accepts POST requests with the following action types:

#### Generate SQL Query
```json
{
  "action": "generate_sql",
  "parameters": {
    "user_request": "Show me all users",
    "schema_dump": {...},
    "attached_files": [...],
    "previous_sql_queries": [...],
    "table_to_db_mapping": {...},
    "table_to_real_db_mapping": {...}
  }
}
```

#### Execute SQL Query
```json
{
  "action": "execute_sql",
  "parameters": {
    "sql_query": "SELECT * FROM users;",
    "db_name": "mydb",
    "table_to_db_mapping": {...}
  }
}
```

#### Get Database Schema
```json
{
  "action": "get_schema",
  "parameters": {
    "db_name": "mydb"
  }
}
```

#### Validate SQL Query
```json
{
  "action": "validate_sql",
  "parameters": {
    "sql_query": "SELECT * FROM users;",
    "schema_dump": {...}
  }
}
```

## Client Usage

Use the provided client to communicate with the server:

```python
from sql_mcp_server.client import SQLMCPClient

client = SQLMCPClient(server_url="http://127.0.0.1:8092")

# Generate SQL
result = client.generate_sql(
    user_request="Show me all users",
    schema_dump={...}
)

# Execute SQL
result = client.execute_sql(
    sql_query="SELECT * FROM users;",
    db_name="mydb"
)
```

## Dependencies

- Python 3.8+
- aiohttp
- requests
- SQLAlchemy
- The core agent components (models, database utilities, etc.)

## Security

The server includes safety checks to prevent potentially harmful SQL commands from being executed. All SQL queries are validated before execution.
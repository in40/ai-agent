# MCP Standard Server - Comprehensive Implementation Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Transport Mechanisms](#transport-mechanisms)
4. [Core Components](#core-components)
5. [Standard MCP Methods](#standard-mcp-methods)
6. [Registry Functionality](#registry-functionality)
7. [Extending the Server](#extending-the-server)
8. [Configuration and Deployment](#configuration-and-deployment)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

## Overview

The MCP Standard Server is a fully compliant implementation of the Model Context Protocol (MCP) server in Python. It provides complete support for the MCP specification with multiple transport mechanisms and mandatory registry functionality.

### Key Features
- Full MCP specification compliance
- Three transport mechanisms: Streamable HTTP (default), Legacy HTTP/SSE, and STDIO
- Support for tools, resources, and prompts
- Client-initiated methods support
- Notification system for dynamic updates
- Mandatory service registry with SQLite/PostgreSQL backends (should not be disabled by default)
- Consistent shell script formatting following the standard provided in the skeleton
- Concurrency control and performance monitoring
- Comprehensive error handling

## Architecture

The server follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Transports    │◄──►│   RPC Handler    │◄──►│   Handlers      │
│ (stdio, http)   │    │ (json_rpc.py)    │    │ (server/client) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              ▲
                              │
                   ┌──────────────────┐
                   │  Notifications   │
                   │ (notifications)  │
                   └──────────────────┘
```

### Core Modules
- **`utils/json_rpc.py`**: Core JSON-RPC 2.0 message handling with concurrency control
- **`transports/`**: Transport-specific implementations (stdio, streamable_http, http_sse)
- **`handlers/`**: Server and client method handlers
- **`utils/`**: Supporting utilities (notifications, registry DB, heartbeat management)

## Transport Mechanisms

### 1. Streamable HTTP (Default)
The modern, standard-compliant transport using a single `/mcp` endpoint.

**Endpoints:**
- `/mcp`: Bidirectional communication (POST for client-to-server requests and responses, GET for connection metadata)
- `/metrics`: Performance and concurrency metrics

**Characteristics:**
- Single endpoint for bidirectional communication
- POST requests: Client sends JSON-RPC requests, server responds with JSON-RPC responses
- GET requests: Return connection metadata (not SSE stream)
- Supports session correlation via `MCP-Session-Id` header
- Security via Origin header validation
- Proper request/response correlation
- Content-Type: application/json (not text/event-stream)

### 2. Legacy HTTP/SSE
Backward-compatible transport with separate endpoints.

**Endpoints:**
- `/sse`: Server-Sent Events for server-to-client communication
- `/message` (or `/send`): Client-to-server communication via POST
- `/metrics`: Performance and concurrency metrics

**Characteristics:**
- Separate endpoints for different communication directions
- Session correlation via `X-MCP-Session-ID` header
- Automatic endpoint discovery via initial `endpoint` event

### 3. STDIO
Traditional transport using standard input/output streams.

**Characteristics:**
- Launch as subprocess
- Messages delimited by newlines
- Suitable for local communication
- No network overhead

## Core Components

### JSON-RPC Handler (`utils/json_rpc.py`)
Handles all JSON-RPC 2.0 message processing with concurrency control.

**Key Features:**
- Message parsing and validation
- Request/response correlation
- Concurrency limiting with semaphore
- Error handling and standard error codes
- Async and sync message processing

**Concurrency Control:**
- Configurable maximum concurrent requests (default: 10)
- Semaphore-based request limiting
- Performance metrics tracking
- Automatic failure recording

### Server Handlers (`handlers/server_handlers.py`)
Implements all standard MCP server methods.

**Default Capabilities:**
- **Tools**: `example_tool` - echoes back input
- **Resources**: `example://resource/data` - returns sample data
- **Prompts**: `example_prompt` - template with subject argument

**Registry Support:**
- Enabled with `--enable-registry` flag
- Adds `registry/register`, `registry/list`, `registry/unregister` methods
- Supports both SQLite and PostgreSQL backends

### Client Handlers (`handlers/client_handlers.py`)
Handles methods that the server can initiate on the client.

**Supported Methods:**
- `sampling/complete`: Request language model completion
- `elicitation/request`: Request user input/confirmation
- `logging/message`: Send log messages to client

### Notification Manager (`utils/notifications.py`)
Manages MCP notifications for dynamic updates.

**Notification Types:**
- `notifications/tools/list_changed`
- `notifications/resources/list_changed`
- `notifications/prompts/list_changed`

## Standard MCP Methods

### Server Methods

#### `initialize`
Initializes the connection and exchanges capabilities.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "initialize",
  "params": {
    "clientInfo": {
      "name": "client-name",
      "version": "1.0.0"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "mcp-standard-server",
      "version": "1.0.0"
    },
    "capabilities": {
      "tools": {
        "listChanged": true
      },
      "resources": {
        "listChanged": true
      },
      "prompts": {
        "listChanged": true
      }
    }
  }
}
```

#### `tools/list`
Lists available tools with pagination support.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "tools/list",
  "params": {
    "pagination": {
      "limit": 10,
      "cursor": "cursor_value"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "tools": [
      {
        "name": "example_tool",
        "description": "An example tool that echoes back the input",
        "inputSchema": {
          "type": "object",
          "properties": {
            "input": {"type": "string", "description": "Input to echo back"}
          },
          "required": ["input"]
        }
      }
    ],
    "pagination": {
      "hasMore": false,
      "nextCursor": null
    }
  }
}
```

#### `tools/call`
Executes a specific tool with given arguments.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "method": "tools/call",
  "params": {
    "name": "example_tool",
    "arguments": {
      "input": "Hello, world!"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "result": {
    "output": "Echo: Hello, world!"
  }
}
```

#### `resources/list` and `resources/read`
Similar to tools but for resources.

#### `prompts/list` and `prompts/get`
Similar to tools but for prompts with argument resolution.

#### `shutdown` and `ping`
- `shutdown`: Initiates graceful server shutdown
- `ping`: Health check returning timestamp and status

### Client Methods (Server-Initiated)

#### `sampling/complete`
Requests language model completion from client.

#### `elicitation/request`
Requests user input from client.

#### `logging/message`
Sends log message to client.

## Registry Functionality

The server includes mandatory registry functionality that should not be disabled by default. The server can operate in two distinct registry modes:

### Registry Server Mode
When enabled with `--enable-registry`, the server acts as a central registry to track available services from other MCP servers.

**Usage:**
```bash
python -m mcp_std_server.server --transport streamable-http --port 3030 --enable-registry
```

### Registry Client Mode
When enabled with `--register-with-registry`, the server registers itself with an external registry server.

**Usage:**
```bash
python -m mcp_std_server.server --transport streamable-http --port 3031 --register-with-registry --registry-host 127.0.0.1 --registry-port 3030
```

### Registry Methods (when --enable-registry is used)

#### `registry/register`
Registers a service with the registry.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "reg-1",
  "method": "registry/register",
  "params": {
    "id": "service-123",
    "name": "My Service",
    "description": "A sample service",
    "endpoint": "http://localhost:3030",
    "capabilities": {
      "tools": ["tool1", "tool2"],
      "resources": ["res1", "res2"],
      "prompts": ["prompt1"]
    }
  }
}
```

#### `registry/list`
Lists all registered services.

#### `registry/unregister`
Removes a service from the registry.

### Database Backends

#### SQLite (Default)
- File-based storage in `mcp_registry.db`
- No configuration required
- Suitable for development and small deployments
- Separate TaskStorage class available for storing received and submitted tasks in addition to registry data

#### PostgreSQL
- Production-ready database solution
- Requires PostgreSQL installation
- Better for high-concurrency scenarios
- Separate TaskStorage class available for storing received and submitted tasks in addition to registry data

**Configuration:**
```bash
--use-postgres
--postgres-host localhost
--postgres-port 5432
--postgres-db mcp_registry
--postgres-user postgres
--postgres-password password
```

### Task Storage
- The server includes a separate TaskStorage class for persisting received and submitted tasks
- Tasks are stored separately from registry data to maintain clear separation of concerns
- Both SQLite and PostgreSQL backends support persistent task storage with status tracking
- Tasks survive server restarts and maintain their state in the database
- Separate schema for task management allows for independent scaling of task processing and service registry

### Heartbeat Management

#### Local Heartbeat Manager
Manages services registered in the local registry:
- Updates `last_seen` timestamp every 30 seconds
- Removes stale services after 10 minutes of inactivity

#### Remote Heartbeat Manager
Manages services that register with a remote registry:
- Maintains registration status with remote registry
- Handles graceful deregistration on shutdown

### Registry Architecture:
1. **Registry Server** - Central server that tracks available services (use `--enable-registry`)
2. **Service Servers** - Individual MCP servers that register their capabilities
3. **Registry Clients** - MCP servers that register with an external registry (use `--register-with-registry`)
4. **AI Agent** - Queries the registry to discover available services

### How to Use Registry:
1. **As Registry Server**: Start the server with `--enable-registry` flag to accept registrations from other servers
2. **As Registry Client**: Start the server with `--register-with-registry` flag to register with an external registry server
3. Other MCP servers can register with the registry via the `/mcp` endpoint (for Streamable HTTP) or `/send` endpoint (for legacy)
4. AI agents can discover services by querying the registry's `registry/list` method
5. Services can deregister via the `registry/unregister` method

## Extending the Server

### Adding Custom Tools

```python
from mcp_std_server.handlers.server_handlers import McpServerHandlers

class CustomMcpServerHandlers(McpServerHandlers):
    def __init__(self, enable_registry=False, use_postgres=False, postgres_config=None):
        super().__init__(enable_registry, use_postgres, postgres_config)

        # Add custom tool
        custom_tool = {
            "name": "custom_calculation",
            "description": "Performs custom calculations",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "multiply"]},
                    "operands": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["operation", "operands"]
            }
        }
        self.tools.append(custom_tool)

    def _execute_tool(self, tool, arguments):
        if tool["name"] == "custom_calculation":
            op = arguments.get("operation")
            operands = arguments.get("operands", [])

            if op == "add":
                result = sum(operands)
            elif op == "multiply":
                result = 1
                for num in operands:
                    result *= num
            else:
                raise ValueError(f"Unknown operation: {op}")

            return {"result": result}

        # Call parent method for other tools
        return super()._execute_tool(tool, arguments)
```

### Customizing Tools for Specific Domains

The server provides a flexible framework for implementing domain-specific tools. When extending the server for specific use cases (e.g., IT leadership, project management, etc.), consider implementing specialized tools that align with the domain requirements:

- **Domain-Specific Tools**: Implement tools tailored to your specific use case (e.g., assign_task, review_code, generate_project_plan for IT leadership)
- **Tool Input Validation**: Define appropriate input schemas for each tool to ensure proper validation
- **Status Tracking**: Implement proper status tracking for long-running operations
- **Integration Points**: Connect tools with external systems as needed for your domain

Example domain-specific tools might include:
- Task assignment and management tools
- Code review and quality assurance tools
- Project planning and scheduling tools
- Team communication and coordination tools
- Progress tracking and reporting tools

### Adding Custom Resources

```python
# In the same CustomMcpServerHandlers class
def __init__(self, enable_registry=False, use_postgres=False, postgres_config=None):
    super().__init__(enable_registry, use_postgres, postgres_config)
    
    # Add custom resource
    custom_resource = {
        "uri": "custom://config/app-config",
        "name": "Application Configuration",
        "description": "Current application configuration"
    }
    self.resources.append(custom_resource)

def _read_resource(self, resource):
    if resource["uri"] == "custom://config/app-config":
        return {
            "contents": [{
                "uri": resource["uri"],
                "text": '{"debug": true, "version": "1.0.0"}'
            }]
        }
    
    # Call parent method for other resources
    return super()._read_resource(resource)
```

### Adding Custom Prompts

```python
# In the same CustomMcpServerHandlers class
def __init__(self, enable_registry=False, use_postgres=False, postgres_config=None):
    super().__init__(enable_registry, use_postgres, postgres_config)
    
    # Add custom prompt
    custom_prompt = {
        "name": "custom_greeting",
        "description": "Generates a personalized greeting",
        "arguments": [
            {
                "name": "name",
                "type": "string",
                "description": "Person's name"
            }
        ]
    }
    self.prompts.append(custom_prompt)

def _resolve_prompt(self, prompt, arguments):
    if prompt["name"] == "custom_greeting":
        name = arguments.get("name", "Friend")
        resolved_text = f"Hello, {name}! Welcome to our service."
        return {
            "contents": [{
                "type": "text",
                "text": resolved_text
            }]
        }
    
    # Call parent method for other prompts
    return super()._resolve_prompt(prompt, arguments)
```

### Creating a Custom Server

```python
from mcp_std_server.server import McpServer

class MyCustomMcpServer(McpServer):
    def __init__(self, transport_type="streamable-http", host="127.0.0.1", port=3030, 
                 enable_registry=False, max_concurrent_requests=10):
        # Initialize with custom handlers
        super().__init__(transport_type, host, port, enable_registry, 
                         max_concurrent_requests=max_concurrent_requests)
        
        # Replace with custom handlers if needed
        # self.server_handlers = CustomMcpServerHandlers(...)
```

## Configuration and Deployment

### Command-Line Options

#### Basic Options
- `--transport`: Transport type (stdio, http, streamable-http) [default: streamable-http]
- `--host`: Host for HTTP transport [default: 127.0.0.1]
- `--port`: Port for HTTP transport [default: 3030]
- `--max-concurrent-requests`: Max concurrent requests [default: 10]

#### Registry Options
- `--enable-registry`: Enable registry functionality (mandatory and enabled by default)
- `--register-with-registry`: Register with a registry server
- `--registry-host`: Registry server host [default: 127.0.0.1]
- `--registry-port`: Registry server port [default: 3031]

#### PostgreSQL Options
- `--use-postgres`: Use PostgreSQL for registry storage
- `--postgres-host`: PostgreSQL host [default: 127.0.0.1]
- `--postgres-port`: PostgreSQL port [default: 5432]
- `--postgres-db`: Database name [default: mcp_registry]
- `--postgres-user`: Username [default: postgres]
- `--postgres-password`: Password [default: empty]

### Port Configuration Clarification
Understanding the difference between server and client ports:
- `--port`: The port that this server listens on for incoming connections (server port)
- `--client-port`: The port that this server connects to when acting as a client to other servers
- When using `--register-with-registry`, the server acts as a client to connect to the registry server
- Default server port is 3030, default registry client port is 3031
- These ports can be configured independently to avoid conflicts

### Startup Scripts

All MCP server implementations should follow the same shell script format as provided in the skeleton for consistency:

#### `start_mcp_server.sh`
Comprehensive script with all configuration options.

#### `start_registry_server.sh`
Specifically configured for registry servers.

#### `start_mcp_default.sh`
Quick start with default settings.

#### Script Format Standards
All implementations must follow the same .sh script format as provided with the skeleton, ensuring consistency across different MCP server deployments.

### Environment Considerations

#### Production Deployment
- Use PostgreSQL backend for registry
- Configure appropriate concurrency limits
- Set up proper logging and monitoring
- Use reverse proxy for SSL termination

#### Development
- SQLite backend is sufficient
- Lower concurrency limits acceptable
- Enable debugging if needed

## Security Considerations

### Transport Security

#### Streamable HTTP
- Origin header validation to prevent DNS rebinding
- Session correlation via headers
- Rate limiting considerations

#### Legacy HTTP/SSE
- Similar security measures apply
- Proper endpoint validation

#### STDIO
- Inherently secure for local processes
- No network exposure

### Database Security

#### PostgreSQL Authentication
When using PostgreSQL, ensure secure authentication by:
- Setting strong passwords via `--postgres-password` parameter
- Using dedicated database users with minimal required privileges
- Storing credentials in environment variables when possible rather than command line
- Ensuring the PostgreSQL server is properly secured and accessible only from authorized networks

### Data Validation

#### Input Sanitization
- All JSON-RPC messages are validated
- Schema validation for tool arguments
- URI validation for resources

#### Error Handling
- Proper error responses without information leakage
- Standard error codes per JSON-RPC 2.0 specification

### Access Control
- No built-in authentication (implement as needed)
- Network-level access controls recommended
- Consider API keys for production use

## Troubleshooting

### Common Issues

#### Transport Not Working
- Verify the correct endpoint is being used
- Check firewall/network connectivity
- Ensure proper headers are sent

#### Registry Registration Failures
- Verify registry server is running
- Check network connectivity to registry
- Ensure correct endpoint format

#### Concurrency Issues
- Adjust `--max-concurrent-requests` as needed
- Monitor `/metrics` endpoint for performance data
- Consider scaling horizontally

#### Database Connection Issues
- For PostgreSQL: Verify connection parameters
- Check database server accessibility
- Ensure proper authentication credentials

### Debugging Tips

#### Enable Verbose Logging
Add logging to your custom implementations to trace execution flow.

#### Use Metrics Endpoint
Check `/metrics` endpoint for performance and concurrency data.

#### Test with Simple Cases
Start with basic tools/resources before implementing complex logic.

### Performance Monitoring

#### Key Metrics
- Current concurrent requests
- Total requests processed
- Failed requests count
- Uptime information

#### Monitoring Recommendations
- Set up alerts for high failure rates
- Monitor concurrency levels
- Track response times

## Best Practices

### Code Organization
- Keep custom logic in separate classes/files
- Follow the existing architecture patterns
- Maintain separation of concerns

### Error Handling
- Use appropriate JSON-RPC error codes
- Provide meaningful error messages
- Log errors for debugging

### Performance
- Implement efficient data structures
- Use async methods where appropriate
- Consider caching for expensive operations

### Security
- Validate all inputs
- Sanitize outputs where necessary
- Implement rate limiting if needed

### Testing
- Test all custom methods thoroughly
- Verify edge cases and error conditions
- Use the provided test framework as a base

### Implementation Standards
- All MCP server implementations must include registry functionality as mandatory (not optional)

## Mixed-Mode Operation

The server supports mixed-mode operation, functioning as both an MCP server (receiving tasks) and an MCP client (submitting tasks to other servers).

### Mixed-Mode Architecture
- **Dual Operation**: Server accepts inbound connections while maintaining outbound client connections
- **Registry Integration**: Automatic service discovery for cross-server task delegation
- **Task Delegation**: Ability to forward operations to other registered MCP servers
- **Load Balancing**: Intelligent routing of requests to appropriate servers based on capabilities

### Cross-Server Task Delegation Logic
When registry functionality is enabled, the server can automatically delegate tasks to other registered MCP servers. The delegation logic works as follows:

1. **Service Discovery**: The server queries the registry to discover available services and their capabilities
2. **Capability Matching**: Tasks are matched to servers based on their advertised capabilities
3. **Intelligent Routing**: Requests are forwarded to appropriate servers based on their capabilities
4. **Result Aggregation**: Results from remote servers are returned to the original requester

### Mixed-Mode Configuration
The server can be configured for mixed-mode operation using the following command-line options:
- `--enable-client-mode`: Enable client functionality to connect to other servers
- `--client-transport`: Specify transport for client connections
- `--client-host`, `--client-port`: Target server address for client connections
- `--client-endpoint`: Direct endpoint specification for client connections

### Cross-Server Operations
When operating in mixed mode, the server provides these capabilities:
- `delegate_tool_call()`: Forward tool execution to another server
- `fetch_remote_resource()`: Retrieve resources from other servers
- `resolve_remote_prompt()`: Get prompt results from other servers
- Automatic service discovery through registry integration
- Load balancing based on server capabilities and availability

## Shell Script Variables

The MCP server comes with several shell scripts for different deployment scenarios. Each script supports various environment variables and command-line parameters:

### `start_mcp_server.sh`
Comprehensive script with all configuration options.

**Environment Variables and Parameters:**
- `TRANSPORT` (default: "streamable-http"): Transport type (stdio, http, streamable-http)
- `HOST` (default: "127.0.0.1"): Host for HTTP transport
- `PORT` (default: 3030): Port for HTTP transport
- `ENABLE_REGISTRY` (default: false): Enable registry functionality to track multiple MCP services
- `REGISTER_WITH_REGISTRY` (default: true): Register this server with a registry server
- `REGISTRY_HOST` (default: "127.0.0.1"): Registry server host to register with
- `REGISTRY_PORT` (default: 3031): Registry server port to register with
- `USE_POSTGRES` (default: false): Use PostgreSQL for registry storage instead of SQLite
- `MAX_CONCURRENT_REQUESTS` (default: 10): Maximum number of concurrent requests

### `start_registry_server.sh`
Specifically configured for registry servers.

**Environment Variables and Parameters:**
- `TRANSPORT` (default: "streamable-http"): Transport type (http, streamable-http)
- `HOST` (default: "127.0.0.1"): Host for HTTP transport
- `PORT` (default: 3031): Port for HTTP transport (registry default)
- `USE_POSTGRES` (default: false): Use PostgreSQL for registry storage instead of SQLite
- `MAX_CONCURRENT_REQUESTS` (default: 10): Maximum number of concurrent requests
- `BACKGROUND` (default: false): Run server in background
- `LOG_FILE`: Redirect output to log file
- `PID_FILE`: Write process ID to file

### `start_mcp_default.sh`
Quick start with default settings.

**Environment Variables and Parameters:**
- Uses default settings: Streamable HTTP transport on port 3030
# Dedicated MCP Model Documentation

## Overview

The Dedicated MCP Model is a specialized model designed specifically for handling MCP (Model Context Protocol)-related queries. It provides a separate, dedicated instance for processing MCP service requests, allowing for optimized configuration and performance for MCP-specific tasks.

## Architecture

The Dedicated MCP Model extends the functionality of the original MCPCapableModel but uses separate configuration settings. This separation allows for:

- Different LLM providers/models for MCP-specific tasks
- Specialized system prompts for MCP service interactions
- Optimized configuration for MCP-related queries
- Better resource management and scaling

## Configuration

The Dedicated MCP Model uses the following environment variables for configuration:

```
# Dedicated MCP LLM Configuration (separate model specifically for MCP-related queries)
DEDICATED_MCP_LLM_PROVIDER=LM Studio
DEDICATED_MCP_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
DEDICATED_MCP_LLM_HOSTNAME=localhost
DEDICATED_MCP_LLM_PORT=1234
DEDICATED_MCP_LLM_API_PATH=/v1
```

### Fallback Behavior

If the dedicated MCP configuration is not set, the model will fall back to using the general MCP configuration:

```
# MCP LLM Configuration (for MCP service queries)
MCP_LLM_PROVIDER=LM Studio
MCP_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
MCP_LLM_HOSTNAME=localhost
MCP_LLM_PORT=1234
MCP_LLM_API_PATH=/v1
```

And if neither is set, it will fall back to the prompt configuration.

## Usage in LangGraph Agent

The Dedicated MCP Model is integrated into the LangGraph agent workflow:

1. `query_mcp_services_node` - Uses the dedicated model to generate tool calls for MCP services
2. `execute_mcp_tool_calls_and_return_node` - Uses the dedicated model to execute tool calls
3. `return_mcp_response_to_llm_node` - Uses the dedicated model to format responses for the LLM

## Key Features

- **Separate Configuration**: Independent settings for optimal MCP service handling
- **Specialized Prompts**: Tailored system prompts for MCP-specific tasks
- **Fallback Support**: Graceful degradation to original MCPCapableModel if dedicated model unavailable
- **Integration**: Seamlessly integrates with existing MCP service discovery and execution workflows

## Implementation Details

The DedicatedMCPModel class implements the same interface as MCPCapableModel, providing:

- `generate_mcp_tool_calls()` - Generates appropriate tool calls for MCP services
- `execute_mcp_tool_calls()` - Executes the generated tool calls
- `return_response_to_llm()` - Formats responses for LLM processing
- `_call_mcp_service()` - Handles actual communication with MCP services

## Best Practices

1. Use a lightweight, fast model for the dedicated MCP model since MCP queries are typically simpler
2. Configure appropriate timeouts for MCP service calls
3. Monitor MCP service availability and response times
4. Consider using a different provider/model than your primary LLM for better resource allocation
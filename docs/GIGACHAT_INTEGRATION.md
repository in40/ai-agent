# GigaChat Integration

## Overview

This project now supports GigaChat models with OAuth token-based authentication. GigaChat is a Russian language model developed by SberDevices that can be used as an alternative to other LLM providers.

## Features

- OAuth token-based authentication
- Support for multiple GigaChat API scopes
- Integration with the existing LLM provider system
- Compatibility with all LLM-using components (SQL generation, response generation, security analysis, MCP services, etc.)
- SSL certificate verification options for self-signed certificates
- Seamless fallback mechanisms

## Configuration

### Environment Variables

The following environment variables are used for GigaChat configuration:

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
- `MCP_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for MCP service queries
- `DEDICATED_MCP_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for dedicated MCP-related queries

## Authentication Methods

GigaChat supports multiple authentication methods:

1. **Credentials-based (OAuth)**: Using `GIGACHAT_CREDENTIALS` which will automatically handle OAuth token acquisition
2. **Pre-generated Access Token**: Using `GIGACHAT_ACCESS_TOKEN` directly
3. **Username/Password**: Not currently implemented in this integration
4. **TLS Certificates**: Not currently implemented in this integration

## Setup Script

The setup script (`setup_config.py`) has been updated to include GigaChat configuration options. Run it with:

```bash
python setup_config.py
```

## Usage Examples

### Basic Usage

To use GigaChat for SQL generation, set the following environment variables:

```bash
export SQL_LLM_PROVIDER=GigaChat
export GIGACHAT_CREDENTIALS="your_credentials_here"
```

### Full Integration

To use GigaChat for all LLM components:

```bash
export SQL_LLM_PROVIDER=GigaChat
export RESPONSE_LLM_PROVIDER=GigaChat
export PROMPT_LLM_PROVIDER=GigaChat
export SECURITY_LLM_PROVIDER=GigaChat
export MCP_LLM_PROVIDER=GigaChat
export DEDICATED_MCP_LLM_PROVIDER=GigaChat
export GIGACHAT_CREDENTIALS="your_credentials_here"
```

### Programmatic Usage

```python
import os

# Set environment variables
os.environ["GIGACHAT_CREDENTIALS"] = "your_credentials_here"
os.environ["GIGACHAT_SCOPE"] = "GIGACHAT_API_PERS"
os.environ["SQL_LLM_PROVIDER"] = "GigaChat"
os.environ["SQL_LLM_MODEL"] = "GigaChat:latest"

# Import and use the AI Agent
from ai_agent import AIAgent
agent = AIAgent()
```

## Dependencies

The following dependencies have been added to support GigaChat:
- `gigachat`: The official GigaChat Python SDK
- `langchain-gigachat`: Official LangChain integration for GigaChat

## Implementation Details

The integration includes:
- A custom `GigaChatModel` class that extends LangChain's `BaseChatModel`
- OAuth token handling within the model class
- Support for all model components (SQL generation, response generation, prompt generation, security analysis, MCP services)
- Proper error handling and validation
- Compatibility with existing configuration patterns
- Support for both the traditional linear architecture and the enhanced LangGraph architecture

## Security Considerations

- Store your GigaChat credentials securely and never commit them to version control
- Consider using environment files (.env) to manage credentials
- Regularly rotate your credentials
- If using self-signed certificates, ensure you trust the certificate authority
- Monitor API usage to avoid unexpected charges

## Troubleshooting

Common issues and solutions:

1. **Authentication failures**: Verify that your credentials are correct and have sufficient permissions
2. **SSL certificate errors**: If using self-signed certificates, set `GIGACHAT_VERIFY_SSL_CERTS=false`
3. **Rate limiting**: Implement appropriate delays between requests if hitting rate limits
4. **Scope issues**: Ensure your credentials have access to the requested scope (PERS, B2B, or CORP)
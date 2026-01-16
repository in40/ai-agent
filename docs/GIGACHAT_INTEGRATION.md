# GigaChat Integration

This project now supports GigaChat models with OAuth token-based authentication.

## Configuration

To use GigaChat models, you need to configure the following environment variables:

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

## Example Usage

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
- Support for all model components (SQL generation, response generation, prompt generation, security analysis)
- Proper error handling and validation
- Compatibility with existing configuration patterns
- Support for both the traditional linear architecture and the enhanced LangGraph architecture
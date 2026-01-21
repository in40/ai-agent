# Setup and Configuration Guide for AI Agent with MCP Architecture

This guide provides comprehensive instructions for setting up and configuring the AI agent with MCP (Model Context Protocol) architecture.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Access to an LLM service (LM Studio, OpenAI, GigaChat, etc.)
- For web search functionality: Brave Search API key
- For database functionality (optional): Database connection details

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai_agent
```

### 2. Create Virtual Environment

```bash
python -m venv ai_agent_env
source ai_agent_env/bin/activate  # On Windows: ai_agent_env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configurations:

```bash
# Main LLM Configuration
DEFAULT_LLM_PROVIDER=LM Studio
DEFAULT_LLM_MODEL=md-coder-qwen3-8b
DEFAULT_LLM_HOSTNAME=your-llm-hostname
DEFAULT_LLM_PORT=1234
DEFAULT_LLM_API_PATH=/v1

# MCP-Specific LLM Configuration (for MCP service queries)
MCP_LLM_PROVIDER=LM Studio
MCP_LLM_MODEL=md-coder-qwen3-8b
MCP_LLM_HOSTNAME=your-llm-hostname
MCP_LLM_PORT=1234
MCP_LLM_API_PATH=/v1

# Dedicated MCP Model Configuration (for optimized MCP-related queries)
DEDICATED_MCP_LLM_PROVIDER=LM Studio
DEDICATED_MCP_LLM_MODEL=md-coder-qwen3-8b
DEDICATED_MCP_LLM_HOSTNAME=your-llm-hostname
DEDICATED_MCP_LLM_PORT=1234
DEDICATED_MCP_LLM_API_PATH=/v1

# API Keys
BRAVE_SEARCH_API_KEY=your_brave_search_api_key  # For web search functionality

# Registry Configuration
REGISTRY_URL=http://127.0.0.1:8080

# RAG Configuration
RAG_ENABLED=true
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_VECTOR_STORE_TYPE=chroma
RAG_TOP_K_RESULTS=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=100
RAG_CHROMA_PERSIST_DIR=./data/chroma_db
RAG_COLLECTION_NAME=documents
RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx,.html,.md

# Security Configuration
SECURITY_LLM_MODEL=md-coder-qwen3-8b
USE_SECURITY_LLM=true
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL=true

# Logging Configuration
ENABLE_SCREEN_LOGGING=true
```

### 2. MCP Services Configuration

The AI agent uses an MCP (Model Context Protocol) architecture with the following services:

#### Registry Server
The registry server manages discovery of MCP services. It runs on port 8080 by default.

#### RAG Service
Handles document retrieval and ingestion:
- Host: 127.0.0.1
- Port: 8091
- Registry URL: http://127.0.0.1:8080

#### Search Service
Provides web search functionality:
- Host: 127.0.0.1
- Port: 8090
- Registry URL: http://127.0.0.1:8080

#### SQL Service
Handles database queries (when enabled):
- Host: 127.0.0.1
- Port: 8092
- Registry URL: http://127.0.0.1:8080

#### DNS Service
Resolves hostnames to IP addresses:
- Host: 127.0.0.1
- Port: 8089
- Registry URL: http://127.0.0.1:8080

## Running the System

### 1. Start MCP Services

First, start the registry server:

```bash
python -m registry.start_registry_server
```

Then start the MCP services:

```bash
# RAG Service
python -m rag_component.rag_mcp_server --host 127.0.0.1 --port 8091 --registry-url http://127.0.0.1:8080

# Search Service
python -m search_server.mcp_search_server --host 127.0.0.1 --port 8090 --registry-url http://127.0.0.1:8080

# SQL Service (if using database functionality)
python -m sql_mcp_server.sql_mcp_server --host 127.0.0.1 --port 8092 --registry-url http://127.0.0.1:8080

# DNS Service
python -m search_server.mcp_dns_server --host 127.0.0.1 --port 8089 --registry-url http://127.0.0.1:8080
```

### 2. Start the AI Agent

```bash
python -m core.main --registry-url http://127.0.0.1:8080
```

### 3. Using the Run Script

Alternatively, you can use the provided run script that starts all services:

```bash
./run_me.sh
```

## Configuration Options

### MCP Service Configuration

#### Registry URL
The `REGISTRY_URL` environment variable specifies where the MCP services register and where the AI agent discovers them.

#### Dedicated MCP Model
The `DEDICATED_MCP_LLM_*` environment variables allow you to configure a separate LLM specifically for MCP-related queries, which can be optimized for tool calling and service interaction.

### RAG Configuration

#### Embedding Models
- `RAG_EMBEDDING_MODEL`: Choose from local models like `all-MiniLM-L6-v2` or cloud models like `text-embedding-ada-002`
- Local models offer privacy but may be slower
- Cloud models offer speed but require internet access and may incur costs

#### Vector Store Settings
- `RAG_TOP_K_RESULTS`: Number of results to retrieve (default: 5)
- `RAG_SIMILARITY_THRESHOLD`: Minimum similarity score (0.0-1.0, default: 0.7)
- `RAG_CHUNK_SIZE`: Size of text chunks when processing documents (default: 1000)
- `RAG_CHUNK_OVERLAP`: Overlap between chunks to preserve context (default: 100)

### Security Configuration

#### SQL Security (when database functionality enabled)
- `USE_SECURITY_LLM`: Enable advanced LLM-based security analysis (default: true)
- `TERMINATE_ON_POTENTIALLY_HARMFUL_SQL`: Block potentially harmful SQL (default: true)
- The security LLM reduces false positives by distinguishing between legitimate column names (like `created_at`) and actual harmful commands

## Troubleshooting

### Common Issues

#### Issue: Services not registering with the registry
**Symptoms:** AI agent reports services as unavailable
**Solution:** 
1. Verify the registry server is running on the configured port
2. Check that service registry URLs match between services and the AI agent
3. Ensure firewall rules allow communication between services

#### Issue: RAG service not responding
**Symptoms:** Document queries return no results despite documents being ingested
**Solution:**
1. Verify the RAG service is running and registered
2. Check that the vector store directory contains data
3. Confirm embedding model compatibility

#### Issue: MCP model not generating appropriate tool calls
**Symptoms:** AI agent doesn't use available MCP services
**Solution:**
1. Verify the dedicated MCP model is properly configured
2. Check that the model has appropriate training for tool calling
3. Confirm service capabilities are properly advertised in the registry

### Configuration Validation

You can validate your configuration by running:

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

# Check required environment variables
required_vars = ['REGISTRY_URL', 'DEFAULT_LLM_PROVIDER', 'DEFAULT_LLM_MODEL']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f'Missing required environment variables: {missing_vars}')
else:
    print('✓ All required environment variables are set')

# Check registry connectivity
import requests
registry_url = os.getenv('REGISTRY_URL', 'http://127.0.0.1:8080')
try:
    response = requests.get(f'{registry_url}/health', timeout=5)
    if response.status_code == 200:
        print('✓ Registry server is accessible')
    else:
        print(f'✗ Registry server returned status: {response.status_code}')
except requests.exceptions.RequestException:
    print('✗ Registry server is not accessible')
"
```

## Performance Tuning

### For Better Responsiveness
```bash
# Use faster embedding model
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Reduce number of results retrieved
RAG_TOP_K_RESULTS=3

# Use smaller chunk sizes for faster processing
RAG_CHUNK_SIZE=500
```

### For Better Accuracy
```bash
# Use higher quality embedding model
RAG_EMBEDDING_MODEL=all-mpnet-base-v2

# Increase number of results retrieved
RAG_TOP_K_RESULTS=8

# Lower similarity threshold to get more results
RAG_SIMILARITY_THRESHOLD=0.6

# Use larger chunk sizes to preserve more context
RAG_CHUNK_SIZE=1500
RAG_CHUNK_OVERLAP=200
```

## Production Deployment

### Environment Considerations
- Use environment-specific configuration files
- Implement proper secret management for API keys
- Set up monitoring for the registry and services
- Configure appropriate resource limits for each service

### Scaling Recommendations
- Deploy registry server with high availability
- Scale MCP services based on demand
- Use load balancers for high-traffic deployments
- Implement circuit breakers for service resilience
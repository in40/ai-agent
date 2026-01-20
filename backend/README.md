# AI Agent System - Microservices Architecture (v0.2)

## Overview

This project implements a microservices architecture for the AI Agent system, decomposing the monolithic application into independent services. The system consists of:

- **Authentication Service**: Handles user authentication, authorization, and session management
- **Agent Service**: Processes AI agent requests and generates responses
- **RAG Service**: Manages document processing and retrieval
- **API Gateway**: Routes requests to appropriate services
- **Web Client**: A React-based single-page application with multiple tabs
- **Command-Line Client**: Maintains original functionality with backend support
- **Nginx Proxy**: Handles TLS termination and routing to backend services

## v0.2 Enhancements

Version 0.2 introduces significant improvements:

### Security Enhancements
- **Role-Based Access Control (RBAC)**: Fine-grained permissions for different user roles
- **Rate Limiting**: Protection against API abuse with configurable limits
- **Enhanced Input Validation**: Comprehensive validation and sanitization of all inputs
- **Audit Logging**: Detailed logging of all user actions for security monitoring
- **Session Management**: Improved session handling with automatic expiration
- **API Key Support**: Programmatic access with secure API keys

### Scalability Enhancements
- **Microservices Architecture**: Decomposed monolith into independent services
- **Independent Scaling**: Each service can be scaled independently
- **Distributed Deployment**: Services can be deployed across multiple machines
- **Load Balancing**: Support for distributing requests across multiple instances
- **Service Discovery**: Mechanisms for services to discover each other

## Architecture Components

### Authentication Service (`/backend/services/auth/`)

Handles user authentication, authorization, and session management:

- User registration and login
- JWT token generation and validation
- Role-based access control (RBAC)
- Session management
- Audit logging

### Agent Service (`/backend/services/agent/`)

Handles AI agent requests and processing:

- Natural language processing
- SQL generation and execution
- Response generation
- Integration with LLM providers

### RAG Service (`/backend/services/rag/`)

Handles document processing and retrieval:

- Document ingestion and indexing
- Document retrieval and lookup
- RAG query processing
- Vector storage management

### API Gateway (`/backend/services/gateway/`)

Routes requests to appropriate services:

- Single entry point for all client requests
- Request routing to appropriate services
- Cross-cutting concerns (authentication, logging, rate limiting)
- Protocol translation if needed

### Web Client (`/backend/web_client/`)

The web client includes:

- **Main Client Tab**: Interface to the AI agent
- **Streamlit GUI Tab**: Embedded Streamlit interface
- **React GUI Tab**: Embedded React workflow editor
- **RAG Functions Tab**: Document ingestion, lookup, and querying
- **Authentication**: Login and registration pages

### Command-Line Client (`/backend/cli_client.py`)

Maintains all original functionality while adding:

- **Backend Mode**: Can connect to backend API when URL provided
- **Standalone Mode**: Runs locally as before
- **RAG Support**: Full access to RAG functionality

### Nginx Configuration

- **TLS Termination**: Handles HTTPS with SSL certificates
- **Load Balancing**: Distributes requests to microservices
- **Routing**: Directs requests to appropriate services via API Gateway
- **Security**: Implements security headers and protections
- **Entry Point**: API Gateway serves as the main entry point for all requests

## Deployment Options

### Single Machine Deployment

All services run on the same machine:

```
API Gateway: http://localhost:5000
Authentication Service: http://localhost:5001
Agent Service: http://localhost:5002
RAG Service: http://localhost:5003
Web Client: https://localhost (via nginx)
Streamlit: http://localhost:8501
React: http://localhost:3000
```

### Distributed Deployment

Services can be deployed across multiple machines using the configuration system:

```python
# config.py
config = {
    'services': {
        'auth_service_url': 'http://auth.example.com:5001',
        'agent_service_url': 'http://agent.example.com:5002',
        'rag_service_url': 'http://rag.example.com:5003',
        'gateway_url': 'http://gateway.example.com:5000',
        'streamlit_url': 'http://streamlit.example.com:8501',
        'react_url': 'http://react.example.com:3000',
        'registry_url': 'http://registry.example.com:8080'
    }
}
```

## Running the System

### Using the Startup Script (Recommended)

1. **Start all services**:
   ```bash
   cd /path/to/ai_agent
   ./backend/services/start_microservices.sh
   ```

### Manual Start

1. **Start Redis** (required for session management and rate limiting):
   ```bash
   redis-server
   ```

2. **Start each service individually**:
   ```bash
   # Terminal 1: Start authentication service
   cd /path/to/ai_agent
   source ai_agent_env/bin/activate
   export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
   python -m backend.services.auth.app

   # Terminal 2: Start agent service
   cd /path/to/ai_agent
   source ai_agent_env/bin/activate
   export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
   python -m backend.services.agent.app

   # Terminal 3: Start RAG service
   cd /path/to/ai_agent
   source ai_agent_env/bin/activate
   export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
   python -m backend.services.rag.app

   # Terminal 4: Start API gateway
   cd /path/to/ai_agent
   source ai_agent_env/bin/activate
   export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
   python -m backend.services.gateway.app
   ```

## API Endpoints

### Through API Gateway (recommended)
- `POST /auth/register` - Register new user (rate limited: 5/5min)
- `POST /auth/login` - Authenticate user (rate limited: 10/min)
- `POST /agent/query` - Process natural language request (rate limited: 30/min, requires `write:agent`)
- `GET /agent/status` - Check agent status (requires `read:agent`)
- `POST /rag/query` - Query RAG system (rate limited: 20/min, requires `read:rag`)
- `POST /rag/ingest` - Ingest documents (rate limited: 10/min, requires `write:rag`)
- `POST /rag/retrieve` - Retrieve documents (rate limited: 20/min, requires `read:rag`)
- `POST /rag/lookup` - Lookup documents (rate limited: 20/min, requires `read:rag`)
- `GET /health` - Health check (rate limited: 60/min)

### Direct Service Access
- Authentication Service: `http://localhost:5001`
- Agent Service: `http://localhost:5002`
- RAG Service: `http://localhost:5003`

## Security Features

- **JWT Authentication**: Across all services
- **Role-Based Access Control**: Enforced at service level
- **Rate Limiting**: Per-service rate limiting
- **Input Validation**: At service boundaries
- **Audit Logging**: Per-service audit trails
- **Session Management**: Secure session handling with automatic expiration
- **HTTPS**: TLS encryption for all communications
- **CORS Policy**: Restricts cross-origin requests

## Configuration

The system uses environment variables for configuration:

```bash
# Authentication service
AUTH_SERVICE_URL=http://auth-service:5001

# Agent service
AGENT_SERVICE_URL=http://agent-service:5002

# RAG service
RAG_SERVICE_URL=http://rag-service:5003

# API Gateway
GATEWAY_PORT=5000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Testing

Run the comprehensive test suite:

```bash
python backend/test_integrated_system.py
```

For v0.2 security features:
```bash
python backend/test_security_v02.py
```

This tests:
- Microservices functionality
- Authentication system
- RBAC permissions
- Rate limiting
- Input validation
- Service communication
- Web client accessibility
- Service availability

## Migration from v0.1

See `MIGRATION_GUIDE_v02.md` for details on migrating from v0.1 to v0.2.

## Service Communication

Services communicate internally using HTTP/REST APIs:

- Client applications communicate with the API Gateway
- The API Gateway forwards requests to appropriate services
- Services may communicate with each other when needed
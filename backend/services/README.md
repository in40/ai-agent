# AI Agent System - Microservices Architecture (v0.2)

## Overview

This document describes the microservices architecture implemented in version 0.2 of the AI Agent system. The monolithic architecture has been decomposed into four independent services:

1. **Authentication Service** - Handles user authentication, authorization, and session management
2. **Agent Service** - Handles AI agent requests and processing
3. **RAG Service** - Handles document processing and retrieval
4. **API Gateway** - Routes requests to appropriate services

## Architecture Components

### Authentication Service (`/backend/services/auth/`)

The authentication service handles:

- User registration and login
- JWT token generation and validation
- Role-based access control (RBAC)
- Session management
- Audit logging

**Endpoints:**
- `POST /register` - Register new user
- `POST /login` - Authenticate user
- `POST /validate` - Validate JWT token

### Agent Service (`/backend/services/agent/`)

The agent service handles:

- AI agent requests and processing
- Natural language to SQL conversion
- Database query execution
- Response generation

**Endpoints:**
- `POST /query` - Process natural language request
- `GET /status` - Check agent status

### RAG Service (`/backend/services/rag/`)

The RAG service handles:

- Document ingestion and indexing
- Document retrieval and lookup
- RAG query processing

**Endpoints:**
- `POST /query` - Query RAG system
- `POST /ingest` - Ingest documents
- `POST /retrieve` - Retrieve documents
- `POST /lookup` - Lookup documents
- `GET /status` - Check RAG status

### API Gateway (`/backend/services/gateway/`)

The API gateway serves as:

- Single entry point for all client requests
- Request routing to appropriate services
- Cross-cutting concerns (authentication, logging, rate limiting)
- Protocol translation if needed

**Endpoints:**
- `GET /health` - Health check
- `/auth/*` - Proxies to authentication service
- `/agent/*` - Proxies to agent service
- `/rag/*` - Proxies to RAG service
- Convenience endpoints that map to appropriate services

## Running the System

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

### Using the Startup Script (Recommended)

1. **Start all services**:
   ```bash
   cd /path/to/ai_agent
   ./backend/services/start_microservices.sh
   ```

## Service Communication

### Internal Communication

Services communicate internally using HTTP/REST APIs:

- Client applications communicate with the API Gateway
- The API Gateway forwards requests to appropriate services
- Services may communicate with each other when needed

### Configuration

Services are configured using environment variables:

- `AUTH_SERVICE_URL` - URL of the authentication service
- `AGENT_SERVICE_URL` - URL of the agent service
- `RAG_SERVICE_URL` - URL of the RAG service
- `REDIS_HOST` - Host of the Redis instance
- `REDIS_PORT` - Port of the Redis instance

## Scaling Considerations

### Horizontal Scaling

Each service can be scaled independently based on demand:

- **Authentication Service**: Moderate scaling, stateful with Redis
- **Agent Service**: High scaling potential, stateless
- **RAG Service**: Moderate scaling, may be limited by document processing
- **API Gateway**: High scaling potential, stateless

### Load Balancing

Load balancers can be placed in front of multiple instances of each service to distribute traffic.

## Security Features

The microservices architecture maintains all security features from the monolithic version:

- **JWT Authentication**: Across all services
- **Role-Based Access Control**: Enforced at service level
- **Rate Limiting**: Per-service rate limiting
- **Input Validation**: At service boundaries
- **Audit Logging**: Per-service audit trails

## Deployment Options

### Containerized Deployment

The system can be deployed using Docker containers orchestrated by Docker Compose or Kubernetes.

### Cloud-Native Deployment

The microservices architecture is suitable for cloud-native deployment on platforms like AWS, Azure, or GCP.

## Migration from Monolithic Architecture

The API Gateway provides backward compatibility with the previous monolithic API, allowing gradual migration of client applications.
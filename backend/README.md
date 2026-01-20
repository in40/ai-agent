# AI Agent System - Backend and Frontend Architecture

## Overview

This project implements a split architecture for the AI Agent system, separating backend services from client interfaces. The system consists of:

- **Backend API Server**: A Flask-based server providing authenticated endpoints
- **Web Client**: A React-based single-page application with multiple tabs
- **Command-Line Client**: Maintains original functionality with backend support
- **Nginx Proxy**: Handles TLS termination and routing to backend services

## Architecture Components

### Backend API Server (`/backend/app.py`)

The backend provides:

- **Authentication**: JWT-based authentication with register/login endpoints
- **Agent API**: `/api/agent/query` for AI agent functionality
- **RAG API**: `/api/rag/*` endpoints for document management and retrieval
- **Service Proxies**: For Streamlit and React GUIs
- **Static File Serving**: For the web client

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
- **Load Balancing**: Distributes requests to backend services
- **Routing**: Directs requests to appropriate services
- **Security**: Implements security headers and protections

## Deployment Options

### Single Machine Deployment

All services run on the same machine:

```
Backend API: http://localhost:5000
Web Client: https://localhost (via nginx)
Streamlit: http://localhost:8501
React: http://localhost:3000
```

### Distributed Deployment

Services can be deployed across multiple machines using the configuration system:

```python
# config.py
config = {
    'backend': {
        'host': 'backend.example.com',
        'port': 5000
    },
    'services': {
        'streamlit_url': 'http://streamlit.example.com:8501',
        'react_url': 'http://react.example.com:3000',
        'registry_url': 'http://registry.example.com:8080'
    }
}
```

## Running the System

### Quick Start

1. **Start all services**:
   ```bash
   cd /path/to/ai_agent
   ./backend/start_system.sh
   ```

2. **Access the web client**:
   - Navigate to `https://localhost` (requires nginx setup)
   - Or directly access `http://localhost:5000` for the web client

3. **Use the command-line client**:
   ```bash
   # Standalone mode
   python -m core.main
   
   # Backend mode
   python backend/cli_client.py --backend-url https://localhost --auth-token YOUR_TOKEN
   ```

### Manual Start

1. **Start backend**:
   ```bash
   cd /path/to/ai_agent
   source ai_agent_env/bin/activate
   export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
   python -m flask --app backend.app run --host=0.0.0.0 --port=5000
   ```

2. **Start supporting services**:
   ```bash
   # Start Streamlit
   streamlit run gui/enhanced_streamlit_app.py --server.port 8501
   
   # Start React (in gui/react_editor/)
   cd gui/react_editor
   npm start
   ```

3. **Configure nginx** (for production):
   ```bash
   ./backend/setup_nginx_tls.sh
   ```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Authenticate user

### Agent
- `POST /api/agent/query` - Process natural language request
- `GET /api/agent/status` - Check agent status

### RAG
- `POST /api/rag/query` - Query RAG system
- `POST /api/rag/ingest` - Ingest documents
- `POST /api/rag/retrieve` - Retrieve documents
- `POST /api/rag/lookup` - Lookup documents

### System
- `GET /api/health` - Health check
- `GET /api/config` - Get system configuration
- `GET /api/services` - List available services

## Security Features

- **JWT Authentication**: All API endpoints require authentication
- **HTTPS**: TLS encryption for all communications
- **Input Validation**: Sanitizes all user inputs
- **Rate Limiting**: Prevents abuse of services
- **CORS Policy**: Restricts cross-origin requests

## Configuration

The system uses a flexible configuration system:

```python
from backend.config import config_manager

# Get backend configuration
backend_config = config_manager.get_backend_config()

# Get services configuration
services_config = config_manager.get_services_config()

# Update configuration
config_manager.update_config({
    'backend': {
        'host': 'new-host.example.com',
        'port': 5001
    }
})
```

## Testing

Run the comprehensive test suite:

```bash
python backend/test_integrated_system.py
```

This tests:
- Backend API functionality
- Authentication system
- Web client accessibility
- Service availability
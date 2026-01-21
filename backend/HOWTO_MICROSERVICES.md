# AI Agent System v0.2 - Microservices HOWTO Guide

This guide provides detailed instructions for working with the new microservices architecture in v0.2.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Service Configuration](#service-configuration)
5. [Development Workflow](#development-workflow)
6. [Troubleshooting](#troubleshooting)
7. [Scaling Guidelines](#scaling-guidelines)

## Overview

The v0.2 architecture decomposes the monolithic application into four independent services:

- **Auth Service** (port 5001): Handles authentication and authorization
- **Agent Service** (port 5002): Processes AI agent requests
- **RAG Service** (port 5003): Manages document processing
- **Gateway** (port 5000): Routes requests to appropriate services

## Prerequisites

Before deploying the microservices, ensure you have:

- Python 3.8+
- Redis server (for session management and rate limiting)
- Docker and Docker Compose (for containerized deployment)
- Virtual environment with required packages

### Installing Dependencies

```bash
cd /path/to/ai_agent
source ai_agent_env/bin/activate
pip install -r backend/services/requirements.txt
```

### Starting Redis

```bash
# Option 1: Using system Redis
redis-server

# Option 2: Using Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

## Deployment Options

### Option 1: Manual Deployment

Start each service individually:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Auth Service
cd /path/to/ai_agent
source ai_agent_env/bin/activate
export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
export REDIS_HOST=localhost
export REDIS_PORT=6379
python -m backend.services.auth.app

# Terminal 3: Start Agent Service
cd /path/to/ai_agent
source ai_agent_env/bin/activate
export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
python -m backend.services.agent.app

# Terminal 4: Start RAG Service
cd /path/to/ai_agent
source ai_agent_env/bin/activate
export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
python -m backend.services.rag.app

# Terminal 5: Start Gateway
cd /path/to/ai_agent
source ai_agent_env/bin/activate
export PYTHONPATH=/path/to/ai_agent:$PYTHONPATH
export AUTH_SERVICE_URL=http://localhost:5001
export AGENT_SERVICE_URL=http://localhost:5002
export RAG_SERVICE_URL=http://localhost:5003
python -m backend.services.gateway.app
```

### Option 2: Using Startup Script (Recommended)

Use the provided startup script:

```bash
cd /path/to/ai_agent
./backend/services/start_microservices.sh
```

## Service Configuration

### Environment Variables

Each service can be configured using environment variables:

#### Auth Service
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export SECRET_KEY=your-secret-key
export JWT_SECRET_KEY=your-jwt-secret
export AUTH_SERVICE_PORT=5001
```

#### Agent Service
```bash
export AGENT_SERVICE_PORT=5002
export AUTH_SERVICE_URL=http://localhost:5001
```

#### RAG Service
```bash
export RAG_SERVICE_PORT=5003
export AUTH_SERVICE_URL=http://localhost:5001
```

#### Gateway
```bash
export GATEWAY_PORT=5000
export AUTH_SERVICE_URL=http://localhost:5001
export AGENT_SERVICE_URL=http://localhost:5002
export RAG_SERVICE_URL=http://localhost:5003
```

### Configuration Files

For production deployments, create `.env` files:

```bash
# backend/services/.env
REDIS_HOST=redis-service
REDIS_PORT=6379
SECRET_KEY=production-secret-key-change-this
JWT_SECRET_KEY=production-jwt-secret-change-this
AUTH_SERVICE_URL=http://auth-service:5001
AGENT_SERVICE_URL=http://agent-service:5002
RAG_SERVICE_URL=http://rag-service:5003
```

## Development Workflow

### Running in Development Mode

For development, you can run services with auto-reload:

```bash
# For auth service
export FLASK_ENV=development
export FLASK_DEBUG=1
python -m backend.services.auth.app

# For agent service
export FLASK_ENV=development
export FLASK_DEBUG=1
python -m backend.services.agent.app

# For RAG service
export FLASK_ENV=development
export FLASK_DEBUG=1
python -m backend.services.rag.app

# For gateway
export FLASK_ENV=development
export FLASK_DEBUG=1
python -m backend.services.gateway.app
```

### Testing Individual Services

Test each service independently:

```bash
# Test auth service
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Test agent service
curl -X POST http://localhost:5002/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"user_request": "What is your name?"}'

# Test RAG service
curl -X POST http://localhost:5003/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"query": "What is the meaning of life?"}'

# Test gateway (recommended approach)
curl -X POST http://localhost:5000/agent/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"user_request": "What is your name?"}'
```

### Adding New Services

To add a new service:

1. Create a new directory in `/backend/services/`
2. Create an `app.py` file with your Flask application
3. Add security decorators as needed
4. Update the gateway to route requests to your service
5. Add Dockerfile and update docker-compose.yml
6. Update documentation

Example service template:

```python
"""
New Service for AI Agent System
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

# Import security components
from backend.security import require_permission, validate_input, Permission

# Initialize Flask app
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'new-service',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.2.0'
    }), 200

# Add your service endpoints here
# Remember to add security decorators where needed

if __name__ == '__main__':
    port = int(os.getenv('NEW_SERVICE_PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=False)
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
- Check if Redis is running
- Verify environment variables are set correctly
- Check logs for specific error messages

#### 2. Service-to-Service Communication Fails
- Verify service URLs are correct
- Check firewall settings
- Ensure services are running on expected ports

#### 3. Authentication Issues
- Verify JWT secrets are consistent across services
- Check that auth service is accessible from other services
- Verify token format (should be "Bearer TOKEN")

#### 4. Rate Limiting Issues
- Check Redis connectivity
- Verify rate limit configuration
- Check if Redis is properly storing rate limit data

### Debugging Commands

Check if services are running:
```bash
# Check if Redis is running
redis-cli ping

# Check if services are listening on ports
netstat -tuln | grep -E '500[0-4]'
```

View service logs:
```bash
# Check the log files created by the startup script
tail -f auth_service.log
tail -f agent_service.log
tail -f rag_service.log
tail -f gateway.log
```

### Health Checks

Each service has a health check endpoint:

```bash
curl http://localhost:5001/health  # Auth service
curl http://localhost:5002/health  # Agent service
curl http://localhost:5003/health  # RAG service
curl http://localhost:5000/health  # Gateway
```

## Scaling Guidelines

### When to Scale Each Service

#### Auth Service
- Scale up if experiencing authentication delays
- Typically requires fewer instances than other services
- Consider caching strategies for token validation

#### Agent Service
- Scale up during high query volume
- CPU-intensive operations, monitor CPU usage
- Consider instance types with good CPU performance

#### RAG Service
- Scale up when processing many documents
- Memory-intensive operations, monitor memory usage
- Consider instance types with good memory performance

#### Gateway
- Scale up with overall system traffic
- Should be balanced with downstream service capacity
- Consider CDN for static assets

### Scaling Commands

For scaling, you would typically deploy additional instances of services on separate machines or processes. Since we're using a manual deployment approach, scaling involves:

1. Deploying additional instances of services on separate machines or processes
2. Using a load balancer to distribute traffic among instances

Monitor resource usage:
```bash
# Monitor system resources
htop
```

### Performance Tuning

#### Redis Configuration
- Increase maxmemory if experiencing cache evictions
- Enable persistence if needed
- Monitor slow queries

#### Application Configuration
- Adjust worker processes based on CPU cores
- Tune connection pools to databases
- Optimize database queries

## Security Best Practices

### Production Deployment
- Use strong, unique secrets for JWT and session management
- Implement HTTPS/TLS termination
- Regularly rotate secrets
- Monitor authentication logs for suspicious activity

### Network Security
- Use private networks for service-to-service communication
- Implement firewall rules to restrict access
- Use VPN for cross-datacenter communication

### Data Security
- Encrypt sensitive data in transit and at rest
- Implement proper access controls
- Regular security audits
# AI Agent Service Management

This directory contains scripts to manage all services of the AI Agent system.

## Available Scripts

### Starting Services

1. **start_all_services.sh** - Starts all services in the correct order
   ```bash
   ./start_all_services.sh
   ```

### Stopping Services

2. **stop_all_services.sh** - Stops all running services
   ```bash
   ./stop_all_services.sh
   ```

### Checking Service Status

3. **check_all_services.sh** - Checks which services are currently running
   ```bash
   ./check_all_services.sh
   ```

## Services Overview

The AI Agent system consists of the following services:

- **API Gateway** (Port 5000): Main entry point that proxies requests to other services
- **Authentication Service** (Port 5001): Handles user registration and login
- **Agent Service** (Port 5002): Core AI agent functionality
- **RAG Service** (Port 5003): Retrieval-Augmented Generation component
- **LangGraph Studio** (Port 8000): LangGraph workflow visualization
- **Streamlit App** (Port 8501): Web-based interface for interaction
- **React Editor** (Port 3000): Visual workflow editor

## Important URLs

- Web Client: https://192.168.51.138
- API Gateway: http://192.168.51.138:5000
- Authentication: http://192.168.51.138:5001/auth/login

## Authentication

To use the web client, you need to register and login first:

1. Register a user:
   ```bash
   curl -X POST http://192.168.51.138:5000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"myusername","password":"mypassword"}'
   ```

2. Login to get a token:
   ```bash
   curl -X POST http://192.168.51.138:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"myusername","password":"mypassword"}'
   ```

## Troubleshooting

If you encounter issues:

1. Check if all services are running: `./check_all_services.sh`
2. Make sure the virtual environment is activated: `source ai_agent_env/bin/activate`
3. Verify that Redis is running if you're using authentication features
4. Check the log files in the project root for error messages
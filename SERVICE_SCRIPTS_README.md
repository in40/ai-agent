# LangGraph AI Agent Service Scripts

This directory contains scripts to start individual services of the LangGraph AI Agent suite.

## Available Scripts

### Individual Service Starters

1. **start_streamlit.sh** - Starts the Streamlit application on port 8501
   ```bash
   ./start_streamlit.sh
   ```
   Access at: http://localhost:8501

2. **start_langgraph_studio.sh** - Starts the LangGraph Studio server on port 8000
   ```bash
   ./start_langgraph_studio.sh
   ```
   Access at: http://localhost:8000

3. **start_react_editor.sh** - Starts the React development server on port 3000
   ```bash
   ./start_react_editor.sh
   ```
   Access at: http://localhost:3000

### Master Starter

4. **start_all_services.sh** - Starts all services in the background
   ```bash
   ./start_all_services.sh
   ```
   This script starts all three services and runs them in the background.

## Notes

- Make sure you have the required dependencies installed before running these scripts
- The React editor requires Node.js and npm to be installed
- The Python applications require the dependencies listed in requirements.txt
- The AI agent requires proper configuration via environment variables in .env file
- Logs for the background processes are stored in:
  - `react_server.log`
  - `streamlit_server.log`
  - `langgraph_server.log`

## Stopping Services

To stop individual services, use the corresponding stop scripts:

1. **stop_streamlit.sh** - Stops the Streamlit application on port 8501
   ```bash
   ./stop_streamlit.sh
   ```

2. **stop_langgraph_studio.sh** - Stops the LangGraph Studio server on port 8000
   ```bash
   ./stop_langgraph_studio.sh
   ```

3. **stop_react_editor.sh** - Stops the React development server on port 3000
   ```bash
   ./stop_react_editor.sh
   ```

### Master Stop Script

4. **stop_all_services.sh** - Stops all services at once
   ```bash
   ./stop_all_services.sh
   ```

Alternatively, you can still use manual methods:
```bash
# Find the process IDs
ps aux | grep -E "(streamlit|python|react-scripts)"

# Kill specific processes
kill <PID>
```

Or use pkill to stop specific services:
```bash
pkill -f "streamlit"
pkill -f "react-scripts start"
pkill -f "gui/server.py"
```

## Service Architecture

The LangGraph AI Agent suite consists of the following services:

- **GUI Interface (Streamlit)**: Provides a visual interface for interacting with the AI agent, visualizing workflows, and monitoring execution
- **LangGraph Studio**: Provides tools for designing, testing, and managing LangGraph workflows
- **React Editor**: A web-based editor for creating and modifying LangGraph workflows with a visual interface
- **AI Agent Core**: The main processing engine that handles natural language requests, generates SQL queries, executes them against databases, and returns natural language responses

## Running the Full Suite

To run the complete LangGraph AI Agent suite with all services:

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your database URLs and API keys
   ```

3. Start all services:
   ```bash
   ./start_all_services.sh
   ```

4. Access the services:
   - GUI Interface: http://localhost:8501
   - LangGraph Studio: http://localhost:8000
   - React Editor: http://localhost:3000

## Service Dependencies

- The AI agent requires a database connection (PostgreSQL, MySQL, etc.) as configured in the .env file
- MCP (Model Context Protocol) services may be required for certain advanced features
- LLM (Large Language Model) access is required for SQL generation, response generation, and security analysis
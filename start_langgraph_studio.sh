#!/bin/bash
# Script to start the LangGraph Studio server on port 8000

cd /root/qwen_test/ai_agent

# Activate the Python environment if needed
# Uncomment the next line if you have a virtual environment
# source venv/bin/activate

# Run the server with minimal output to avoid interfering with parent script
python gui/server.py 2>/dev/null
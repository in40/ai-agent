#!/bin/bash
# Script to start the LangGraph Studio server on port 8000

echo "Starting LangGraph Studio server on port 8000..."
cd /root/qwen_test/ai_agent

# Activate the Python environment if needed
# Uncomment the next line if you have a virtual environment
# source venv/bin/activate

python gui/server.py
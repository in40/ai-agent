#!/bin/bash
# Master script to start all LangGraph Editor services

echo "Starting all LangGraph Editor services..."

# Start React development server in the background
echo "Starting React development server on port 3000..."
nohup /root/qwen_test/ai_agent/start_react_editor.sh > react_server.log 2>&1 &

# Wait a moment for the React server to start
sleep 5

# Start Streamlit application in the background
echo "Starting Streamlit application on port 8501..."
nohup /root/qwen_test/ai_agent/start_streamlit.sh > streamlit_server.log 2>&1 &

# Wait a moment for the Streamlit server to start
sleep 5

# Start LangGraph Studio server in the background
echo "Starting LangGraph Studio server on port 8000..."
nohup /root/qwen_test/ai_agent/start_langgraph_studio.sh > langgraph_server.log 2>&1 &

echo "All services started!"
echo "React Editor: http://localhost:3000"
echo "Streamlit App: http://localhost:8501"
echo "LangGraph Studio: http://localhost:8000"

# Show the running processes
echo "Running processes:"
jobs -l
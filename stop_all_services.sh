#!/bin/bash
# Master script to stop all LangGraph Editor services

echo "Stopping all LangGraph Editor services..."

# Stop React development server
echo "Stopping React development server on port 3000..."
PORT=3000
PID=$(lsof -t -i:$PORT 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "Found React process $PID, stopping it..."
    kill $PID
else
    echo "No React process found on port $PORT"
fi

# Stop Streamlit application
echo "Stopping Streamlit application on port 8501..."
PORT=8501
PID=$(lsof -t -i:$PORT 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "Found Streamlit process $PID, stopping it..."
    kill $PID
else
    echo "No Streamlit process found on port $PORT"
fi

# Stop LangGraph Studio server
echo "Stopping LangGraph Studio server on port 8000..."
PORT=8000
PID=$(lsof -t -i:$PORT 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "Found LangGraph Studio process $PID, stopping it..."
    kill $PID
else
    echo "No LangGraph Studio process found on port $PORT"
fi

echo "All services stopped!"
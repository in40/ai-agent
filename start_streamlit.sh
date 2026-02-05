#!/bin/bash
# Script to start the Streamlit application on port 8501

cd /root/qwen/ai_agent

# Activate the Python environment
source ai_agent_env/bin/activate

# Check if a process is already running on port 8501
PORT=8501
PID=$(lsof -t -i:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Port $PORT is already in use by process $PID. Killing the process..."
    kill $PID
    sleep 2
fi

# Start the Streamlit app in the background
nohup streamlit run gui/enhanced_streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --logger.level=WARNING > streamlit_output.log 2>&1 &

echo "Streamlit application started on port $PORT. Check streamlit_output.log for details."
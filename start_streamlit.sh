#!/bin/bash
# Script to start the Streamlit application on port 8501

echo "Starting Streamlit application on port 8501..."
cd /root/qwen_test/ai_agent

# Activate the Python environment if needed
# Uncomment the next line if you have a virtual environment
# source venv/bin/activate

streamlit run gui/enhanced_streamlit_app.py --server.port=8501 --server.address=0.0.0.0
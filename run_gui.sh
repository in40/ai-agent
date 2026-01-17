#!/bin/bash

# Script to run the LangGraph GUI application

echo "Starting LangGraph Visual Editor..."
echo "Make sure you have installed the required dependencies:"
echo "pip install -r gui/requirements.txt"
echo ""

cd /root/qwen_test/ai_agent

# Run the Streamlit application
streamlit run gui/streamlit_app.py --server.address=0.0.0.0 --server.port=8501
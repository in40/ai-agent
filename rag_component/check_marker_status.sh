#!/bin/bash

# Script to check the status of marker models and LLM configuration
# Run this script to see the current status of your marker library setup

echo "==========================================="
echo "MARKER LIBRARY STATUS CHECK"
echo "==========================================="

# Change to the rag_component directory
cd /root/qwen_test/ai_agent/rag_component

# Run the Python script
python check_marker_status.py

echo ""
echo "==========================================="
echo "STATUS CHECK COMPLETED"
echo "==========================================="
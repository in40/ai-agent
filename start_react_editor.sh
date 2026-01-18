#!/bin/bash
# Script to start the React development server on port 3000

echo "Starting React development server on port 3000..."
cd /root/qwen_test/ai_agent/gui/react_editor

# Install dependencies if not already installed
npm install

# Start the React development server
npx react-scripts start
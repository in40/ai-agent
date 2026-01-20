#!/bin/bash
# Script to start the React Editor server

cd /root/qwen_test/ai_agent/gui/react_editor
source ../../ai_agent_env/bin/activate
npm install
npx react-scripts start
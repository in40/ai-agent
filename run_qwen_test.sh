#!/bin/bash
# Wrapper to clear env vars and run Qwen test
unset RESPONSE_LLM_HOSTNAME RESPONSE_LLM_MODEL RESPONSE_LLM_API_PATH RESPONSE_LLM_PORT RESPONSE_LLM_PROVIDER
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate
exec python3 /root/qwen/ai_agent/test_qwen_direct.py "$@"

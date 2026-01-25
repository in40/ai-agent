#!/usr/bin/env python3
"""Debug script to check the check_rag_applicability_node function."""

import os
from langgraph_agent.langgraph_agent import check_rag_applicability_node

# Set environment variables
os.environ['RAG_ENABLED'] = 'true'
os.environ['RAG_MODE'] = 'local'

# Create a test state
state = {
    "user_request": "Explain quantum computing concepts",
    "discovered_services": [{"id": "sql-service", "type": "sql"}],  # No RAG service
    "rag_query": ""
}

print("Environment variables:")
print(f"  RAG_ENABLED: {os.environ.get('RAG_ENABLED')}")
print(f"  RAG_MODE: {os.environ.get('RAG_MODE')}")

print(f"\nInput state: {state}")

result = check_rag_applicability_node(state)

print(f"\nResult: {result}")
print(f"use_rag_flag: {result['use_rag_flag']}")
#!/usr/bin/env python3
"""
NLP Data Scientist MCP Server
Entity extraction and NLP analysis tools using spaCy, NLTK, and LLM (LM Studio)
"""
import sys
import os

# Ensure proper imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_nlp_server.server import create_nlp_server

if __name__ == "__main__":
    create_nlp_server()

#!/usr/bin/env python3
"""Test script to check if environment variables are loaded properly"""

import os
from dotenv import load_dotenv

print("Before loading .env:")
print(f"RAG_QDRANT_API_KEY: {repr(os.getenv('RAG_QDRANT_API_KEY'))}")

# Load the environment
load_dotenv()

print("\nAfter loading .env:")
print(f"RAG_QDRANT_API_KEY: {repr(os.getenv('RAG_QDRANT_API_KEY'))}")
print(f"RAG_QDRANT_URL: {repr(os.getenv('RAG_QDRANT_URL'))}")

# Also check a few other variables to see if anything loads
print(f"RAG_ENABLED: {repr(os.getenv('RAG_ENABLED'))}")
print(f"DEFAULT_LLM_PROVIDER: {repr(os.getenv('DEFAULT_LLM_PROVIDER'))}")
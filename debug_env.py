#!/usr/bin/env python3
"""Debug script to check .env file parsing"""

from dotenv import dotenv_values
import os

# Load using dotenv_values to see raw content
raw_config = dotenv_values(".env")
print("Raw config keys:", list(raw_config.keys()))
print("RAG_QDRANT_API_KEY in raw config:", "RAG_QDRANT_API_KEY" in raw_config)
if "RAG_QDRANT_API_KEY" in raw_config:
    print("RAG_QDRANT_API_KEY value:", repr(raw_config["RAG_QDRANT_API_KEY"]))

# Check for any keys that might contain "QDRANT_API_KEY"
qdrant_keys = [key for key in raw_config.keys() if "QDRANT" in key]
print("QDRANT-related keys:", qdrant_keys)
for key in qdrant_keys:
    print(f"  {key}: {repr(raw_config[key])}")

# Now try load_dotenv and see what gets set in os.environ
from dotenv import load_dotenv
load_dotenv()

print("\nAfter load_dotenv():")
print("RAG_QDRANT_API_KEY in os.environ:", "RAG_QDRANT_API_KEY" in os.environ)
if "RAG_QDRANT_API_KEY" in os.environ:
    print("RAG_QDRANT_API_KEY from os.environ:", repr(os.environ["RAG_QDRANT_API_KEY"]))
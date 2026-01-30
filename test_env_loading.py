#!/usr/bin/env python3
"""
Test script that mimics the RAG MCP Server environment variable loading
"""

# Load environment variables from .env file FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path
import sys

# Add the project root to the path so we can import from rag_component
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import the RAG config
from rag_component.config import RAG_QDRANT_API_KEY, RAG_QDRANT_URL

print(f"RAG_QDRANT_URL: {RAG_QDRANT_URL}")
print(f"RAG_QDRANT_API_KEY: {'Set' if RAG_QDRANT_API_KEY else 'Not set'}")

if not RAG_QDRANT_API_KEY:
    print("ERROR: RAG_QDRANT_API_KEY is not set!")
else:
    print(f"RAG_QDRANT_API_KEY length: {len(RAG_QDRANT_API_KEY)}")
    
    # Now try to connect to Qdrant
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(
            url=RAG_QDRANT_URL,
            api_key=RAG_QDRANT_API_KEY,
            prefer_grpc=False
        )
        
        print("Connected to Qdrant successfully!")
        
        # Try to list collections
        collections = client.get_collections()
        print(f"Collections: {collections}")
        
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        import traceback
        traceback.print_exc()
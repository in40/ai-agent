"""
Configuration module for the RAG component.
Handles environment variables and settings specific to RAG functionality.
"""
import os
from typing import Optional
from config.settings import str_to_bool


# RAG Configuration
RAG_ENABLED = str_to_bool(os.getenv("RAG_ENABLED", "true"))
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RAG_VECTOR_STORE_TYPE = os.getenv("RAG_VECTOR_STORE_TYPE", "chroma")
RAG_TOP_K_RESULTS = int(os.getenv("RAG_TOP_K_RESULTS", "5"))
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

# Vector store configuration
RAG_CHROMA_PERSIST_DIR = os.getenv("RAG_CHROMA_PERSIST_DIR", "./data/chroma_db")
RAG_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "documents")

# Document processing configuration
RAG_SUPPORTED_FILE_TYPES = os.getenv("RAG_SUPPORTED_FILE_TYPES", ".txt,.pdf,.docx,.html,.md").split(',')
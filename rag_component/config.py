"""
Configuration module for the RAG component.
Handles environment variables and settings specific to RAG functionality.
"""
import os
import sys
from pathlib import Path
from typing import Optional

# Get the project root (parent of rag_component)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from project root config.settings (not rag_component.config.settings)
try:
    # Try direct import from parent directory
    import config.settings as settings
    str_to_bool = settings.str_to_bool
    EMBEDDING_PROVIDER = settings.EMBEDDING_PROVIDER
    EMBEDDING_MODEL = settings.EMBEDDING_MODEL
except (ImportError, ModuleNotFoundError):
    # Fallback: directly import from file path
    import importlib.util
    spec = importlib.util.spec_from_file_location("settings", project_root / "config" / "settings.py")
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    str_to_bool = settings.str_to_bool
    EMBEDDING_PROVIDER = settings.EMBEDDING_PROVIDER
    EMBEDDING_MODEL = settings.EMBEDDING_MODEL


# RAG Configuration
RAG_ENABLED = str_to_bool(os.getenv("RAG_ENABLED", "true"))
RAG_MODE = os.getenv("RAG_MODE", "local").lower()  # Options: "local", "mcp", "hybrid"
# Only use RAG-specific provider/model if they are explicitly set in the environment
rag_embedding_provider_env = os.getenv("RAG_EMBEDDING_PROVIDER")
rag_embedding_model_env = os.getenv("RAG_EMBEDDING_MODEL")

RAG_EMBEDDING_PROVIDER = rag_embedding_provider_env if rag_embedding_provider_env is not None else EMBEDDING_PROVIDER
RAG_EMBEDDING_MODEL = rag_embedding_model_env if rag_embedding_model_env is not None else EMBEDDING_MODEL
RAG_VECTOR_STORE_TYPE = os.getenv("RAG_VECTOR_STORE_TYPE", "qdrant")
RAG_TOP_K_RESULTS = int(os.getenv("RAG_TOP_K_RESULTS", "5"))
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.3"))
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

# Vector store configuration
RAG_CHROMA_PERSIST_DIR = os.getenv("RAG_CHROMA_PERSIST_DIR", "./data/chroma_db")
RAG_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "documents")
RAG_QDRANT_URL = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")
RAG_QDRANT_API_KEY = os.getenv("RAG_QDRANT_API_KEY", "")

# Document processing configuration
RAG_SUPPORTED_FILE_TYPES = os.getenv("RAG_SUPPORTED_FILE_TYPES", ".txt,.pdf,.docx,.html,.md").split(',')

# PDF to Markdown conversion configuration
RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED = str_to_bool(os.getenv("RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED", "false"))
RAG_PDF_CONVERSION_QUALITY = os.getenv("RAG_PDF_CONVERSION_QUALITY", "standard")  # Options: "fast", "standard", "high"
RAG_USE_FALLBACK_ON_CONVERSION_ERROR = str_to_bool(os.getenv("RAG_USE_FALLBACK_ON_CONVERSION_ERROR", "true"))

# File storage configuration
RAG_FILE_STORAGE_DIR = os.getenv("RAG_FILE_STORAGE_DIR", "./data/rag_uploaded_files")
RAG_MARKDOWN_STORAGE_DIR = os.getenv("RAG_MARKDOWN_STORAGE_DIR", "./data/rag_converted_markdown")

# Reranker configuration
RERANKER_ENABLED = str_to_bool(os.getenv("RERANKER_ENABLED", "false"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "text-embedding-bge-reranker-v2-m3")
RERANKER_HOSTNAME = os.getenv("RERANKER_HOSTNAME", "localhost")
RERANKER_PORT = os.getenv("RERANKER_PORT", "1234")
RERANKER_API_PATH = os.getenv("RERANKER_API_PATH", "/v1")
RERANK_TOP_K_RESULTS = int(os.getenv("RERANK_TOP_K_RESULTS", "5"))

# Hybrid RAG configuration
RAG_RETRIEVER_MODE = os.getenv("RAG_RETRIEVER_MODE", "hybrid").lower()  # "vector", "graph", "hybrid"
RAG_HYBRID_VECTOR_WEIGHT = float(os.getenv("RAG_HYBRID_VECTOR_WEIGHT", "0.6"))
RAG_HYBRID_GRAPH_WEIGHT = float(os.getenv("RAG_HYBRID_GRAPH_WEIGHT", "0.4"))
RAG_GRAPH_EXPANSION_DEPTH = int(os.getenv("RAG_GRAPH_EXPANSION_DEPTH", "2"))
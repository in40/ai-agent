# RAG Component Configuration Reference

This document provides a comprehensive reference for all configuration options available for the RAG component.

## Environment Variables

### Core RAG Settings

#### `RAG_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enables or disables the RAG functionality in the AI agent
- **Values:** `true`, `false`
- **Example:** `RAG_ENABLED=true`
- **Notes:** When disabled, the agent will skip RAG evaluation and proceed directly with the traditional workflow

#### `RAG_EMBEDDING_MODEL`
- **Type:** String
- **Default:** `all-MiniLM-L6-v2`
- **Description:** Specifies the model to use for generating text embeddings
- **Examples:**
  - Local models: `all-MiniLM-L6-v2`, `all-mpnet-base-v2`, `multi-qa-mpnet-base-dot-v1`
  - OpenAI models: `text-embedding-ada-002`, `text-embedding-3-small`, `text-embedding-3-large`
- **Example:** `RAG_EMBEDDING_MODEL=all-mpnet-base-v2`
- **Notes:** Local models offer privacy but may be slower; cloud models offer speed but require internet and may have costs

#### `RAG_VECTOR_STORE_TYPE`
- **Type:** String
- **Default:** `chroma`
- **Description:** Specifies the type of vector store to use
- **Supported Values:** `chroma`, `faiss` (future support planned)
- **Example:** `RAG_VECTOR_STORE_TYPE=chroma`
- **Notes:** Currently only Chroma is fully implemented

#### `RAG_TOP_K_RESULTS`
- **Type:** Integer
- **Default:** `5`
- **Description:** Number of most similar documents to retrieve for each query
- **Range:** Positive integers (typically 1-20)
- **Example:** `RAG_TOP_K_RESULTS=10`
- **Notes:** Higher values provide more context but may slow down response; lower values are faster but may miss relevant information

#### `RAG_SIMILARITY_THRESHOLD`
- **Type:** Float
- **Default:** `0.7`
- **Description:** Minimum similarity score for retrieved documents (0.0 to 1.0)
- **Range:** 0.0 to 1.0
- **Example:** `RAG_SIMILARITY_THRESHOLD=0.6`
- **Notes:** Lower values return more results (possibly less relevant); higher values return fewer but more relevant results

### Document Processing Settings

#### `RAG_CHUNK_SIZE`
- **Type:** Integer
- **Default:** `1000`
- **Description:** Size of text chunks in tokens/characters when splitting documents
- **Range:** Positive integers (typically 500-2000)
- **Example:** `RAG_CHUNK_SIZE=800`
- **Notes:** Larger chunks provide more context but may exceed model limits; smaller chunks provide more precision but may lose context

#### `RAG_CHUNK_OVERLAP`
- **Type:** Integer
- **Default:** `100`
- **Description:** Number of tokens/characters to overlap between consecutive chunks
- **Range:** Non-negative integers (typically 0-200)
- **Example:** `RAG_CHUNK_OVERLAP=50`
- **Notes:** Helps preserve context across chunk boundaries; zero means no overlap

#### `RAG_SUPPORTED_FILE_TYPES`
- **Type:** String (comma-separated)
- **Default:** `.txt,.pdf,.docx,.html,.md`
- **Description:** List of file extensions the system will process
- **Format:** Extensions starting with dots, separated by commas
- **Example:** `RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx,.html,.md,.rtf`
- **Notes:** Files with unsupported extensions will be skipped during directory ingestion

### Vector Store Settings

#### `RAG_CHROMA_PERSIST_DIR`
- **Type:** String (path)
- **Default:** `./data/chroma_db`
- **Description:** Directory where Chroma will persist the vector database
- **Example:** `RAG_CHROMA_PERSIST_DIR=/opt/vectordb/chroma`
- **Notes:** Directory must be writable; will be created if it doesn't exist

#### `RAG_COLLECTION_NAME`
- **Type:** String
- **Default:** `documents`
- **Description:** Name of the Chroma collection to use for storing document embeddings
- **Example:** `RAG_COLLECTION_NAME=company_knowledge_base`
- **Notes:** Changing this creates a new collection; existing data remains in the old collection

## Configuration Best Practices

### Performance Optimization

#### For Speed
```bash
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_TOP_K_RESULTS=3
RAG_CHUNK_SIZE=500
```

#### For Quality
```bash
RAG_EMBEDDING_MODEL=all-mpnet-base-v2
RAG_SIMILARITY_THRESHOLD=0.6
RAG_TOP_K_RESULTS=8
RAG_CHUNK_SIZE=1500
```

#### For Memory Efficiency
```bash
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_CHUNK_SIZE=750
RAG_CHUNK_OVERLAP=50
RAG_TOP_K_RESULTS=3
```

### Use Case Specific Configurations

#### Customer Support Knowledge Base
```bash
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_SIMILARITY_THRESHOLD=0.65
RAG_TOP_K_RESULTS=5
RAG_CHUNK_SIZE=800
RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx,.html,.md
```

#### Technical Documentation
```bash
RAG_EMBEDDING_MODEL=all-mpnet-base-v2
RAG_SIMILARITY_THRESHOLD=0.75
RAG_TOP_K_RESULTS=7
RAG_CHUNK_SIZE=1200
RAG_CHUNK_OVERLAP=150
RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx,.html,.md
```

#### Legal Documents
```bash
RAG_EMBEDDING_MODEL=all-mpnet-base-v2
RAG_SIMILARITY_THRESHOLD=0.8
RAG_TOP_K_RESULTS=10
RAG_CHUNK_SIZE=2000
RAG_CHUNK_OVERLAP=200
RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx
```

## Configuration Validation

### Validating Your Configuration

You can validate your configuration by running this diagnostic script:

```python
# config_validator.py
import os
from rag_component.config import *

def validate_config():
    print("Validating RAG Configuration...")
    
    # Check required values
    assert isinstance(RAG_ENABLED, bool), "RAG_ENABLED must be boolean"
    assert isinstance(RAG_TOP_K_RESULTS, int) and RAG_TOP_K_RESULTS > 0, "RAG_TOP_K_RESULTS must be positive integer"
    assert 0.0 <= RAG_SIMILARITY_THRESHOLD <= 1.0, "RAG_SIMILARITY_THRESHOLD must be between 0.0 and 1.0"
    assert isinstance(RAG_CHUNK_SIZE, int) and RAG_CHUNK_SIZE > 0, "RAG_CHUNK_SIZE must be positive integer"
    assert isinstance(RAG_CHUNK_OVERLAP, int) and RAG_CHUNK_OVERLAP >= 0, "RAG_CHUNK_OVERLAP must be non-negative integer"
    
    print("✓ Basic validation passed")
    
    # Check embedding model availability (basic check)
    if RAG_EMBEDDING_MODEL.startswith("text-embedding"):
        print("⚠ Using OpenAI embedding model - ensure API key is configured")
    else:
        print("✓ Using local embedding model")
    
    # Check file types
    for ext in RAG_SUPPORTED_FILE_TYPES:
        if not ext.startswith('.'):
            print(f"⚠ File extension '{ext}' should start with a dot")
    
    print(f"✓ Configuration summary:")
    print(f"  - Enabled: {RAG_ENABLED}")
    print(f"  - Model: {RAG_EMBEDDING_MODEL}")
    print(f"  - Top-K: {RAG_TOP_K_RESULTS}")
    print(f"  - Threshold: {RAG_SIMILARITY_THRESHOLD}")
    print(f"  - Chunk size: {RAG_CHUNK_SIZE}")
    print(f"  - Chunk overlap: {RAG_CHUNK_OVERLAP}")
    print(f"  - Supported types: {','.join(RAG_SUPPORTED_FILE_TYPES)}")

if __name__ == "__main__":
    validate_config()
```

## Migration Guide

### From Earlier Versions

If upgrading from an earlier version of the RAG component:

1. **Check deprecated settings:**
   - Old: `VECTOR_DB_PATH` → New: `RAG_CHROMA_PERSIST_DIR`
   - Old: `EMBEDDING_MODEL` → New: `RAG_EMBEDDING_MODEL`

2. **Update your .env file** with the new variable names

3. **Review default values** as they may have changed

## Troubleshooting Configuration Issues

### Common Configuration Problems

#### Problem: Configuration not taking effect
**Cause:** Environment variables not loaded properly
**Solution:** Ensure `load_dotenv()` is called before importing RAG components

#### Problem: Invalid value errors
**Cause:** Incorrect data types in environment variables
**Solution:** Check that numeric values are actually numbers, booleans are true/false (not "true"/"false")

#### Problem: Performance issues
**Cause:** Suboptimal configuration for your use case
**Solution:** Refer to the best practices section above

## Default Configuration File Template

Create a `.env` file with these defaults:

```bash
# RAG Configuration
RAG_ENABLED=true
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_VECTOR_STORE_TYPE=chroma
RAG_TOP_K_RESULTS=5
RAG_SIMILARITY_THRESHOLD=0.7
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=100
RAG_CHROMA_PERSIST_DIR=./data/chroma_db
RAG_COLLECTION_NAME=documents
RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx,.html,.md
```

## Testing Your Configuration

After setting up your configuration, test it with:

```python
from rag_component import RAGOrchestrator
from models.response_generator import ResponseGenerator
import os

def test_config():
    try:
        # Initialize with your configured LLM
        response_gen = ResponseGenerator()
        llm = response_gen._get_llm_instance(
            provider=os.getenv("RESPONSE_LLM_PROVIDER", "LM Studio"),
            model=os.getenv("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
        )
        
        # Create orchestrator
        rag = RAGOrchestrator(llm=llm)
        
        # Test basic functionality
        print("✓ RAG component initialized successfully")
        
        # Test embedding
        test_text = "This is a test"
        embedding = rag.embedding_manager.embed_text(test_text)
        print(f"✓ Embedding created successfully, dimension: {len(embedding)}")
        
        # Test vector store
        results = rag.vector_store_manager.similarity_search("test query", top_k=1)
        print(f"✓ Vector store search works, found {len(results)} results")
        
        print("✓ Configuration test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    test_config()
```
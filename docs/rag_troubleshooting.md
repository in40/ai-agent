# RAG Component Troubleshooting Guide

This guide covers common issues you might encounter when using the RAG component and their solutions.

## Installation Issues

### ModuleNotFoundError: No module named 'langchain_chroma'

**Problem:** The RAG component fails to import due to missing dependencies.

**Solution:**
```bash
pip install langchain-chroma
```

### Could not import sentence_transformers

**Problem:** Error when trying to use embedding functionality.

**Solution:**
```bash
pip install sentence-transformers
```

### Missing HuggingFace Embeddings

**Problem:** Warning about deprecated HuggingFaceEmbeddings.

**Solution:** Install the updated package:
```bash
pip install langchain-huggingface
```

## Document Ingestion Issues

### Out of Memory Error During Document Loading

**Problem:** Large documents cause memory errors during ingestion.

**Solutions:**
1. Reduce chunk size in your configuration:
   ```
   RAG_CHUNK_SIZE=500
   ```

2. Process documents in smaller batches:
   ```python
   # Instead of ingesting all at once
   rag_orchestrator.ingest_documents(['doc1.pdf', 'doc2.pdf'])  # Process in smaller groups
   
   # Rather than
   rag_orchestrator.ingest_documents(large_list_of_docs)  # This might cause memory issues
   ```

3. Use a more memory-efficient embedding model:
   ```
   RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```

### Unsupported File Type Error

**Problem:** Document loader rejects certain file formats.

**Solutions:**
1. Check your configuration:
   ```
   RAG_SUPPORTED_FILE_TYPES=.txt,.pdf,.docx,.html,.md
   ```

2. Convert unsupported files to supported formats (PDF, DOCX, TXT, HTML, MD)

### Document Content Extraction Issues

**Problem:** PDFs or DOCX files don't extract text properly.

**Solutions:**
1. For PDFs, try different extraction methods:
   ```python
   # In document_loader.py, you might need to update the loader
   from langchain_community.document_loaders import PyPDFLoader
   
   # Use different parameters if needed
   loader = PyPDFLoader(file_path, extract_images=False)  # Disable image extraction if causing issues
   ```

2. For scanned PDFs, OCR might be needed (requires additional setup)

## Query and Retrieval Issues

### No Relevant Documents Found

**Problem:** Queries return no results even when documents should match.

**Solutions:**
1. Lower the similarity threshold:
   ```
   RAG_SIMILARITY_THRESHOLD=0.5
   ```

2. Increase the number of results retrieved:
   ```
   RAG_TOP_K_RESULTS=10
   ```

3. Check if documents were properly ingested by verifying the vector store has entries

### Poor Quality Results

**Problem:** Retrieved documents are not relevant to the query.

**Solutions:**
1. Try a different embedding model:
   ```
   RAG_EMBEDDING_MODEL=all-mpnet-base-v2  # Higher quality but slower
   ```

2. Increase the similarity threshold to get more precise matches:
   ```
   RAG_SIMILARITY_THRESHOLD=0.8
   ```

3. Adjust chunk size to provide more context:
   ```
   RAG_CHUNK_SIZE=2000
   ```

### Slow Query Response Times

**Problem:** Queries take too long to return results.

**Solutions:**
1. Use a faster embedding model:
   ```
   RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```

2. Reduce the number of results retrieved:
   ```
   RAG_TOP_K_RESULTS=3
   ```

3. Use Maximal Marginal Relevance (MMR) for faster diversity:
   ```python
   # In your retriever call
   results = rag_orchestrator.retrieve_documents(query, use_mmr=True)
   ```

## Integration Issues

### RAG Not Being Used in Agent Workflow

**Problem:** The AI agent continues to use SQL path instead of RAG.

**Solutions:**
1. Verify RAG is enabled:
   ```
   RAG_ENABLED=true
   ```

2. Check that your query doesn't contain SQL keywords that trigger the SQL path:
   - Words like "database", "table", "column", "query", "select", "from", "where", etc.
   - The system may classify these as SQL-related and skip RAG

3. Force RAG usage by structuring queries to avoid SQL terminology

### Agent Returns SQL Error Instead of Using RAG

**Problem:** Agent tries to generate SQL even for document-based queries.

**Solutions:**
1. Review the heuristic in `check_rag_applicability_node` in `langgraph_agent.py`
2. Modify the SQL keyword detection if needed for your use case
3. Ensure your query doesn't contain terms that trigger SQL path

## Performance Issues

### High Memory Usage

**Problem:** Application consumes too much memory after document ingestion.

**Solutions:**
1. Reduce the embedding model size:
   ```
   RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smaller model
   ```

2. Decrease chunk overlap:
   ```
   RAG_CHUNK_OVERLAP=50  # Reduce from default 100
   ```

3. Use approximate nearest neighbor search if supported by your vector store

### Slow Document Ingestion

**Problem:** Adding documents takes a long time.

**Solutions:**
1. Process documents in batches rather than all at once
2. Use a faster embedding model during ingestion:
   ```
   RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```
3. Ensure your system has enough CPU/memory resources

## Configuration Issues

### Environment Variables Not Being Picked Up

**Problem:** Configuration changes in .env file don't take effect.

**Solutions:**
1. Restart your Python process after changing .env
2. Verify .env file is in the correct location (project root)
3. Check that python-dotenv is installed and working:
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()  # Make sure this is called
   print(os.getenv("RAG_ENABLED"))  # Verify the value
   ```

### Invalid Configuration Values

**Problem:** Configuration values cause errors.

**Solutions:**
1. Check that numeric values are valid:
   - `RAG_TOP_K_RESULTS` should be a positive integer
   - `RAG_SIMILARITY_THRESHOLD` should be between 0.0 and 1.0
   - `RAG_CHUNK_SIZE` should be a positive integer

2. Verify file paths exist:
   - `RAG_CHROMA_PERSIST_DIR` directory should exist or be creatable
   - File extensions in `RAG_SUPPORTED_FILE_TYPES` should start with '.'

## Debugging Tips

### Enable Detailed Logging

Add this to your script to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific RAG logging
from rag_component.config import RAG_ENABLED
print(f"RAG Enabled: {RAG_ENABLED}")
```

### Test Individual Components

Test each component separately to isolate issues:

```python
# Test document loading
from rag_component.document_loader import DocumentLoader
loader = DocumentLoader()
docs = loader.load_document("path/to/doc.pdf")
print(f"Loaded {len(docs)} document chunks")

# Test embedding
from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
embedding = emb_manager.embed_text("test")
print(f"Embedding dimension: {len(embedding)}")

# Test vector store
from rag_component.vector_store_manager import VectorStoreManager
vs_manager = VectorStoreManager()
results = vs_manager.similarity_search("test query", top_k=1)
print(f"Found {len(results)} results")
```

### Verify Vector Store Contents

Check if documents were properly stored:

```python
# This depends on your vector store implementation
# For Chroma, you can check collection stats
from rag_component.vector_store_manager import VectorStoreManager
vs_manager = VectorStoreManager()

# If using Chroma, you can access the client directly
if hasattr(vs_manager, 'vector_store') and hasattr(vs_manager.vector_store, 'client'):
    collection = vs_manager.vector_store.client.get_collection(name=vs_manager.collection_name)
    count = collection.count()
    print(f"Vector store contains {count} documents")
```

## Common Error Messages and Solutions

### "CUDA out of memory" Error
- Solution: Use CPU instead of GPU, or reduce batch size/chunk size

### "Connection refused" for vector store
- Solution: Ensure your vector database service is running

### "Tokenizer error" during embedding
- Solution: Update transformers and tokenizers packages:
  ```bash
  pip install --upgrade transformers tokenizers
  ```

### "Invalid parameter" error from vector store
- Solution: Check that your configuration values are valid for your vector store type

## When to Seek Further Help

If you've tried the above solutions and still have issues:

1. Check the logs for specific error messages
2. Verify your Python environment and dependencies
3. Ensure you're using compatible versions of all packages
4. Consult the full documentation in `docs/rag_complete_documentation.md`
5. Consider reaching out to the development team with specific error messages and your configuration
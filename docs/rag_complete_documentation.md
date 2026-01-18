# RAG Component Complete Documentation Pack

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation Guide](#installation-guide)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Configuration Guide](#configuration-guide)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)

## Overview

The RAG (Retrieval-Augmented Generation) component enhances the AI agent by allowing it to retrieve and utilize external documents to supplement its responses. This is particularly useful when database queries are insufficient or inappropriate for answering user requests.

### Key Features
- Support for multiple document formats (PDF, DOCX, TXT, HTML, MD)
- Vector storage and similarity search capabilities
- Seamless integration with existing LangGraph workflow
- Configurable embedding models and vector stores
- Automatic fallback to traditional SQL approach when appropriate

## Architecture

The RAG component consists of several interconnected modules:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   User Query    │───▶│ RAG Applicability│───▶│ Document Retrieval  │
└─────────────────┘    │     Node         │    │      Node           │
                      └──────────────────┘    └─────────────────────┘
                                                     │
┌─────────────────┐    ┌──────────────────┐         ▼
│   SQL Path      │◀───│   Fallback       │    ┌─────────────────────┐
│ (Traditional)   │    │                  │───▶│ Context Augmentation│
└─────────────────┘    │ Decision Logic   │    │      Node           │
                       └──────────────────┘    └─────────────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────────┐
                                            │  Response Generation│
                                            │      Node           │
                                            └─────────────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────────┐
                                            │   Final Response    │
                                            └─────────────────────┘
```

### Components

#### 1. Document Loader (`rag_component/document_loader.py`)
- Handles loading and preprocessing of various document types
- Supports recursive loading from directories
- Uses LangChain's document loaders for different file formats

#### 2. Embedding Manager (`rag_component/embedding_manager.py`)
- Manages text embeddings using various models
- Supports both HuggingFace and OpenAI embedding models
- Provides consistent interface for embedding operations

#### 3. Vector Store Manager (`rag_component/vector_store_manager.py`)
- Handles storage and retrieval of document embeddings
- Supports ChromaDB as the primary vector store
- Provides similarity search and MMR (Maximal Marginal Relevance) search

#### 4. Retriever (`rag_component/retriever.py`)
- Retrieves relevant documents based on user queries
- Formats documents for use in the RAG pipeline
- Applies relevance thresholds to filter results

#### 5. RAG Chain (`rag_component/rag_chain.py`)
- Combines retrieved documents with user queries to generate responses
- Uses a specialized prompt template for RAG
- Integrates with the language model for response generation

#### 6. Main Orchestrator (`rag_component/main.py`)
- Coordinates all RAG components
- Provides a unified interface for RAG operations
- Handles document ingestion and query processing

## Installation Guide

### Prerequisites
- Python 3.9+
- Pip package manager
- Access to the AI agent codebase

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

The RAG component requires these additional dependencies:
- `chromadb==0.6.3`
- `sentence-transformers==3.2.1`
- `unstructured==0.16.1`
- `pypdf==5.1.0`
- `langchain-huggingface==0.1.2`

### Step 2: Verify Installation
```bash
python -c "import rag_component; print('RAG component imported successfully')"
```

## Step-by-Step Setup

### Step 1: Prepare Your Documents
Before using the RAG component, prepare the documents you want to make searchable:

1. Organize your documents in a directory
2. Ensure they are in supported formats:
   - Plain text (.txt)
   - PDF (.pdf)
   - Microsoft Word (.docx)
   - HTML (.html)
   - Markdown (.md)

### Step 2: Configure Environment Variables
Create or update your `.env` file with RAG-specific settings:

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

### Step 3: Initialize the RAG Component
```python
from rag_component import RAGOrchestrator
from models.response_generator import ResponseGenerator
import os

# Get the response generator's LLM instance
response_gen = ResponseGenerator()
llm = response_gen._get_llm_instance(
    provider=os.getenv("RESPONSE_LLM_PROVIDER", "LM Studio"),
    model=os.getenv("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
)

# Initialize RAG orchestrator
rag_orchestrator = RAGOrchestrator(llm=llm)
```

### Step 4: Ingest Your Documents
```python
# Ingest individual documents
success = rag_orchestrator.ingest_documents([
    "path/to/document1.pdf",
    "path/to/document2.txt",
    "path/to/document3.docx"
])

# Or ingest all documents from a directory
success = rag_orchestrator.ingest_documents_from_directory("path/to/documents/")
```

### Step 5: Test the RAG Component
```python
# Process a query using RAG
result = rag_orchestrator.query("What does the document say about artificial intelligence?")
print(result['response'])
```

### Step 6: Integrate with the AI Agent
The RAG component is automatically integrated with the main AI agent workflow. When you run the agent:

```python
from langgraph_agent.langgraph_agent import run_enhanced_agent

# The agent will automatically use RAG when appropriate
result = run_enhanced_agent("Your question that might require document knowledge")
```

## Configuration Guide

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `RAG_ENABLED` | Enable or disable RAG functionality | `true` |
| `RAG_EMBEDDING_MODEL` | Model to use for embeddings | `all-MiniLM-L6-v2` |
| `RAG_VECTOR_STORE_TYPE` | Type of vector store to use | `chroma` |
| `RAG_TOP_K_RESULTS` | Number of results to retrieve | `5` |
| `RAG_SIMILARITY_THRESHOLD` | Minimum similarity threshold | `0.7` |
| `RAG_CHUNK_SIZE` | Size of text chunks | `1000` |
| `RAG_CHUNK_OVERLAP` | Overlap between chunks | `100` |
| `RAG_CHROMA_PERSIST_DIR` | Directory for Chroma persistence | `./data/chroma_db` |
| `RAG_COLLECTION_NAME` | Name of the Chroma collection | `documents` |
| `RAG_SUPPORTED_FILE_TYPES` | Supported file types | `.txt,.pdf,.docx,.html,.md` |

### Choosing the Right Embedding Model

For local deployment, consider:
- `all-MiniLM-L6-v2`: Good balance of speed and quality
- `all-mpnet-base-v2`: Higher quality but slower
- `multi-qa-mpnet-base-dot-v1`: Optimized for question answering

For cloud deployment with OpenAI:
- `text-embedding-ada-002`: High quality, paid service

### Setting Similarity Threshold

- Lower threshold (0.5-0.6): More results, potentially less relevant
- Medium threshold (0.6-0.8): Balanced approach
- Higher threshold (0.8-0.9): Fewer but more relevant results

## Usage Examples

### Example 1: Simple Document Query
```python
from rag_component import RAGOrchestrator
from models.response_generator import ResponseGenerator
import os

# Initialize RAG orchestrator
response_gen = ResponseGenerator()
llm = response_gen._get_llm_instance(
    provider=os.getenv("RESPONSE_LLM_PROVIDER", "LM Studio"),
    model=os.getenv("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
)

rag_orchestrator = RAGOrchestrator(llm=llm)

# Ingest documents
rag_orchestrator.ingest_documents(["company_handbook.pdf"])

# Query the documents
result = rag_orchestrator.query("What is the company policy on remote work?")
print(result['response'])
```

### Example 2: Directory-Based Document Loading
```python
# Load all supported documents from a directory
rag_orchestrator.ingest_documents_from_directory("./knowledge_base/")

# Query with context from multiple documents
result = rag_orchestrator.query("Summarize the key points about customer service?")
print(result['response'])
```

### Example 3: Manual Document Processing
```python
# Process documents without automatic ingestion
docs = rag_orchestrator.retrieve_documents("customer complaints trends", top_k=3)

# Display retrieved documents
for i, doc in enumerate(docs):
    print(f"Document {i+1}:")
    print(f"Content: {doc['content'][:200]}...")
    print(f"Score: {doc['score']}")
    print("---")
```

### Example 4: Updating LLM Dynamically
```python
# Switch to a different LLM for RAG operations
from models.response_generator import ResponseGenerator
import os

new_response_gen = ResponseGenerator()
new_llm = new_response_gen._get_llm_instance(
    provider="OpenAI",
    model="gpt-4-turbo"
)

rag_orchestrator.update_llm(new_llm)

# Now queries will use the new LLM
result = rag_orchestrator.query("Analyze this technical document")
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: ModuleNotFoundError: No module named 'langchain_chroma'
**Solution:** Install the required dependency:
```bash
pip install langchain-chroma
```

#### Issue: Could not import sentence_transformers
**Solution:** Install the required dependency:
```bash
pip install sentence-transformers
```

#### Issue: Out of Memory Error During Document Ingestion
**Solution:** 
1. Reduce the chunk size in your configuration:
   ```
   RAG_CHUNK_SIZE=500
   ```
2. Process documents in smaller batches
3. Use a more memory-efficient embedding model

#### Issue: Slow Query Response Times
**Solution:**
1. Use a faster embedding model (e.g., all-MiniLM-L6-v2)
2. Reduce the number of results retrieved (RAG_TOP_K_RESULTS)
3. Increase the similarity threshold to reduce irrelevant results

#### Issue: Poor Quality Results
**Solution:**
1. Try a higher-quality embedding model (e.g., all-mpnet-base-v2)
2. Adjust the similarity threshold lower (e.g., 0.5)
3. Increase the chunk size to provide more context

### Debugging Tips

1. Enable logging to see what's happening:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

2. Check if documents were properly ingested:
```python
# Check the number of documents in the vector store
# This depends on your vector store implementation
```

3. Verify the configuration:
```python
from rag_component.config import *
print(f"RAG Enabled: {RAG_ENABLED}")
print(f"Embedding Model: {RAG_EMBEDDING_MODEL}")
print(f"Top K: {RAG_TOP_K_RESULTS}")
```

## Best Practices

### Document Preparation
- Use clear, descriptive titles and headings in your documents
- Structure documents logically with sections
- Remove unnecessary formatting that might interfere with text extraction
- Keep documents up-to-date

### Performance Optimization
- Use appropriate chunk sizes (1000-2000 tokens typically work well)
- Set overlap to capture context across chunk boundaries (100-200 tokens)
- Choose embedding models based on your quality vs. speed requirements
- Monitor vector store size and consider archiving old documents

### Quality Assurance
- Regularly review the quality of retrieved documents
- Adjust similarity thresholds based on your content type
- Test with various query types to ensure robustness
- Monitor for hallucinations when using retrieved context

### Security Considerations
- Validate document sources before ingestion
- Consider data privacy implications
- Implement access controls if needed
- Sanitize retrieved content before passing to LLMs

## API Reference

### RAGOrchestrator Class

#### Constructor
```python
def __init__(self, llm=None):
    """
    Initialize the RAG orchestrator.
    
    Args:
        llm: Language model to use for generation (will be passed to RAGChain)
    """
```

#### Methods

##### `ingest_documents(file_paths, preprocess=True)`
Ingest documents into the vector store.

Parameters:
- `file_paths`: List of file paths to ingest
- `preprocess`: Whether to split documents into chunks (default: True)

Returns: `True` if ingestion was successful

##### `ingest_documents_from_directory(directory_path, preprocess=True)`
Ingest all supported documents from a directory.

Parameters:
- `directory_path`: Path to directory containing documents
- `preprocess`: Whether to split documents into chunks (default: True)

Returns: `True` if ingestion was successful

##### `query(user_query)`
Process a user query using the RAG pipeline.

Parameters:
- `user_query`: User's natural language query

Returns: Dictionary containing response and relevant context

##### `retrieve_documents(query, top_k=None)`
Retrieve relevant documents for a query without generating a response.

Parameters:
- `query`: Query to search for
- `top_k`: Number of top results to return (uses default if not provided)

Returns: List of relevant documents with metadata and scores

##### `update_llm(llm)`
Update the language model used by the RAG chain.

Parameters:
- `llm`: New language model instance

### Configuration Module

#### Available Configuration Options
- `RAG_ENABLED`: Enable or disable RAG functionality
- `RAG_EMBEDDING_MODEL`: Model to use for embeddings
- `RAG_VECTOR_STORE_TYPE`: Type of vector store to use
- `RAG_TOP_K_RESULTS`: Number of results to retrieve
- `RAG_SIMILARITY_THRESHOLD`: Minimum similarity threshold
- `RAG_CHUNK_SIZE`: Size of text chunks
- `RAG_CHUNK_OVERLAP`: Overlap between chunks
- `RAG_CHROMA_PERSIST_DIR`: Directory for Chroma persistence
- `RAG_COLLECTION_NAME`: Name of the Chroma collection
- `RAG_SUPPORTED_FILE_TYPES`: Supported file types

### LangGraph Integration

#### New State Fields
- `rag_documents`: List of retrieved documents from RAG
- `rag_context`: Augmented context with retrieved documents
- `use_rag_flag`: Boolean indicating whether to use RAG for this request
- `rag_relevance_score`: Average relevance score of retrieved documents
- `rag_query`: The query used for document retrieval
- `rag_response`: Response generated using RAG

#### New Nodes
- `check_rag_applicability_node`: Determines if RAG is appropriate for the user request
- `retrieve_documents_node`: Retrieves relevant documents using the RAG component
- `augment_context_node`: Augments the user request with retrieved documents for RAG
- `generate_rag_response_node`: Generates a response using the RAG-augmented context

#### Conditional Logic
- `should_use_rag`: Determines whether to use RAG or traditional SQL approach
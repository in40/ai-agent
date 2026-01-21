# RAG (Retrieval-Augmented Generation) Component Documentation

## Overview
The RAG (Retrieval-Augmented Generation) component enhances the AI agent by allowing it to retrieve and utilize external documents to supplement its responses, particularly when database queries are insufficient or inappropriate.

## Components

### 1. Main Orchestrator (`rag_component/main.py`)
- `RAGOrchestrator`: Coordinates all RAG components and provides a unified interface
- Initializes and manages all other RAG components

### 2. Configuration (`rag_component/config.py`)
- Handles environment variables and settings specific to RAG functionality
- Key settings include:
  - `RAG_ENABLED`: Enable/disable RAG functionality
  - `RAG_EMBEDDING_MODEL`: Model to use for embeddings (default: all-MiniLM-L6-v2)
  - `RAG_VECTOR_STORE_TYPE`: Type of vector store to use (default: chroma)
  - `RAG_TOP_K_RESULTS`: Number of results to retrieve (default: 5)
  - `RAG_SIMILARITY_THRESHOLD`: Minimum similarity threshold (default: 0.7)
  - `RAG_CHUNK_SIZE`: Size of text chunks (default: 1000)
  - `RAG_CHUNK_OVERLAP`: Overlap between chunks (default: 100)

### 3. Document Loader (`rag_component/document_loader.py`)
- `DocumentLoader`: Loads documents of various types (TXT, PDF, DOCX, HTML, MD)
- Handles different file formats with appropriate loaders

### 4. Embedding Manager (`rag_component/embedding_manager.py`)
- `EmbeddingManager`: Manages text embeddings using various models
- Supports both OpenAI and HuggingFace embedding models

### 5. Vector Store Manager (`rag_component/vector_store_manager.py`)
- `VectorStoreManager`: Handles storage and retrieval of document embeddings
- Supports Chroma as the primary vector store

### 6. Retriever (`rag_component/retriever.py`)
- `Retriever`: Retrieves relevant documents based on user queries
- Implements similarity search and MMR (Maximal Marginal Relevance) search

### 7. RAG Chain (`rag_component/rag_chain.py`)
- `RAGChain`: Combines retrieved documents with user queries to generate responses
- Creates the RAG processing chain using LangChain components

## Integration with Main Agent

### Agent State Extensions
The `AgentState` has been extended with RAG-specific fields:
- `rag_documents`: List of retrieved documents from RAG
- `rag_context`: Augmented context with retrieved documents
- `use_rag_flag`: Whether to use RAG for this request
- `rag_relevance_score`: Relevance score of retrieved documents
- `rag_query`: The query used for document retrieval
- `rag_response`: Response generated using RAG

### LangGraph Workflow Integration
The main LangGraph workflow includes these RAG-related nodes:
- `check_rag_applicability_node`: Determines if RAG is appropriate for the request
- `retrieve_documents_node`: Retrieves relevant documents using the RAG component
- `augment_context_node`: Combines retrieved documents with user query
- `generate_rag_response_node`: Generates the final response using RAG-augmented context

Conditional logic routes requests appropriately between RAG and traditional SQL approaches.

## Setup and Usage

### Environment Variables
Configure RAG functionality using these environment variables in your `.env` file:
```
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

### Basic Usage Example
```python
from rag_component import RAGOrchestrator
from models.response_generator import ResponseGenerator

# Initialize the response generator to get the LLM
response_gen = ResponseGenerator()
llm = response_gen.llm  # Access the LLM directly from the response generator

# Initialize the RAG orchestrator
rag_orchestrator = RAGOrchestrator(llm=llm)

# Ingest documents from a directory
success = rag_orchestrator.ingest_documents_from_directory("./my_documents/")

if success:
    # Process a query using RAG
    result = rag_orchestrator.query("What does the document say about X?")
    print(result['response'])
    print(f"Retrieved {len(result['context'])} documents")
```

## Dependencies
- `chromadb`: For vector storage
- `sentence-transformers`: For text embeddings
- `pypdf`: For PDF processing
- `unstructured`: For document preprocessing
- `langchain-chroma`: For LangChain integration with Chroma

## Troubleshooting

### Common Issues
1. **Model Downloading**: The first run may take longer as embedding models are downloaded
2. **Memory Usage**: Large documents or many embeddings may require significant memory
3. **Similarity Threshold**: Adjust `RAG_SIMILARITY_THRESHOLD` based on your content

### Performance Tips
1. Use lighter embedding models for faster processing
2. Adjust `RAG_TOP_K_RESULTS` to balance between thoroughness and speed
3. Tune `RAG_CHUNK_SIZE` based on your document types and query patterns
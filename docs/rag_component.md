# RAG (Retrieval-Augmented Generation) Component Documentation

## Overview

The RAG component enhances the AI agent by allowing it to retrieve and utilize external documents to supplement its responses, particularly when database queries are insufficient or inappropriate. This component integrates seamlessly with the existing LangGraph-based workflow.

## Architecture

The RAG component consists of five main modules:

### 1. Document Loader (`document_loader.py`)
- Handles loading and preprocessing of various document types (PDF, DOCX, TXT, HTML, MD)
- Supports recursive loading from directories
- Uses LangChain's document loaders for different file formats

### 2. Embedding Manager (`embedding_manager.py`)
- Manages text embeddings using various models
- Supports both HuggingFace and OpenAI embedding models
- Provides consistent interface for embedding operations

### 3. Vector Store Manager (`vector_store_manager.py`)
- Handles storage and retrieval of document embeddings
- Supports ChromaDB as the primary vector store
- Provides similarity search and MMR (Maximal Marginal Relevance) search

### 4. Retriever (`retriever.py`)
- Retrieves relevant documents based on user queries
- Formats documents for use in the RAG pipeline
- Applies relevance thresholds to filter results

### 5. RAG Chain (`rag_chain.py`)
- Combines retrieved documents with user queries to generate responses
- Uses a specialized prompt template for RAG
- Integrates with the language model for response generation

### 6. Main Orchestrator (`main.py`)
- Coordinates all RAG components
- Provides a unified interface for RAG operations
- Handles document ingestion and query processing

## Integration with LangGraph

The RAG component integrates with the existing LangGraph workflow through four new nodes:

### 1. `check_rag_applicability_node`
- Determines if RAG is appropriate for the user request
- Uses heuristics to decide between RAG and SQL approaches
- Updates the state with the `use_rag_flag`

### 2. `retrieve_documents_node`
- Retrieves relevant documents using the RAG component
- Updates the state with retrieved documents and relevance scores

### 3. `augment_context_node`
- Combines retrieved documents with the user request
- Creates an augmented context for response generation

### 4. `generate_rag_response_node`
- Generates a response using the RAG-augmented context
- Sets the final response in the state

## State Management

The RAG component extends the `AgentState` with the following fields:

- `rag_documents`: List of retrieved documents from RAG
- `rag_context`: Augmented context with retrieved documents
- `use_rag_flag`: Boolean indicating whether to use RAG for this request
- `rag_relevance_score`: Average relevance score of retrieved documents
- `rag_query`: The query used for document retrieval
- `rag_response`: Response generated using RAG

## Configuration

The RAG component is configured through environment variables:

- `RAG_ENABLED`: Enable or disable RAG functionality (default: true)
- `RAG_EMBEDDING_MODEL`: Model to use for embeddings (default: all-MiniLM-L6-v2)
- `RAG_VECTOR_STORE_TYPE`: Type of vector store to use (default: chroma)
- `RAG_TOP_K_RESULTS`: Number of results to retrieve (default: 5)
- `RAG_SIMILARITY_THRESHOLD`: Minimum similarity threshold (default: 0.7)
- `RAG_CHUNK_SIZE`: Size of text chunks (default: 1000)
- `RAG_CHUNK_OVERLAP`: Overlap between chunks (default: 100)
- `RAG_CHROMA_PERSIST_DIR`: Directory for Chroma persistence (default: ./data/chroma_db)
- `RAG_COLLECTION_NAME`: Name of the Chroma collection (default: documents)
- `RAG_SUPPORTED_FILE_TYPES`: Supported file types (default: .txt,.pdf,.docx,.html,.md)

## Usage

### Document Ingestion

Documents can be ingested using the RAG orchestrator:

```python
from rag_component import RAGOrchestrator

# Initialize the orchestrator with an LLM
rag_orchestrator = RAGOrchestrator(llm=your_llm_instance)

# Ingest individual documents
success = rag_orchestrator.ingest_documents(["path/to/doc1.pdf", "path/to/doc2.txt"])

# Ingest all documents from a directory
success = rag_orchestrator.ingest_documents_from_directory("path/to/documents/")
```

### Query Processing

The RAG component automatically integrates with the main agent workflow. When a user request is processed:

1. The `check_rag_applicability_node` determines if RAG is appropriate
2. If RAG is selected, documents are retrieved and the context is augmented
3. A response is generated using the augmented context
4. The response is returned to the user

## Dependencies

The RAG component requires the following additional dependencies:

- `chromadb`: For vector storage and retrieval
- `sentence-transformers`: For text embeddings
- `unstructured`: For document preprocessing
- `pypdf`: For PDF processing
- `langchain-huggingface`: For HuggingFace embeddings integration

## Error Handling

The RAG component includes comprehensive error handling:

- If RAG components fail to initialize, the system falls back to the traditional SQL workflow
- If document retrieval fails, an empty document list is returned
- If response generation fails, an error message is returned to the user
- All operations are logged for debugging purposes

## Performance Considerations

- Document ingestion happens offline and is stored in the vector database
- Query processing involves embedding the query and searching the vector store
- The system caches embeddings to improve performance
- Relevance thresholds help filter out low-quality results
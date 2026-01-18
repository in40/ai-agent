# RAG Component Quick Start Guide

This guide will walk you through setting up and using the RAG (Retrieval-Augmented Generation) component in just a few minutes.

## Prerequisites

- Python 3.9+
- The AI agent codebase installed and running
- Documents you want to make searchable (PDF, DOCX, TXT, HTML, or MD format)

## Step 1: Install Dependencies

First, make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

This will install the RAG-specific dependencies including:
- `chromadb` - for vector storage
- `sentence-transformers` - for text embeddings
- `pypdf` - for PDF processing
- `unstructured` - for document preprocessing

## Step 2: Configure RAG Settings

Create or update your `.env` file with these minimum settings:

```bash
# Enable RAG functionality
RAG_ENABLED=true

# Set the embedding model (default is fine for most cases)
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Set how many results to retrieve
RAG_TOP_K_RESULTS=5

# Set similarity threshold (0.0 to 1.0, higher = more similar)
RAG_SIMILARITY_THRESHOLD=0.7
```

## Step 3: Prepare Your Documents

Organize the documents you want to make searchable in a directory. For example:

```
my_documents/
├── handbook.pdf
├── policies.docx
├── faqs.txt
└── guides/
    ├── guide1.md
    └── guide2.html
```

## Step 4: Initialize and Ingest Documents

Create a Python script to initialize the RAG component and ingest your documents:

```python
# rag_setup.py
from rag_component import RAGOrchestrator
from models.response_generator import ResponseGenerator
import os

def setup_rag():
    # Initialize the response generator to get the LLM
    response_gen = ResponseGenerator()
    llm = response_gen._get_llm_instance(
        provider=os.getenv("RESPONSE_LLM_PROVIDER", "LM Studio"),
        model=os.getenv("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
    )
    
    # Initialize the RAG orchestrator
    rag_orchestrator = RAGOrchestrator(llm=llm)
    
    # Ingest documents from a directory
    success = rag_orchestrator.ingest_documents_from_directory("./my_documents/")
    
    if success:
        print("Documents ingested successfully!")
        return rag_orchestrator
    else:
        print("Failed to ingest documents")
        return None

if __name__ == "__main__":
    rag_orch = setup_rag()
    if rag_orch:
        # Test a sample query
        result = rag_orch.query("What is covered in the documents?")
        print("Sample response:", result['response'])
```

Run this script to ingest your documents:

```bash
python rag_setup.py
```

## Step 5: Query Your Documents

Once documents are ingested, you can query them:

```python
# query_documents.py
from rag_component import RAGOrchestrator
from models.response_generator import ResponseGenerator
import os

# Initialize the same way as in setup
response_gen = ResponseGenerator()
llm = response_gen._get_llm_instance(
    provider=os.getenv("RESPONSE_LLM_PROVIDER", "LM Studio"),
    model=os.getenv("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
)

rag_orchestrator = RAGOrchestrator(llm=llm)

# Ask a question about your documents
question = "What are the company policies?"
result = rag_orchestrator.query(question)

print("Response:", result['response'])
print("Retrieved documents:", len(result['context']))
```

## Step 6: Integrate with the AI Agent

The RAG component is automatically integrated with the main AI agent. When you run the agent, it will automatically use RAG when appropriate:

```python
from langgraph_agent.langgraph_agent import run_enhanced_agent

# This will automatically use RAG if the query is better suited for document retrieval
result = run_enhanced_agent("What does the employee handbook say about vacation time?")
print(result)
```

## Troubleshooting Quick Fixes

### Problem: ModuleNotFoundError for RAG components
**Solution:** Make sure you're running from the project root directory where the rag_component package is available.

### Problem: Out of memory during document ingestion
**Solution:** Reduce the chunk size in your .env file:
```
RAG_CHUNK_SIZE=500
```

### Problem: Slow responses
**Solution:** Use a lighter embedding model or reduce the number of results:
```
RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_TOP_K_RESULTS=3
```

### Problem: Poor quality results
**Solution:** Lower the similarity threshold to get more results:
```
RAG_SIMILARITY_THRESHOLD=0.5
```

## Next Steps

1. Experiment with different embedding models to find the best balance of quality and speed for your use case
2. Fine-tune the similarity threshold based on your content
3. Add more documents to your knowledge base
4. Explore the advanced configuration options in the full documentation

That's it! You now have a working RAG system that can answer questions based on your documents.
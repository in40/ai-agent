# Testing Document Ingestion in the RAG System

## Overview
This document explains how to verify that documents have been successfully ingested into the RAG (Retrieval-Augmented Generation) system.

## Methods to Test Document Ingestion

### Method 1: Direct Vector Store Verification (Recommended)
This is the quickest method that doesn't require downloading models:

```bash
cd /root/qwen_test/ai_agent
source ai_agent_env/bin/activate
python3 verify_ingestion.py
```

This script will:
- Connect to the vector store
- Count the number of documents
- Show sample document IDs
- Confirm successful ingestion

### Method 2: Using the Ingestion Script
To ingest new documents or re-ingest existing ones:

```bash
cd /root/qwen_test/ai_agent
./ingest_documents.sh
```

Options:
- `-d, --documents DIR`: Specify directory with documents (default: ./sample_documents)
- `-v, --venv PATH`: Specify virtual environment path (default: ./ai_agent_env)

### Method 3: Manual Verification
You can manually check if the vector store exists:

```bash
ls -la ./data/chroma_db/
```

Look for files like `chroma.sqlite3` which indicate the vector store has been created.

## Expected Results
- The vector store directory (`./data/chroma_db/`) should exist
- The vector store should contain document embeddings
- The verification script should report the number of documents found
- Document IDs should be displayed as proof of ingestion

## Troubleshooting
- If the vector store directory doesn't exist, documents haven't been ingested yet
- If the count is 0, try re-running the ingestion script
- Make sure the virtual environment is activated when running scripts
- Ensure the .env file has the correct model configuration

## Current Configuration
The system is configured to use the `qwen3-4b` model as specified in the .env file.
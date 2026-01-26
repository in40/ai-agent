#!/bin/bash

# Script to clean the vector database and remove all stored PDF and Markdown files

set -e  # Exit immediately if a command exits with a non-zero status

echo "Cleaning vector database and stored files..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to the rag_component directory
cd "$SCRIPT_DIR"

echo "Removing ChromaDB vector store..."
if [ -d "./data/chroma_db" ]; then
    rm -rf ./data/chroma_db
    echo "Removed ./data/chroma_db"
else
    echo "ChromaDB directory not found at ./data/chroma_db"
fi

echo "Removing stored PDF files..."
if [ -d "./data/rag_uploaded_files" ]; then
    rm -rf ./data/rag_uploaded_files
    echo "Removed ./data/rag_uploaded_files"
else
    echo "PDF storage directory not found at ./data/rag_uploaded_files"
fi

echo "Removing stored Markdown files..."
if [ -d "./data/rag_converted_markdown" ]; then
    rm -rf ./data/rag_converted_markdown
    echo "Removed ./data/rag_converted_markdown"
else
    echo "Markdown storage directory not found at ./data/rag_converted_markdown"
fi

echo "Creating fresh directories..."
mkdir -p ./data/chroma_db
mkdir -p ./data/rag_uploaded_files
mkdir -p ./data/rag_converted_markdown

echo "Cleanup complete!"
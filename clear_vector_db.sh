#!/bin/bash

# Script to clear the vector database by removing all documents
# This script calls the Python script that handles the actual clearing
# It also removes sub-directories for stored files

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/clear_vector_db.py"

echo "Clearing vector database and stored files..."
echo "Using Python script: $PYTHON_SCRIPT"

# Activate the virtual environment if it exists
if [ -f "$SCRIPT_DIR/ai_agent_env/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/ai_agent_env/bin/activate"
elif [ -f "$SCRIPT_DIR/../ai_agent_env/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/../ai_agent_env/bin/activate"
fi

# Run the Python script to clear the vector database
python "$PYTHON_SCRIPT"

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "✗ Failed to clear vector database. Exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi

# Also remove all data subdirectories
echo "Removing data subdirectories..."

DATA_DIR="$SCRIPT_DIR/data"

if [ -d "$DATA_DIR/chroma_db" ]; then
    rm -rf "$DATA_DIR/chroma_db"
    echo "Removed $DATA_DIR/chroma_db"
fi

if [ -d "$DATA_DIR/rag_uploaded_files" ]; then
    rm -rf "$DATA_DIR/rag_uploaded_files"
    echo "Removed $DATA_DIR/rag_uploaded_files"
fi

if [ -d "$DATA_DIR/rag_converted_markdown" ]; then
    rm -rf "$DATA_DIR/rag_converted_markdown"
    echo "Removed $DATA_DIR/rag_converted_markdown"
fi

# Also check for these directories in the rag_component subdirectory for completeness
RAG_COMPONENT_DIR="$SCRIPT_DIR/rag_component"

if [ -d "$RAG_COMPONENT_DIR/data/chroma_db" ]; then
    rm -rf "$RAG_COMPONENT_DIR/data/chroma_db"
    echo "Removed $RAG_COMPONENT_DIR/data/chroma_db"
fi

if [ -d "$RAG_COMPONENT_DIR/data/rag_uploaded_files" ]; then
    rm -rf "$RAG_COMPONENT_DIR/data/rag_uploaded_files"
    echo "Removed $RAG_COMPONENT_DIR/data/rag_uploaded_files"
fi

if [ -d "$RAG_COMPONENT_DIR/data/rag_converted_markdown" ]; then
    rm -rf "$RAG_COMPONENT_DIR/data/rag_converted_markdown"
    echo "Removed $RAG_COMPONENT_DIR/data/rag_converted_markdown"
fi

echo "✓ Vector database and stored files cleared successfully!"
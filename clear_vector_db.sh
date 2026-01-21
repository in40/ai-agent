#!/bin/bash

# Script to clear the vector database by removing all documents
# This script calls the Python script that handles the actual clearing

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/clear_vector_db.py"

echo "Clearing vector database..."
echo "Using Python script: $PYTHON_SCRIPT"

# Activate the virtual environment if it exists
if [ -f "$SCRIPT_DIR/ai_agent_env/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/ai_agent_env/bin/activate"
elif [ -f "$SCRIPT_DIR/../ai_agent_env/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/../ai_agent_env/bin/activate"
fi

# Run the Python script
python "$PYTHON_SCRIPT"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Vector database cleared successfully!"
else
    echo "✗ Failed to clear vector database. Exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi
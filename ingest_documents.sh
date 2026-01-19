#!/bin/bash

# RAG Document Ingestion Script
# This script initializes the RAG component and ingests documents from a specified directory

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_DOCUMENT_DIR="./sample_documents"
DEFAULT_VENV_PATH="./ai_agent_env"

# Print usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --documents DIR     Directory containing documents to ingest (default: $DEFAULT_DOCUMENT_DIR)"
    echo "  -v, --venv PATH       Path to Python virtual environment (default: $DEFAULT_VENV_PATH)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Environment:"
    echo "  This script expects a .env file in the current directory with RAG configuration"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use default settings"
    echo "  $0 -d /path/to/my/documents         # Specify document directory"
    echo "  $0 -v /custom/venv/path             # Specify virtual environment path"
}

# Parse command line arguments
DOCUMENT_DIR="$DEFAULT_DOCUMENT_DIR"
VENV_PATH="$DEFAULT_VENV_PATH"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--documents)
            DOCUMENT_DIR="$2"
            shift 2
            ;;
        -v|--venv)
            VENV_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

echo -e "${BLUE}RAG Document Ingestion Script${NC}"
echo "================================"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PATH${NC}" >&2
    echo "Please create the virtual environment first."
    exit 1
fi

# Check if documents directory exists
if [ ! -d "$DOCUMENT_DIR" ]; then
    echo -e "${RED}Error: Documents directory not found at $DOCUMENT_DIR${NC}" >&2
    echo "Please create the directory or specify a different one."
    exit 1
fi

# Count the number of documents
DOC_COUNT=$(find "$DOCUMENT_DIR" -type f \( -iname "*.txt" -o -iname "*.pdf" -o -iname "*.docx" -o -iname "*.html" -o -iname "*.md" \) | wc -l)
echo -e "${BLUE}Found $DOC_COUNT documents in $DOCUMENT_DIR${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found in current directory.${NC}"
    echo "Make sure RAG environment variables are properly configured."
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check if required modules are available
echo -e "${BLUE}Checking for required modules...${NC}"
python -c "import rag_component" || { echo -e "${RED}Error: rag_component module not found${NC}" >&2; exit 1; }
python -c "import langchain_chroma" || { echo -e "${RED}Error: langchain_chroma module not found${NC}" >&2; exit 1; }

# Create a temporary Python script for ingestion
TEMP_INGEST_SCRIPT=$(mktemp --suffix=.py)
cat > "$TEMP_INGEST_SCRIPT" << EOF
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the project root to the Python path
script_dir = Path(__file__).parent.absolute()  # Current directory where the project is located
sys.path.insert(0, str(script_dir))

# Also add the current directory to the Python path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def ingest_documents(doc_dir):
    """Ingest documents from the specified directory."""
    print("Starting document ingestion process...")

    try:
        # Import required modules
        from rag_component import RAGOrchestrator
        from models.response_generator import ResponseGenerator

        # Initialize the response generator to get the LLM
        response_gen = ResponseGenerator()
        llm = response_gen.llm  # Access the LLM directly from the response generator

        print("Initializing RAG orchestrator...")
        # Initialize the RAG orchestrator
        rag_orchestrator = RAGOrchestrator(llm=llm)

        print(f"Ingesting documents from: {doc_dir}")
        # Ingest documents from the specified directory
        success = rag_orchestrator.ingest_documents_from_directory(doc_dir)

        if success:
            print("✓ Documents ingested successfully!")
            return True
        else:
            print("✗ Failed to ingest documents")
            return False

    except Exception as e:
        print(f"✗ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Ingest documents into RAG system')
    parser.add_argument('doc_dir', help='Directory containing documents to ingest')
    args = parser.parse_args()

    success = ingest_documents(args.doc_dir)
    sys.exit(0 if success else 1)
EOF

# Run the ingestion process
echo -e "${BLUE}Starting document ingestion from $DOCUMENT_DIR...${NC}"
python "$TEMP_INGEST_SCRIPT" "$DOCUMENT_DIR"

INGESTION_STATUS=$?

# Clean up temporary script
rm "$TEMP_INGEST_SCRIPT"

if [ $INGESTION_STATUS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Document ingestion completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. You can now query the RAG system using the AI agent"
    echo "2. The documents are stored in the vector database and ready for retrieval"
else
    echo ""
    echo -e "${RED}✗ Document ingestion failed.${NC}"
    echo "Check the error messages above for details."
    exit 1
fi

deactivate
echo -e "${BLUE}Virtual environment deactivated.${NC}"
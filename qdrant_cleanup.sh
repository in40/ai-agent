#!/bin/bash

# Qdrant Cleanup Script
# Wrapper script for the Qdrant cleanup utility

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_SCRIPT="$SCRIPT_DIR/qdrant_cleanup.py"

# Default values
METHOD="collections"
DRY_RUN=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --method)
            METHOD="$2"
            shift 2
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --method METHOD    Method to use: 'collections' (default) or 'points'"
            echo "  --dry-run, -n      Show what would be deleted without actually deleting"
            echo "  --verbose, -v      Enable verbose logging"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  QDRANT_HOST        Qdrant host (default: localhost)"
            echo "  QDRANT_PORT        Qdrant port (default: 6333)"
            echo "  QDRANT_API_KEY     Qdrant API key (optional)"
            echo "  QDRANT_HTTPS       Use HTTPS (default: false)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set default environment variables if not already set
export QDRANT_HOST="${QDRANT_HOST:-localhost}"
export QDRANT_PORT="${QDRANT_PORT:-6333}"

echo "Qdrant Cleanup Script"
echo "====================="
echo "Host: $QDRANT_HOST"
echo "Port: $QDRANT_PORT"
echo "Method: $METHOD"
echo "Dry Run: $DRY_RUN"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "Performing dry run..."
    python3 "$CLEANUP_SCRIPT" --method "$METHOD" --dry-run ${VERBOSE:+--verbose}
else
    echo "Starting cleanup..."
    python3 "$CLEANUP_SCRIPT" --method "$METHOD" ${VERBOSE:+--verbose}
fi

echo ""
echo "Cleanup operation completed."
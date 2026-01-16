#!/bin/bash

# Script to execute setup utility and update .env file

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

echo "Running setup utility..."

# Execute the Python setup script from the project root to ensure proper module resolution
if [ -f "$SCRIPT_DIR/config/setup_config.py" ]; then
    echo "Found setup script at $SCRIPT_DIR/config/setup_config.py"
    cd "$SCRIPT_DIR"  # Change to the project root directory
    python3 config/setup_config.py
else
    echo "Setup script not found at $SCRIPT_DIR/config/setup_config.py"
    exit 1
fi

echo "Configuration complete!"
#!/bin/bash
#
# Recovery Script for Pre-Production Backup
# This script moves files back to their original locations
#

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         File Recovery Script                                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Confirm recovery
read -p "This will move files back to their original locations. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled."
    exit 0
fi

echo ""
echo "Starting recovery..."
echo ""


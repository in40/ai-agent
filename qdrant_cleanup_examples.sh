#!/bin/bash
# Quick start examples for Qdrant cleanup

echo "QDRANT CLEANUP UTILITY - QUICK START EXAMPLES"
echo "============================================"
echo

echo "1. Basic usage (assumes Qdrant is at localhost:6333 with no auth):"
echo "   ./qdrant_cleanup.sh"
echo

echo "2. With API key authentication:"
echo "   QDRANT_API_KEY=your_key_here ./qdrant_cleanup.sh"
echo

echo "3. With custom host and port:"
echo "   QDRANT_HOST=my-qdrant.example.com QDRANT_PORT=6333 ./qdrant_cleanup.sh"
echo

echo "4. Using full URL (for cloud instances):"
echo "   QDRANT_URL=https://cluster-id.region.cloud.qdrant.io:6333 QDRANT_API_KEY=your_key ./qdrant_cleanup.sh"
echo

echo "5. Dry run (see what would be deleted without actually deleting):"
echo "   ./qdrant_cleanup.sh --dry-run"
echo

echo "6. Verbose output:"
echo "   ./qdrant_cleanup.sh --verbose"
echo

echo "7. SSL configuration:"
echo "   # If using HTTPS"
echo "   QDRANT_HTTPS=true ./qdrant_cleanup.sh"
echo "   # If needing to disable SSL verification"
echo "   QDRANT_VERIFY_SSL=false ./qdrant_cleanup.sh"
echo

echo "8. API key with HTTP (important scenario):"
echo "   # If your Qdrant uses API key authentication over HTTP (not HTTPS)"
echo "   QDRANT_API_KEY=your_key QDRANT_HTTPS=false ./qdrant_cleanup.sh"
echo "   # This prevents SSL negotiation issues when using API key with HTTP"
echo

echo "9. Load configuration from file:"
echo "   source qdrant_cleanup_config.env && ./qdrant_cleanup.sh"
echo

echo "For more information, see QDRANT_CLEANUP_README.md"
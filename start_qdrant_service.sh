#!/bin/bash

# Script to start Qdrant service using Docker Compose

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Qdrant service..."
echo "Project directory: $SCRIPT_DIR"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed or not in PATH"
    echo "Please install Docker Compose first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "Error: Docker daemon is not running"
    echo "Please start Docker first."
    exit 1
fi

# Start Qdrant service
echo "Starting Qdrant service with Docker Compose..."
cd "$SCRIPT_DIR"
docker-compose up -d qdrant

# Wait a moment for the service to start
sleep 5

# Check if the Qdrant container is running
if docker ps | grep -q qdrant; then
    echo "✓ Qdrant service started successfully!"
    echo "Qdrant is now running on:"
    echo "  - REST API: http://localhost:6333"
    echo "  - gRPC: http://localhost:6334"
    
    # Show the logs for a few seconds to verify it's running properly
    echo ""
    echo "Recent Qdrant logs:"
    docker logs qdrant --tail 10
else
    echo "✗ Failed to start Qdrant service"
    echo "Check the Docker Compose configuration or logs for errors:"
    docker-compose logs qdrant
    exit 1
fi

echo ""
echo "To stop the Qdrant service, run: docker-compose down"
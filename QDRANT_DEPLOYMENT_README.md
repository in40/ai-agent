# Qdrant Vector Database Deployment

This directory contains scripts and configuration for deploying Qdrant as a vector database for the AI Agent project.

## Files Overview

- `docker-compose.yml`: Docker Compose configuration for Qdrant
- `start_qdrant_full_setup.sh`: Complete setup script that installs Docker, starts Qdrant, and configures the AI Agent
- `stop_qdrant_service.sh`: Script to stop Qdrant and optionally restore previous configuration
- `test_qdrant_integration.py`: Test script to verify Qdrant integration
- `test_qdrant_syntax.py`: Simple syntax check for Qdrant integration files

## Quick Start

### To deploy Qdrant:
```bash
./start_qdrant_full_setup.sh
```

This script will:
1. Install Docker and Docker Compose if not present (optimized for Debian 13)
2. Start the Qdrant service
3. Configure the AI Agent to use Qdrant as the vector store
4. Verify connectivity

### To stop Qdrant:
```bash
./stop_qdrant_service.sh
```

This script will:
1. Stop the Qdrant service
2. Optionally restore previous configuration
3. Clean up resources as requested

## Manual Deployment

If you prefer to set up Qdrant manually:

1. Ensure Docker and Docker Compose are installed
2. Start Qdrant: `docker-compose up -d qdrant`
3. Configure the AI Agent to use Qdrant by setting environment variable:
   ```
   RAG_VECTOR_STORE_TYPE=qdrant
   ```
4. Optionally set custom Qdrant connection details:
   ```
   RAG_QDRANT_URL=http://localhost:6333
   RAG_QDRANT_API_KEY=your_api_key_here
   ```

## Configuration

The Qdrant service is configured to:
- Expose REST API on port 6333
- Expose gRPC on port 6334
- Store data persistently in `./data/qdrant_data/`
- Use default settings suitable for development and production

## Troubleshooting

- Check Qdrant status: `docker-compose ps`
- View Qdrant logs: `docker-compose logs qdrant`
- Verify connectivity: `curl http://localhost:6333/health`
- Check if the AI Agent is using Qdrant: Look for `RAG_VECTOR_STORE_TYPE=qdrant` in your `.env` file

## Compatibility

This setup has been tested with:
- Debian 13 (Trixie)
- Docker 20.10+
- Docker Compose v2+

The Qdrant service uses the official `qdrant/qdrant` Docker image.
# Neo4j Graph Database Configuration for AI Agent

This document describes how to configure and use Neo4j Graph Database with the AI Agent system for hybrid RAG (Retrieval-Augmented Generation) storage.

## Overview

The AI Agent system supports a **Hybrid Mode** that stores document chunks in both:
1. **Vector Database** (Qdrant) - for semantic similarity search
2. **Graph Database** (Neo4j) - for relationship-based queries and knowledge graph

## Architecture

```
AI Agent Server (192.168.51.216)
        |
        | SSH Tunnel (encrypted)
        v
Neo4j Server (192.168.51.187)
  - Bolt Port: 7687
  - HTTP Port: 7474
```

## Configuration

### Environment Variables (.env file)

```bash
# Neo4j Graph Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j
NEO4J_DATABASE=neo4j

# SSH Tunnel Configuration
NEO4J_SSH_HOST=192.168.51.187
NEO4J_SSH_USER=sorokin
NEO4J_SSH_KEY=~/.ssh/id_ed25519_graphrag
NEO4J_SSH_TUNNEL_PORT=7687
```

### SSH Tunnel Setup

The system automatically establishes an SSH tunnel when:
1. Starting all services via `./start_all_services.sh`
2. Connecting to Neo4j via the `Neo4jIntegration` class

Manual tunnel setup:
```bash
ssh -N -f -i ~/.ssh/id_ed25519_graphrag \
    -o StrictHostKeyChecking=no \
    -L 7687:localhost:7687 \
    -L 7474:localhost:7474 \
    sorokin@192.168.51.187
```

## Neo4j Server Setup

### On the Remote Server (192.168.51.187)

Run the setup script (requires sudo):

```bash
# Copy setup script to remote server
scp setup_neo4j_remote.sh sorokin@192.168.51.187:~/

# SSH to remote server
ssh sorokin@192.168.51.187

# Run setup script with sudo
sudo bash ~/setup_neo4j_remote.sh
```

The setup script will:
1. Set Neo4j password to `neo4j`
2. Configure Neo4j to accept remote connections
3. Restart Neo4j service
4. Verify ports are listening

### Manual Setup (if script fails)

```bash
# Set password
sudo neo4j-admin dbms set-initial-password 'neo4j' --overwrite-destination

# Configure remote access
echo "server.default_listen_address=0.0.0.0" | sudo tee -a /etc/neo4j/neo4j.conf

# Restart Neo4j
sudo systemctl restart neo4j

# Verify
sudo ss -tlnp | grep -E '7687|7474'
```

## Usage

### Using Smart Ingestion (Web UI)

1. Navigate to **RAG Functions** → **Smart Ingestion**
2. Select **Processing Mode**: **Hybrid (Vector + Graph)**
3. Upload documents or select from Document Store
4. Click **Start Smart Inestion**

### Using the API

```python
import requests

# Upload files for hybrid processing
files = [('files', open('doc.pdf', 'rb'))]
response = requests.post(
    'http://localhost:5005/process_hybrid',
    files=files,
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

result = response.json()
print(f"Vector chunks: {result['vector_chunks']}")
print(f"Graph nodes: {result['graph_nodes']}")
```

### Using Neo4jIntegration Directly

```python
from backend.services.rag.neo4j_integration import get_neo4j_connection

# Get connection (auto-establishes SSH tunnel)
neo4j = get_neo4j_connection()

if neo4j.connected:
    # Store document
    neo4j.store_document('doc_001', 'test.pdf', {'user': 'admin'})
    
    # Store chunks
    chunks = [
        {'chunk_id': 0, 'content': '...', 'section': '1.1'},
        {'chunk_id': 1, 'content': '...', 'section': '1.2'}
    ]
    neo4j.store_chunks_batch('doc_001', chunks)
    
    # Create knowledge graph
    neo4j.create_knowledge_graph(chunks)
```

## Graph Schema

### Nodes

- **Document** - Represents an uploaded document
  - Properties: `doc_id`, `filename`, `uploaded_at`, `format`, `job_id`

- **Chunk** - Represents a document chunk
  - Properties: `chunk_id`, `content`, `section`, `title`, `chunk_type`, `chunk_index`

- **Entity** - Extracted entities (standards, terms, etc.)
  - Properties: `name`, `type`, `updated_at`

### Relationships

- `(:Document)-[:HAS_CHUNK]->(:Chunk)` - Document contains chunks
- `(:Chunk)-[:REFERENCES]->(:Formula)` - Chunk references a formula
- `(:Chunk)-[:MENTIONS]->(:Entity)` - Chunk mentions an entity

## Cypher Query Examples

### Find all chunks in a document
```cypher
MATCH (d:Document {doc_id: 'doc_001'})-[:HAS_CHUNK]->(c:Chunk)
RETURN c.chunk_id, c.section, c.title
ORDER BY c.chunk_index
```

### Find related concepts
```cypher
MATCH (c:Chunk {chunk_id: 'doc_001_chunk_5'})-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(other:Chunk)
RETURN other.chunk_id, other.content, e.name
LIMIT 10
```

### Search by section
```cypher
MATCH (c:Chunk)
WHERE c.section STARTS WITH '5.2'
RETURN c.chunk_id, c.content
```

## Troubleshooting

### Connection Issues

1. **Check SSH tunnel:**
   ```bash
   ps aux | grep "ssh.*7687"
   nc -zv localhost 7687
   ```

2. **Restart SSH tunnel:**
   ```bash
   pkill -f "ssh.*7687"
   ssh -N -f -i ~/.ssh/id_ed25519_graphrag -L 7687:localhost:7687 sorokin@192.168.51.187
   ```

3. **Test Neo4j connection:**
   ```bash
   cd /root/qwen/ai_agent
   source ai_agent_env/bin/activate
   python -c "from backend.services.rag.neo4j_integration import get_neo4j_connection; n = get_neo4j_connection(); print('Connected:', n.connected)"
   ```

### Authentication Errors

If you see "Unauthorized" errors:
1. Verify password in `.env` matches Neo4j server
2. Reset password on server: `sudo neo4j-admin dbms set-initial-password 'neo4j'`
3. Restart Neo4j: `sudo systemctl restart neo4j`

### Neo4j Not Starting

Check logs on remote server:
```bash
ssh sorokin@192.168.51.187
sudo journalctl -u neo4j -n 50
# or
sudo cat /var/log/neo4j/neo4j.log | tail -50
```

## Performance Tuning

For large document sets, consider:

1. **Increase Neo4j heap size:**
   ```bash
   # In /etc/neo4j/neo4j.conf
   server.memory.heap.initial_size=512m
   server.memory.heap.max_size=2g
   ```

2. **Enable vector indexing** (for similarity search):
   ```cypher
   CREATE INDEX chunk_content IF NOT EXISTS FOR (c:Chunk) ON (c.content)
   ```

3. **Batch operations:** Use `store_chunks_batch()` instead of individual `store_chunk()` calls

## Security Notes

- SSH tunnel provides encryption for Neo4j traffic
- Default password is `neo4j` - change in production
- Neo4j is only accessible via SSH tunnel (not exposed to network)
- SSH key (`id_ed25519_graphrag`) should be kept secure

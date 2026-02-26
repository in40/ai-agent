# Neo4j Configuration Summary

## Current Status

✅ **Completed:**
- Neo4j Python driver installed
- SSH tunnel configuration added to start_all_services.sh
- Neo4jIntegration class updated with SSH tunnel support
- Environment variables configured in .env
- Neo4j setup script created (setup_neo4j_remote.sh)
- Documentation created (NEO4J_CONFIGURATION.md)

⚠️ **Requires Action on Remote Server:**

The Neo4j password on 192.168.51.187 needs to be reset. The current password is unknown.

## Steps to Complete Neo4j Setup

### Option 1: Run Setup Script (Recommended)

1. **Copy setup script to remote server:**
   ```bash
   scp /root/qwen/ai_agent/setup_neo4j_remote.sh sorokin@192.168.51.187:~/
   ```

2. **SSH to remote server:**
   ```bash
   ssh sorokin@192.168.51.187
   ```

3. **Run setup script with sudo:**
   ```bash
   sudo bash ~/setup_neo4j_remote.sh
   ```

### Option 2: Manual Setup

1. **SSH to remote server:**
   ```bash
   ssh sorokin@192.168.51.187
   ```

2. **Reset Neo4j password:**
   ```bash
   sudo neo4j-admin dbms set-initial-password 'neo4j' --overwrite-destination
   ```

3. **Configure remote access:**
   ```bash
   echo "server.default_listen_address=0.0.0.0" | sudo tee -a /etc/neo4j/neo4j.conf
   ```

4. **Restart Neo4j:**
   ```bash
   sudo systemctl restart neo4j
   ```

5. **Verify ports:**
   ```bash
   ss -tlnp | grep -E '7687|7474'
   ```
   Should show:
   - `127.0.0.1:7687` (Bolt protocol)
   - `127.0.0.1:7474` (HTTP interface)

## Current Configuration

### .env Settings
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j
NEO4J_DATABASE=neo4j
NEO4J_SSH_HOST=192.168.51.187
NEO4J_SSH_USER=sorokin
NEO4J_SSH_KEY=~/.ssh/id_ed25519_graphrag
```

### SSH Tunnel
- Automatically established by `./start_all_services.sh`
- Maps localhost:7687 → 192.168.51.187:7687
- Uses SSH key: `~/.ssh/id_ed25519_graphrag`

## Testing Connection

After resetting the password on the remote server:

```bash
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate

python3 -c "
from backend.services.rag.neo4j_integration import get_neo4j_connection
neo4j = get_neo4j_connection()
print('Connected:', neo4j.connected)
if neo4j.connected:
    print('Neo4j is ready for hybrid mode!')
else:
    print('Error:', neo4j.last_error)
"
```

## Using Hybrid Mode

Once Neo4j is connected, use hybrid mode in the Smart Ingestion tab:

1. Go to **RAG Functions** → **Smart Ingestion**
2. Select **Processing Mode**: **Hybrid (Vector + Graph)**
3. Upload documents
4. Click **Start Smart Ingestion**

Documents will be stored in:
- Vector DB (Qdrant) for semantic search
- Neo4j Graph DB for relationship queries

## Files Modified/Created

| File | Purpose |
|------|---------|
| `backend/services/rag/neo4j_integration.py` | Neo4j connection and storage |
| `backend/services/rag/smart_ingestion_enhanced.py` | Hybrid processing endpoint |
| `backend/web_client/index.html` | Smart Ingestion UI with all modes |
| `.env` | Neo4j configuration |
| `start_all_services.sh` | SSH tunnel auto-startup |
| `setup_neo4j_remote.sh` | Remote server setup script |
| `NEO4J_CONFIGURATION.md` | Full documentation |

## Troubleshooting

### SSH Tunnel Issues
```bash
# Check if tunnel is running
ps aux | grep "ssh.*7687"

# Restart tunnel
pkill -f "ssh.*7687"
ssh -N -f -i ~/.ssh/id_ed25519_graphrag -L 7687:localhost:7687 sorokin@192.168.51.187
```

### Neo4j Connection Issues
```bash
# Test connection
nc -zv localhost 7687

# Should show: localhost [127.0.0.1] 7687 (?) open
```

### Check Neo4j Status on Remote
```bash
ssh sorokin@192.168.51.187 "sudo systemctl status neo4j --no-pager | head -10"
```

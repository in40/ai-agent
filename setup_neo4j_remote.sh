#!/bin/bash
# Neo4j Setup Script for GraphRAG Server (192.168.51.187)
# Run this script on the remote server with sudo access

set -e

echo "=== Neo4j Setup Script ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Set Neo4j password
echo "Setting Neo4j password to 'neo4j'..."
neo4j-admin dbms set-initial-password 'neo4j' --overwrite-destination 2>/dev/null || {
    echo "Warning: Could not set password. Neo4j may already be configured."
}

# Update neo4j.conf to allow remote connections
echo "Configuring Neo4j for remote connections..."
CONF_FILE="/etc/neo4j/neo4j.conf"

# Allow bolt connections from any address
if ! grep -q "^server.default_listen_address=" "$CONF_FILE"; then
    echo "server.default_listen_address=0.0.0.0" >> "$CONF_FILE"
fi

# Restart Neo4j
echo "Restarting Neo4j service..."
systemctl restart neo4j || service neo4j restart

# Wait for Neo4j to start
sleep 5

# Check status
echo ""
echo "Neo4j status:"
systemctl status neo4j --no-pager | head -5 || service neo4j status | head -5

# Verify ports
echo ""
echo "Listening ports:"
ss -tlnp | grep -E '7687|7474' || netstat -tlnp | grep -E '7687|7474'

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Neo4j is now configured with:"
echo "  - Bolt port: 7687"
echo "  - HTTP port: 7474"
echo "  - Username: neo4j"
echo "  - Password: neo4j"
echo ""
echo "To connect from AI Agent server, establish SSH tunnel:"
echo "  ssh -N -f -L 7687:localhost:7687 -L 7474:localhost:7474 graphrag-server"

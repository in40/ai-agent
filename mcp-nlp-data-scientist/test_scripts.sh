#!/bin/bash

# Test script to verify the MCP server scripts work correctly

echo "Testing MCP Standard Server scripts..."

# Test 1: Check if all scripts exist and are executable
echo "Checking if scripts exist and are executable..."

SCRIPTS=(
    "start_mcp_server.sh"
    "start_registry_server.sh"
    "start_mcp_default.sh"
    "stop_mcp_server.sh"
    "stop_registry_server.sh"
    "stop_all_servers.sh"
)

ALL_EXIST=true
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "✅ $script exists and is executable"
    else
        echo "❌ $script does not exist or is not executable"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo "❌ Some scripts are missing or not executable"
    exit 1
else
    echo "✅ All scripts exist and are executable"
fi

# Test 2: Check if help works for each script
echo ""
echo "Testing help functionality..."

for script in "${SCRIPTS[@]}"; do
    if ./$script --help >/dev/null 2>&1; then
        echo "✅ $script --help works correctly"
    else
        echo "❌ $script --help failed"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo "❌ Some scripts have help issues"
    exit 1
else
    echo "✅ All scripts have working help functionality"
fi

# Test 3: Check if Python modules can be imported
echo ""
echo "Testing Python module imports..."

PYTHON_MODULES=(
    "mcp_std_server.server"
    "mcp_std_server.handlers.server_handlers"
    "mcp_std_server.transports.streamable_http"
    "mcp_std_server.transports.http_sse"
    "mcp_std_server.transports.stdio"
    "mcp_std_server.utils.json_rpc"
    "mcp_std_server.utils.service_registry_db"
    "mcp_std_server.utils.postgres_registry_db"
    "mcp_std_server.utils.heartbeat_manager"
    "mcp_std_server.utils.notifications"
)

for module in "${PYTHON_MODULES[@]}"; do
    if python -c "import $module" 2>/dev/null; then
        echo "✅ $module imports correctly"
    else
        echo "❌ $module failed to import"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo "❌ Some Python modules failed to import"
    exit 1
else
    echo "✅ All Python modules import correctly"
fi

echo ""
echo "🎉 All tests passed! The MCP Standard Server is ready to use."
echo ""
echo "Quick start commands:"
echo "  ./start_mcp_default.sh                    # Start server with default settings"
echo "  ./start_mcp_server.sh --transport streamable-http --port 3030  # Start server with options"
echo "  ./start_registry_server.sh --port 3031    # Start registry server"
echo "  ./stop_mcp_server.sh --port 3030          # Stop server on port 3030"
echo "  ./stop_registry_server.sh --port 3031      # Stop registry server on port 3031"
echo "  ./stop_all_servers.sh                     # Stop all servers"
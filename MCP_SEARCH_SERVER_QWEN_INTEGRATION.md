# MCP Search Server — Dual-Mode Integration Guide

## Overview

The MCP Search Server now supports **both** the legacy custom HTTP API and the standard MCP protocol (JSON-RPC 2.0) on the same port.

---

## What Changed

The server was **not** a standard MCP server — it was a custom HTTP API with a simple `POST /search` endpoint. Qwen Code's MCP infrastructure expects the Model Context Protocol (JSON-RPC `initialize`, `list_tools`, `call_tool`), which the old server didn't speak.

**The fix:** Added full MCP JSON-RPC 2.0 protocol support **without removing any existing features**.

---

## Dual-Mode Endpoints

Both endpoints run on the same port (8090):

| Endpoint | Protocol | Use Case |
|----------|----------|----------|
| `POST /search` | Legacy custom JSON | Existing callers (backward compatible) |
| `POST /` | MCP JSON-RPC 2.0 | Qwen Code auto-discovery |

---

## Feature Inventory (All Preserved)

### Endpoints
- `POST /search` — legacy format `{"query": "..."}` → `{"success": true, "result": {...}}`
- `POST /` — MCP JSON-RPC 2.0 (`initialize`, `tools/list`, `tools/call`)

### Service Registry
- Registers with registry at `http://127.0.0.1:8080`
- Heartbeat every 20 seconds
- TTL of 60 seconds
- Service type: `mcp_search` with capabilities `["web_search", "brave_search"]`

### Brave Search API
- Calls `https://api.search.brave.com/res/v1/web/search`
- Extracts: `title`, `url`, `description`, `date`, `language`, `thumbnail`
- Exponential backoff retry (configurable `SEARCH_MAX_RETRIES`, `SEARCH_BASE_DELAY`)
- Jitter on retry delays
- Handles 429 rate limiting

### CLI args
`--host`, `--port`, `--registry-url`, `--service-id`, `--service-ttl`, `--log-level`

### Env vars
`BRAVE_SEARCH_API_KEY`, `SEARCH_MAX_RETRIES`, `SEARCH_BASE_DELAY`, `ENABLE_SCREEN_LOGGING`

### Other
Threaded HTTP server, heartbeat filter for logs

---

## Qwen Code Configuration

### Settings File

Edit `/root/qwen/ai_agent/.qwen/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 *)",
      "Bash(ss *)",
      "Bash(netstat *)",
      "Bash(curl *)"
    ]
  },
  "mcpServers": {
    "internet-search": {
      "url": "http://127.0.0.1:8090"
    }
  },
  "$version": 3
}
```

### Restart Qwen Code

After updating the settings file, restart Qwen Code. The MCP search server will be auto-discovered.

---

## Testing

### Legacy Endpoint (backward compatible)

```bash
curl -X POST http://127.0.0.1:8090/search \
  -H "Content-Type: application/json" \
  -d '{"query":"python programming"}'
```

### MCP Protocol (Qwen Code auto-discovery)

```bash
# 1. Initialize
curl -X POST http://127.0.0.1:8090 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'

# 2. List tools
curl -X POST http://127.0.0.1:8090 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}'

# 3. Call tool
curl -X POST http://127.0.0.1:8090 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"internet_search","arguments":{"query":"Qwen AI","count":3}},"id":3}'
```

### In Qwen Code

Ask Qwen Code to perform a search:

> "Search the internet for the latest AI news"

Qwen will auto-discover the `internet_search` tool and call it natively.

---

## Files Modified

| File | Change |
|------|--------|
| `search_server/mcp_search_server.py` | Added MCP JSON-RPC 2.0 protocol support (dual-mode) |
| `.qwen/settings.json` | Added `mcpServers.internet-search` config |
| `MCP_SEARCH_SERVER_QWEN_INTEGRATION.md` | This guide |

---

**Version**: 2.0 (dual-mode)  
**Last Updated**: 2026-04-23  
**MCP Server**: Running on `http://127.0.0.1:8090`

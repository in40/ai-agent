#!/bin/bash
# Test NLP Data Scientist MCP Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== NLP Data Scientist MCP Server Tests ==="
echo ""

# Activate venv
if [ -d "../ai_agent_env" ]; then
    source ../ai_agent_env/bin/activate
elif [ -d "ai_agent_env" ]; then
    source ai_agent_env/bin/activate
fi

echo "1. Testing entity extraction (spaCy)..."
python3 << 'EOF'
import requests
import json

url = "http://127.0.0.1:3065/mcp"

# Test extract_entities
payload = {
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/call",
    "params": {
        "name": "extract_entities",
        "arguments": {
            "text": "GOST R 34.10-2012 was developed by FSB Russia using elliptic curve cryptography. ISO 27001 also references similar concepts."
        }
    }
}

response = requests.post(url, json=payload, timeout=30)
result = response.json()

if "error" in result:
    print(f"✗ Error: {result['error']}")
else:
    content = result.get("result", {}).get("content", [{}])[0].get("text", "")
    data = json.loads(content)
    entities = data.get("entities", [])
    print(f"✓ Found {len(entities)} entities")
    for e in entities[:5]:
        print(f"  - {e['text']} ({e['label']})")
EOF

echo ""
echo "2. Testing entity extraction (LLM)..."
python3 << 'EOF'
import requests
import json

url = "http://127.0.0.1:3065/mcp"

payload = {
    "jsonrpc": "2.0",
    "id": "test-2",
    "method": "tools/call",
    "params": {
        "name": "extract_entities_llm",
        "arguments": {
            "text": "GOST R 34.10-2012 defines digital signature requirements for Russian Federation."
        }
    }
}

response = requests.post(url, json=payload, timeout=60)
result = response.json()

if "error" in result:
    print(f"✗ Error: {result.get('error', 'Unknown')}")
else:
    content = result.get("result", {}).get("content", [{}])[0].get("text", "")
    data = json.loads(content)
    entities = data.get("entities", [])
    print(f"✓ Found {len(entities)} entities via LLM")
EOF

echo ""
echo "3. Testing standards extraction..."
python3 << 'EOF'
import requests
import json

url = "http://127.0.0.1:3065/mcp"

payload = {
    "jsonrpc": "2.0",
    "id": "test-3",
    "method": "tools/call",
    "params": {
        "name": "extract_standards",
        "arguments": {
            "text": "This document references GOST R 34.10-2012, ISO 27001, and RFC 8446 standards."
        }
    }
}

response = requests.post(url, json=payload, timeout=30)
result = response.json()

if "error" in result:
    print(f"✗ Error: {result['error']}")
else:
    content = result.get("result", {}).get("content", [{}])[0].get("text", "")
    data = json.loads(content)
    standards = data.get("standards", [])
    print(f"✓ Found {len(standards)} standards")
    for s in standards:
        print(f"  - {s['text']}")
EOF

echo ""
echo "4. Testing get_entity_types..."
python3 << 'EOF'
import requests
import json

url = "http://127.0.0.1:3065/mcp"

payload = {
    "jsonrpc": "2.0",
    "id": "test-4",
    "method": "tools/call",
    "params": {
        "name": "get_entity_types",
        "arguments": {}
    }
}

response = requests.post(url, json=payload, timeout=30)
result = response.json()

if "error" in result:
    print(f"✗ Error: {result['error']}")
else:
    content = result.get("result", {}).get("content", [{}])[0].get("text", "")
    data = json.loads(content)
    print(f"✓ Available entity types: {len(data)}")
    for type_name in list(data.keys())[:5]:
        print(f"  - {type_name}: {data[type_name][:50]}...")
EOF

echo ""
echo "=== Tests Complete ==="

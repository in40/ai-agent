#!/bin/bash
# Script to get token and test API

# Register user (might fail if already exists, which is OK)
curl -X POST http://192.168.51.216:5000/auth/register -H "Content-Type: application/json" -d '{"username":"testuser","password":"testpassword123"}'
echo ""

# Get token
RESPONSE=$(curl -s -X POST http://192.168.51.216:5000/auth/login -H "Content-Type: application/json" -d '{"username":"testuser","password":"testpassword123"}')
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

echo "Token: $TOKEN"

# Call the API
curl -X POST http://192.168.51.216:5000/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_request":"look into local documents, what is current price for URALS"}'
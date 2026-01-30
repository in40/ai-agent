#!/bin/bash
# Test script to verify the import_processed endpoint is accessible through the gateway

echo "Testing import_processed endpoint accessibility..."

# Test if the endpoint exists and returns the expected method not allowed error (since we're not sending proper data)
response=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS http://localhost:5000/api/rag/import_processed)
if [ "$response" -eq 200 ] || [ "$response" -eq 405 ]; then
    echo "✅ Endpoint accessible through gateway"
else
    echo "❌ Endpoint not accessible through gateway (status: $response)"
fi

# Test with GET method (should return method not allowed)
response=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:5000/api/rag/import_processed)
if [ "$response" -eq 405 ]; then
    echo "✅ GET method correctly returns 405 Method Not Allowed"
else
    echo "❌ Unexpected response for GET method (status: $response)"
fi

echo "Gateway endpoint verification complete."
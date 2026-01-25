#!/bin/bash
# Script to start services with consistent environment variables

# Set consistent environment variables
export JWT_SECRET_KEY="consistent-secret-for-all-services"
export SECRET_KEY="consistent-secret-for-all-services"

echo "Environment variables set:"
echo "JWT_SECRET_KEY: $JWT_SECRET_KEY"
echo "SECRET_KEY: $SECRET_KEY"

echo "Starting microservices with consistent secrets..."
cd /root/qwen_test/ai_agent/backend

# Start microservices with explicit environment variables
JWT_SECRET_KEY="$JWT_SECRET_KEY" SECRET_KEY="$SECRET_KEY" ./services/start_microservices.sh &
MICROSERVICES_PID=$!

echo "Waiting for microservices to start..."
sleep 25

echo "Starting web client with consistent secrets..."
cd /root/qwen_test/ai_agent/backend
JWT_SECRET_KEY="$JWT_SECRET_KEY" SECRET_KEY="$SECRET_KEY" python web_client/app.py &
WEBC_CLIENT_PID=$!

echo "Services started!"
echo "Microservices PID: $MICROSERVICES_PID"
echo "Web Client PID: $WEBC_CLIENT_PID"

# Keep the script running
wait $MICROSERVICES_PID $WEBC_CLIENT_PID
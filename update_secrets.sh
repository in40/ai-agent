#!/bin/bash

# Script to generate random secrets and update the gateway app.py file

# Generate random secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

echo "Generated new secrets:"
echo "SECRET_KEY: $SECRET_KEY"
echo "JWT_SECRET_KEY: $JWT_SECRET_KEY"

# Backup the original file
cp /root/qwen/ai_agent/backend/app.py /root/qwen/ai_agent/backend/app.py.backup

echo "Created backup: /root/qwen/ai_agent/backend/app.py.backup"

# Update the SECRET_KEY in the gateway app.py file
sed -i "s|os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')|os.environ.get('SECRET_KEY', '$SECRET_KEY')|" /root/qwen/ai_agent/backend/app.py

# Update the JWT_SECRET_KEY in the gateway app.py file
sed -i "s|os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-this-too')|os.environ.get('JWT_SECRET_KEY', '$JWT_SECRET_KEY')|" /root/qwen/ai_agent/backend/app.py

echo "Updated secrets in /root/qwen/ai_agent/backend/app.py"

echo "Done!"
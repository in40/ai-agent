#!/bin/bash

# Script to configure nginx with TLS support for the AI Agent system
# This script will:
# 1. Generate self-signed certificates (for testing purposes)
# 2. Create nginx configuration
# 3. Enable the site
# 4. Restart nginx

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up nginx with TLS for AI Agent system...${NC}"

# Configuration variables
DOMAIN_NAME=${DOMAIN_NAME:-"localhost"}
SSL_DIR="/etc/ssl/ai_agent"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
CONFIG_FILE="$NGINX_SITES_AVAILABLE/ai_agent"

# Create SSL directory if it doesn't exist
sudo mkdir -p $SSL_DIR

# Generate self-signed certificate if they don't exist
if [ ! -f "$SSL_DIR/ai_agent.crt" ] || [ ! -f "$SSL_DIR/ai_agent.key" ]; then
    echo -e "${YELLOW}Generating self-signed SSL certificate...${NC}"
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $SSL_DIR/ai_agent.key \
        -out $SSL_DIR/ai_agent.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN_NAME"
    echo -e "${GREEN}SSL certificate generated successfully.${NC}"
else
    echo -e "${GREEN}SSL certificate already exists.${NC}"
fi

# Create nginx configuration
echo -e "${YELLOW}Creating nginx configuration...${NC}"

sudo tee $CONFIG_FILE > /dev/null <<EOF
# AI Agent System Nginx Configuration
# Auto-generated configuration

upstream backend {
    server localhost:5000;
}

upstream streamlit {
    server localhost:8501;
}

upstream react {
    server localhost:3000;
}

# Main server with SSL
server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;

    # SSL Configuration
    ssl_certificate $SSL_DIR/ai_agent.crt;
    ssl_certificate_key $SSL_DIR/ai_agent.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5:!EXPORT:!DES:!RC4:!PSK:!SRP:!CAMELLIA;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Main API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
        
        # WebSocket support if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Authentication routes
    location /auth/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
    }

    # Static files and web client
    location / {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # RAG routes
    location /rag/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
    }

    # Streamlit GUI proxy
    location /streamlit/ {
        proxy_pass http://streamlit/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # React GUI proxy
    location /react/ {
        proxy_pass http://react/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
        
        # WebSocket support for React if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }

    # Favicon
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $DOMAIN_NAME;
    return 301 https://\$server_name\$request_uri;
}
EOF

echo -e "${GREEN}Nginx configuration created.${NC}"

# Enable the site
echo -e "${YELLOW}Enabling site...${NC}"
sudo ln -sf $CONFIG_FILE $NGINX_SITES_ENABLED/ai_agent

echo -e "${GREEN}Site enabled.${NC}"

# Test nginx configuration
echo -e "${YELLOW}Testing nginx configuration...${NC}"
sudo nginx -t

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Nginx configuration is valid.${NC}"
    
    # Restart nginx
    echo -e "${YELLOW}Restarting nginx...${NC}"
    sudo systemctl restart nginx
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Nginx restarted successfully.${NC}"
        echo -e "${GREEN}AI Agent system is now available at https://$DOMAIN_NAME${NC}"
    else
        echo -e "${RED}Failed to restart nginx.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Nginx configuration is invalid. Please check the configuration.${NC}"
    exit 1
fi

echo -e "${GREEN}Setup complete!${NC}"
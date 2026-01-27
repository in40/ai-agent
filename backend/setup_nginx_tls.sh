#!/bin/bash
# Script to configure nginx with TLS for the AI Agent system
set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up nginx with TLS for AI Agent system...${NC}"

# Create SSL directory if it doesn't exist
SSL_DIR="/etc/ssl/ai_agent"
sudo mkdir -p $SSL_DIR

# Generate self-signed certificate if they don't exist
CERT_PATH="$SSL_DIR/ai_agent.crt"
KEY_PATH="$SSL_DIR/ai_agent.key"

if [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
    echo -e "${YELLOW}Generating self-signed SSL certificate...${NC}"
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $KEY_PATH \
        -out $CERT_PATH \
        -subj "/C=US/ST=State/L=City/O=AI Agent System/CN=localhost"
    echo -e "${GREEN}SSL certificate generated.${NC}"
else
    echo -e "${GREEN}SSL certificate already exists.${NC}"
fi

# Create nginx configuration
NGINX_CONFIG="/etc/nginx/sites-available/ai_agent"

sudo tee $NGINX_CONFIG > /dev/null <<EOF
# AI Agent System Nginx Configuration
# Auto-generated configuration

upstream gateway {
    server localhost:5000;
}

upstream auth_service {
    server localhost:5001;
}

upstream agent_service {
    server localhost:5002;
}

upstream rag_service {
    server localhost:5003;
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
    server_name localhost;

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
    location / {
        proxy_pass http://gateway;
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
        proxy_connect_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_read_timeout 3600s;
    }

    # Authentication routes
    location /auth/ {
        proxy_pass http://auth_service/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
    }

    # Agent routes
    location /agent/ {
        proxy_pass http://agent_service/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Authorization \$http_authorization;
    }

    # RAG routes
    location /rag/ {
        proxy_pass http://rag_service/;
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
        proxy_connect_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_read_timeout 3600s;
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
        proxy_connect_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_read_timeout 3600s;
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
    server_name localhost;
    return 301 https://\$server_name\$request_uri;
}
EOF

echo -e "${GREEN}Nginx configuration created.${NC}"

# Enable the site
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
sudo ln -sf $NGINX_CONFIG $NGINX_SITES_ENABLED/ai_agent

echo -e "${GREEN}Site enabled.${NC}"

# Test nginx configuration
echo -e "${YELLOW}Testing nginx configuration...${NC}"
sudo nginx -t

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Nginx configuration is valid.${NC}"
    
    # Reload nginx
    echo -e "${YELLOW}Reloading nginx...${NC}"
    sudo systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Nginx reloaded successfully.${NC}"
        echo -e "${GREEN}AI Agent system is now available at https://localhost${NC}"
    else
        echo -e "${RED}Failed to reload nginx.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Nginx configuration is invalid. Please check the configuration.${NC}"
    exit 1
fi

echo -e "${GREEN}Setup complete!${NC}"
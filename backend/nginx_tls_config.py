#!/bin/bash
"""
Nginx TLS Configuration Script
Sets up TLS termination with nginx for the AI Agent system
"""
import os
import subprocess
import sys
from pathlib import Path

def setup_nginx_tls():
    """Set up nginx with TLS configuration"""
    
    # Create SSL certificate directory
    ssl_dir = Path("/etc/ssl/ai_agent")
    ssl_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate self-signed certificate if it doesn't exist
    cert_path = ssl_dir / "ai_agent.crt"
    key_path = ssl_dir / "ai_agent.key"
    
    if not cert_path.exists() or not key_path.exists():
        print("Generating self-signed SSL certificate...")
        subprocess.run([
            "openssl", "req", "-x509", "-nodes", "-days", "365",
            "-newkey", "rsa:2048",
            "-keyout", str(key_path),
            "-out", str(cert_path),
            "-subj", "/C=US/ST=State/L=City/O=AI Agent System/CN=localhost"
        ])
        print("SSL certificate generated.")
    else:
        print("SSL certificate already exists.")
    
    # Create nginx configuration
    nginx_config = f"""
# AI Agent System Nginx Configuration
# Auto-generated configuration

upstream gateway {{
    server localhost:5000;
}}

upstream auth_service {{
    server localhost:5001;
}}

upstream agent_service {{
    server localhost:5002;
}}

upstream rag_service {{
    server localhost:5003;
}}

upstream streamlit {{
    server localhost:8501;
}}

upstream react {{
    server localhost:3000;
}}

# Main server with SSL
server {{
    listen 443 ssl http2;
    server_name localhost;

    # SSL Configuration
    ssl_certificate {cert_path};
    ssl_certificate_key {key_path};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5:!EXPORT:!DES:!RC4:!PSK:!SRP:!CAMELLIA;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Main API routes
    location / {{
        proxy_pass http://gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
        
        # WebSocket support if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # Authentication routes
    location /auth/ {{
        proxy_pass http://auth_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
    }}

    # Agent routes
    location /agent/ {{
        proxy_pass http://agent_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
    }}

    # RAG routes
    location /rag/ {{
        proxy_pass http://rag_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
    }}

    # Streamlit GUI proxy
    location /streamlit/ {{
        proxy_pass http://streamlit/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # React GUI proxy
    location /react/ {{
        proxy_pass http://react/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
        
        # WebSocket support for React if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # Health check
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}

    # Favicon
    location = /favicon.ico {{
        log_not_found off;
        access_log off;
    }}
}}

# Redirect HTTP to HTTPS
server {{
    listen 80;
    server_name localhost;
    return 301 https://$server_name$request_uri;
}}
"""
    
    # Write nginx configuration
    nginx_sites_available = Path("/etc/nginx/sites-available")
    nginx_sites_enabled = Path("/etc/nginx/sites-enabled")
    
    config_path = nginx_sites_available / "ai_agent"
    with open(config_path, 'w') as f:
        f.write(nginx_config)
    
    print(f"Nginx configuration written to {config_path}")
    
    # Enable the site
    config_enabled_path = nginx_sites_enabled / "ai_agent"
    if config_enabled_path.exists():
        config_enabled_path.unlink()  # Remove existing symlink
    
    config_enabled_path.symlink_to(config_path)
    print(f"Site enabled at {config_enabled_path}")
    
    # Test nginx configuration
    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in nginx configuration: {result.stderr}")
        return False
    
    # Reload nginx
    subprocess.run(["systemctl", "reload", "nginx"])
    print("Nginx configuration loaded successfully.")
    
    return True

if __name__ == "__main__":
    success = setup_nginx_tls()
    if success:
        print("\\nNginx TLS configuration completed successfully!")
        print("The AI Agent system is now accessible at https://localhost")
    else:
        print("\\nNginx TLS configuration failed!")
        sys.exit(1)
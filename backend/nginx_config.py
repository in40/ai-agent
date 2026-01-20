"""
Nginx configuration for the AI Agent system
This configuration sets up HTTPS with TLS and proxies requests to backend services
"""
import os
from config import config_manager


def generate_nginx_config():
    """Generate nginx configuration file"""
    
    nginx_config = f"""# AI Agent System Nginx Configuration
# Auto-generated configuration

events {{
    worker_connections 1024;
}}

http {{
    upstream backend {{
        server {config_manager.get_backend_config()['host']}:{config_manager.get_backend_config()['port']};
    }}

    upstream streamlit {{
        server {config_manager.get_services_config().get('streamlit_url', 'localhost:8501').replace('http://', '')};
    }}

    upstream react {{
        server {config_manager.get_services_config().get('react_url', 'localhost:3000').replace('http://', '')};
    }}

    # Main server with SSL
    server {{
        listen 443 ssl http2;
        server_name _;

        # SSL Configuration
        ssl_certificate {config_manager.get_nginx_config().get('ssl_cert_path', '/etc/ssl/certs/ai_agent.crt')};
        ssl_certificate_key {config_manager.get_nginx_config().get('ssl_key_path', '/etc/ssl/private/ai_agent.key')};
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5:!EXPORT:!DES:!RC4:!PSK:!SRP:!CAMELLIA;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # Main API routes
        location /api/ {{
            proxy_pass http://backend;
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
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Authorization $http_authorization;
        }}

        # RAG routes
        location /rag/ {{
            proxy_pass http://backend;
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
        server_name _;
        return 301 https://$server_name$request_uri;
    }}
}}
"""
    
    return nginx_config


def write_nginx_config(config_path: str = "/etc/nginx/sites-available/ai_agent"):
    """Write the nginx configuration to a file"""
    config_content = generate_nginx_config()
    
    # Write the configuration
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print(f"Nginx configuration written to {config_path}")
    print("To enable this configuration, run: ln -s {config_path} /etc/nginx/sites-enabled/")
    print("Then restart nginx: systemctl restart nginx")


if __name__ == "__main__":
    # Generate and write the nginx configuration
    write_nginx_config()
"""
Configuration module for distributed deployment of AI Agent system
"""
import os
import json
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration for distributed deployment"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or os.getenv('CONFIG_FILE', 'config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment variables"""
        config = {}
        
        # Load from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        # Override with environment variables
        config['backend'] = {
            'host': os.getenv('BACKEND_HOST', config.get('backend', {}).get('host', '0.0.0.0')),
            'port': int(os.getenv('BACKEND_PORT', config.get('backend', {}).get('port', 5000))),
            'debug': os.getenv('BACKEND_DEBUG', config.get('backend', {}).get('debug', 'false')).lower() == 'true'
        }
        
        config['frontend'] = {
            'host': os.getenv('FRONTEND_HOST', config.get('frontend', {}).get('host', '0.0.0.0')),
            'port': int(os.getenv('FRONTEND_PORT', config.get('frontend', {}).get('port', 3000)))
        }
        
        config['nginx'] = {
            'ssl_enabled': os.getenv('NGINX_SSL_ENABLED', config.get('nginx', {}).get('ssl_enabled', 'true')).lower() == 'true',
            'ssl_cert_path': os.getenv('NGINX_SSL_CERT_PATH', config.get('nginx', {}).get('ssl_cert_path', '/etc/ssl/certs/ai_agent.crt')),
            'ssl_key_path': os.getenv('NGINX_SSL_KEY_PATH', config.get('nginx', {}).get('ssl_key_path', '/etc/ssl/private/ai_agent.key')),
            'backend_proxy_url': os.getenv('NGINX_BACKEND_PROXY_URL', config.get('nginx', {}).get('backend_proxy_url', 'http://localhost:5000')),
            'streamlit_proxy_url': os.getenv('NGINX_STREAMLIT_PROXY_URL', config.get('nginx', {}).get('streamlit_proxy_url', 'http://localhost:8501')),
            'react_proxy_url': os.getenv('NGINX_REACT_PROXY_URL', config.get('nginx', {}).get('react_proxy_url', 'http://localhost:3000'))
        }
        
        config['services'] = {
            'streamlit_url': os.getenv('STREAMLIT_URL', config.get('services', {}).get('streamlit_url', 'http://localhost:8501')),
            'react_url': os.getenv('REACT_URL', config.get('services', {}).get('react_url', 'http://localhost:3000')),
            'registry_url': os.getenv('REGISTRY_URL', config.get('services', {}).get('registry_url'))
        }
        
        config['auth'] = {
            'secret_key': os.getenv('SECRET_KEY', config.get('auth', {}).get('secret_key', 'your-secret-key-change-this-in-production')),
            'jwt_secret_key': os.getenv('JWT_SECRET_KEY', config.get('auth', {}).get('jwt_secret_key', 'jwt-secret-string-change-this-too')),
            'token_expiry_hours': int(os.getenv('TOKEN_EXPIRY_HOURS', config.get('auth', {}).get('token_expiry_hours', 24)))
        }
        
        return config
    
    def get_backend_config(self) -> Dict[str, Any]:
        """Get backend configuration"""
        return self.config.get('backend', {})
    
    def get_frontend_config(self) -> Dict[str, Any]:
        """Get frontend configuration"""
        return self.config.get('frontend', {})
    
    def get_nginx_config(self) -> Dict[str, Any]:
        """Get nginx configuration"""
        return self.config.get('nginx', {})

    def get_backend_config(self) -> Dict[str, Any]:
        """Get backend configuration"""
        return self.config.get('backend', {})

    def get_services_config(self) -> Dict[str, Any]:
        """Get services configuration"""
        return self.config.get('services', {})
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration"""
        return self.config.get('auth', {})
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """
        Save current configuration to file
        
        Args:
            config_file: Path to save configuration (optional, uses default if not provided)
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            save_path = config_file or self.config_file
            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config to {save_path}: {e}")
            return False
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration with new values
        
        Args:
            new_config: Dictionary with new configuration values
        """
        def merge_dict(base_dict: Dict, update_dict: Dict) -> Dict:
            """Recursively merge two dictionaries"""
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    merge_dict(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        merge_dict(self.config, new_config)


# Global configuration instance
config_manager = ConfigManager()


def get_backend_host() -> str:
    """Get backend host from configuration"""
    return config_manager.get_backend_config().get('host', '0.0.0.0')


def get_backend_port() -> int:
    """Get backend port from configuration"""
    return config_manager.get_backend_config().get('port', 5000)


def get_frontend_host() -> str:
    """Get frontend host from configuration"""
    return config_manager.get_frontend_config().get('host', '0.0.0.0')


def get_frontend_port() -> int:
    """Get frontend port from configuration"""
    return config_manager.get_frontend_config().get('port', 3000)


def is_ssl_enabled() -> bool:
    """Check if SSL is enabled"""
    return config_manager.get_nginx_config().get('ssl_enabled', True)


def get_backend_proxy_url() -> str:
    """Get backend proxy URL for nginx"""
    return config_manager.get_nginx_config().get('backend_proxy_url', 'http://localhost:5000')


def get_streamlit_proxy_url() -> str:
    """Get Streamlit proxy URL for nginx"""
    return config_manager.get_nginx_config().get('streamlit_proxy_url', 'http://localhost:8501')


def get_react_proxy_url() -> str:
    """Get React proxy URL for nginx"""
    return config_manager.get_nginx_config().get('react_proxy_url', 'http://localhost:3000')


def get_auth_secret() -> str:
    """Get authentication secret"""
    return config_manager.get_auth_config().get('secret_key', 'your-secret-key-change-this-in-production')


def get_jwt_secret() -> str:
    """Get JWT secret"""
    return config_manager.get_auth_config().get('jwt_secret_key', 'jwt-secret-string-change-this-too')
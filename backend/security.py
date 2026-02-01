"""
Security module for the AI Agent system
Implements enhanced security features including RBAC, rate limiting, and audit logging
"""
import jwt
import hashlib
import time
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import redis
import ipaddress
from dataclasses import dataclass
import os
# Use environment variables instead of config manager for now
# from config import config_manager

# Initialize Redis connection for rate limiting and session management
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )
    redis_client.ping()  # Test connection
except:
    # Fallback to in-memory storage if Redis is not available
    redis_client = None


class UserRole(Enum):
    """Enumeration of user roles"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SERVICE_ACCOUNT = "service_account"


class Permission(Enum):
    """Enumeration of permissions"""
    READ_AGENT = "read:agent"
    WRITE_AGENT = "write:agent"
    READ_RAG = "read:rag"
    WRITE_RAG = "write:rag"
    READ_MCP = "read:mcp"
    MANAGE_USERS = "manage:users"
    READ_SYSTEM = "read:system"
    WRITE_SYSTEM = "write:system"


@dataclass
class UserSession:
    """Data class for user session information"""
    user_id: str
    role: UserRole
    permissions: List[Permission]
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime


class SecurityManager:
    """Main security manager class"""
    
    def __init__(self):
        self.role_permissions = {
            UserRole.ADMIN: [
                Permission.READ_AGENT, Permission.WRITE_AGENT,
                Permission.READ_RAG, Permission.WRITE_RAG,
                Permission.READ_MCP,
                Permission.MANAGE_USERS,
                Permission.READ_SYSTEM, Permission.WRITE_SYSTEM
            ],
            UserRole.USER: [
                Permission.READ_AGENT, Permission.WRITE_AGENT,
                Permission.READ_RAG, Permission.WRITE_RAG,
                Permission.READ_MCP
            ],
            UserRole.GUEST: [
                Permission.READ_AGENT
            ],
            UserRole.SERVICE_ACCOUNT: [
                Permission.READ_AGENT, Permission.WRITE_AGENT,
                Permission.READ_RAG, Permission.WRITE_RAG,
                Permission.READ_MCP
            ]
        }
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with username and password
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            User info dict if authentication succeeds, None otherwise
        """
        import bcrypt
        
        # For authentication, we now use the database
        # Import the user database module
        from database.user_db import user_db

        # Verify user credentials using the database
        user = user_db.get_user(username)
        if user and user_db.verify_password(username, password):
            # Determine user role from database
            user_role = UserRole(user.get('role', 'user'))
            return {
                'user_id': username,
                'role': user_role,
                'permissions': self.role_permissions[user_role]
            }
        return None
    
    def generate_token(self, user_info: Dict, expiration_hours: int = 24) -> str:
        """
        Generate JWT token for authenticated user

        Args:
            user_info: Dictionary containing user information
            expiration_hours: Token expiration in hours

        Returns:
            JWT token string
        """
        # Use environment variable for JWT secret, with fallback to consistent default that matches auth service
        jwt_secret = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string-change-this-too')

        payload = {
            'user_id': user_info['user_id'],
            'role': user_info['role'].value,
            'permissions': [perm.value for perm in user_info['permissions']],
            'exp': datetime.utcnow() + timedelta(hours=expiration_hours),
            'iat': datetime.utcnow()
        }

        return jwt.encode(payload, jwt_secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and return user information

        Args:
            token: JWT token to verify

        Returns:
            User info dict if token is valid, None otherwise
        """
        # Use environment variable for JWT secret, with fallback to consistent default that matches auth service
        jwt_secret = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string-change-this-too')

        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])

            # In a microservices architecture, we can't rely on a shared in-memory users_db
            # Instead, we'll just return the user info from the token
            # In a real implementation, you might want to check against a centralized user service
            return {
                'user_id': payload['user_id'],
                'role': UserRole(payload['role']),
                'permissions': [Permission(perm) for perm in payload['permissions']]
            }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def has_permission(self, user_info: Dict, permission: Permission) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user_info: User information dictionary
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        return permission in user_info['permissions']
    
    def create_session(self, user_info: Dict, ip_address: str, user_agent: str) -> str:
        """
        Create a new user session
        
        Args:
            user_info: User information dictionary
            ip_address: IP address of the user
            user_agent: User agent string
            
        Returns:
            Session ID
        """
        session_id = hashlib.sha256(f"{user_info['user_id']}{time.time()}{ip_address}".encode()).hexdigest()
        
        session = UserSession(
            user_id=user_info['user_id'],
            role=user_info['role'],
            permissions=user_info['permissions'],
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # Store session in Redis or fallback to in-memory
        if redis_client:
            redis_client.setex(
                f"session:{session_id}",
                timedelta(hours=24),
                session.user_id
            )
        else:
            # Fallback to in-memory storage
            if not hasattr(self, 'sessions'):
                self.sessions = {}
            self.sessions[session_id] = session
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate a session ID
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        if redis_client:
            return redis_client.exists(f"session:{session_id}") == 1
        else:
            # Fallback to in-memory validation
            if not hasattr(self, 'sessions'):
                self.sessions = {}
            return session_id in self.sessions and self.sessions[session_id].expires_at > datetime.utcnow()
    
    def log_audit_event(self, user_id: str, action: str, resource: str, ip_address: str, success: bool = True):
        """
        Log an audit event
        
        Args:
            user_id: ID of the user performing the action
            action: Action performed (e.g., 'read', 'write', 'delete')
            resource: Resource affected
            ip_address: IP address of the request
            success: Whether the action was successful
        """
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'ip_address': ip_address,
            'success': success
        }
        
        # In a real implementation, this would be stored in a database or log system
        # For now, we'll just print it
        print(f"AUDIT: {audit_entry}")


# Global security manager instance
security_manager = SecurityManager()


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for API endpoints
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request, jsonify
            import os
            
            # Get token from header
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'message': 'Token is missing!'}), 401
            
            # Verify token
            user_info = security_manager.verify_token(token)
            if not user_info:
                return jsonify({'message': 'Token is invalid or expired!'}), 401
            
            # Check permission
            if not security_manager.has_permission(user_info, permission):
                return jsonify({'message': 'Insufficient permissions!'}), 403
            
            # Log audit event
            security_manager.log_audit_event(
                user_info['user_id'],
                permission.value.split(':')[0],  # Extract action from permission
                permission.value.split(':')[1],  # Extract resource from permission
                request.remote_addr,
                success=True
            )
            
            return f(user_info['user_id'], *args, **kwargs)
        return decorated
    return decorator


def rate_limit(max_requests: int, window_seconds: int):
    """
    Decorator to implement rate limiting
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request, jsonify
            
            # Create a unique key for this endpoint and IP
            key = f"rate_limit:{request.endpoint}:{request.remote_addr}"
            
            if redis_client:
                # Use Redis for rate limiting
                current_requests = redis_client.get(key)
                if current_requests is None:
                    redis_client.setex(key, window_seconds, 1)
                else:
                    current_requests = int(current_requests)
                    if current_requests >= max_requests:
                        return jsonify({
                            'message': f'Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.'
                        }), 429
                    else:
                        redis_client.incr(key)
            else:
                # Fallback to in-memory rate limiting (not persistent across restarts)
                if not hasattr(rate_limit, 'requests'):
                    rate_limit.requests = {}
                
                current_time = time.time()
                if key not in rate_limit.requests:
                    rate_limit.requests[key] = []
                
                # Clean old requests
                rate_limit.requests[key] = [
                    timestamp for timestamp in rate_limit.requests[key]
                    if current_time - timestamp < window_seconds
                ]
                
                if len(rate_limit.requests[key]) >= max_requests:
                    return jsonify({
                        'message': f'Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.'
                    }), 429
                
                rate_limit.requests[key].append(current_time)
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_input(data: Dict, schema: Dict) -> Dict:
    """
    Validate input data against a schema
    
    Args:
        data: Input data to validate
        schema: Schema to validate against
        
    Returns:
        Dictionary with validation errors if any, otherwise empty dict
    """
    errors = {}
    
    for field, constraints in schema.items():
        if constraints.get('required', False) and field not in data:
            errors[field] = 'Field is required'
            continue
            
        if field in data:
            value = data[field]
            
            # Type validation
            expected_type = constraints.get('type')
            if expected_type and not isinstance(value, expected_type):
                errors[field] = f'Expected {expected_type.__name__}, got {type(value).__name__}'
            
            # Length validation for strings
            if isinstance(value, str):
                min_length = constraints.get('min_length')
                max_length = constraints.get('max_length')

                if min_length and len(value) < min_length:
                    errors[field] = f'Minimum length is {min_length}'

                if max_length and len(value) > max_length:
                    errors[field] = f'Maximum length is {max_length}'

            # Value range validation for numbers
            if isinstance(value, (int, float)):
                min_value = constraints.get('min_value')
                max_value = constraints.get('max_value')

                if min_value is not None and value < min_value:
                    errors[field] = f'Minimum value is {min_value}'

                if max_value is not None and value > max_value:
                    errors[field] = f'Maximum value is {max_value}'
            
            # Sanitization
            if constraints.get('sanitize', False):
                # Remove potentially dangerous characters
                sanitized_value = value.replace('<script', '&lt;script').replace('javascript:', 'javascript&#58;')
                if sanitized_value != value:
                    data[field] = sanitized_value
    
    return errors
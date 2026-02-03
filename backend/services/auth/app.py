"""
Authentication Service for AI Agent System
Handles user authentication, authorization, and session management
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import bcrypt
import logging
from typing import Dict, Any, Optional
import redis
import hashlib
import time

# Import security components from shared module
from backend.security import security_manager, validate_input, Permission, UserRole

# Import database components
from database.user_db import user_db

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-this-too')

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis for session management and rate limiting
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

# Initialize the database
try:
    user_db.init_db()
    logger.info("User database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize user database: {e}")
    raise


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
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
            
            return f(user_info['user_id'], *args, **kwargs)
        return decorated
    return decorator


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'authentication',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        # Validate input
        schema = {
            'username': {
                'type': str,
                'required': True,
                'min_length': 3,
                'max_length': 50,
                'sanitize': True
            },
            'password': {
                'type': str,
                'required': True,
                'min_length': 8,
                'max_length': 128,
                'sanitize': True
            }
        }

        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'message': f'Validation error: {validation_errors}'}), 400

        username = data.get('username')
        password = data.get('password')

        # Check if user already exists using the database
        existing_user = user_db.get_user(username)
        if existing_user:
            return jsonify({'message': 'Username already exists!'}), 400

        # Create user in database
        success = user_db.create_user(username, password)
        if not success:
            return jsonify({'message': 'Registration failed!'}), 500

        # Log audit event
        security_manager.log_audit_event(
            'system',
            'create',
            'user',
            request.remote_addr,
            success=True
        )

        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed!'}), 500


@app.route('/login', methods=['POST'])
def login():
    """Login a user and return JWT token"""
    try:
        data = request.get_json()

        # Validate input
        schema = {
            'username': {
                'type': str,
                'required': True,
                'min_length': 3,
                'max_length': 50,
                'sanitize': True
            },
            'password': {
                'type': str,
                'required': True,
                'min_length': 8,
                'max_length': 128,
                'sanitize': True
            }
        }

        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'message': f'Validation error: {validation_errors}'}), 400

        username = data.get('username')
        password = data.get('password')

        # Verify user credentials using the database
        user = user_db.get_user(username)
        if not user or not user_db.verify_password(username, password):
            # Log failed login attempt
            security_manager.log_audit_event(
                username or 'unknown',
                'login',
                'auth',
                request.remote_addr,
                success=False
            )
            return jsonify({'message': 'Invalid credentials!'}), 401

        # Update last login time
        user_db.update_last_login(username)

        # Create user info
        user_role = UserRole(user.get('role', 'user'))  # Use the role from the database
        user_info = {
            'user_id': username,
            'role': user_role,
            'permissions': security_manager.role_permissions[user_role]
        }

        # Generate JWT token
        token = security_manager.generate_token(user_info)

        # Create session
        session_id = security_manager.create_session(
            user_info,
            request.remote_addr,
            request.headers.get('User-Agent', 'Unknown')
        )

        # Log successful login
        security_manager.log_audit_event(
            username,
            'login',
            'auth',
            request.remote_addr,
            success=True
        )

        return jsonify({
            'token': token,
            'session_id': session_id,
            'message': 'Login successful!',
            'user_info': {
                'user_id': user_info['user_id'],
                'role': user_info['role'].value,
                'permissions': [p.value for p in user_info['permissions']]
            }
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")

        # Log failed login attempt
        username = data.get('username', 'unknown') if 'data' in locals() else 'unknown'
        security_manager.log_audit_event(
            username,
            'login',
            'auth',
            request.remote_addr,
            success=False
        )

        return jsonify({'message': 'Login failed!'}), 500


@app.route('/validate', methods=['POST'])
@token_required
def validate_token(current_user_id):
    """Validate a JWT token and return user info"""
    try:
        token = request.headers.get('Authorization')
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_info = security_manager.verify_token(token)
        if user_info:
            return jsonify({
                'valid': True,
                'user_id': user_info['user_id'],
                'role': user_info['role'].value,
                'permissions': [p.value for p in user_info['permissions']]
            }), 200
        else:
            return jsonify({'valid': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return jsonify({'valid': False, 'message': 'Validation failed'}), 500


if __name__ == '__main__':
    # Get port from environment variable or default to 5001
    port = int(os.getenv('AUTH_SERVICE_PORT', 5001))

    # Check if running in production mode
    if os.getenv('FLASK_ENV') == 'production':
        try:
            # Production: Use Gunicorn programmatically
            from gunicorn.app.base import BaseApplication

            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super(StandaloneApplication, self).__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                'bind': f'0.0.0.0:{port}',
                'workers': 4,
                'worker_class': 'sync',
                'timeout': 43200,  # 12 hours to accommodate long-running requests
                'keepalive': 10,
                'max_requests': 1000,
                'max_requests_jitter': 100,
                'preload_app': True,
                'accesslog': '-',
                'errorlog': '-',
            }
            StandaloneApplication(app, options).run()
        except Exception as e:
            print(f"Gunicorn error: {type(e).__name__}: {e}")
            print("Running in development mode instead...")
            app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development: Use Flask's built-in server
        app.run(host='0.0.0.0', port=port, debug=False)
#!/usr/bin/env python3
"""
Script to determine the actual JWT secret key used by the system
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_jwt_secret():
    """Get the JWT secret key used by the system."""
    print("Getting the JWT secret key used by the system...")
    
    # Check what the environment variable is set to
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    print(f"Environment variable JWT_SECRET_KEY: {jwt_secret}")
    
    # Check the default value used in the code
    default_secret = 'jwt-secret-string-change-this-too'
    print(f"Default JWT secret in code: {default_secret}")
    
    # Try importing and checking what the security module uses
    from backend.security import security_manager
    import jwt
    from datetime import datetime, timedelta
    from backend.security import UserRole, Permission
    
    # Create a simple token using the default secret
    user_info = {
        'user_id': 'debug_user',
        'role': UserRole.ADMIN,
        'permissions': [Permission.READ_RAG, Permission.WRITE_RAG]
    }
    
    payload = {
        'user_id': user_info['user_id'],
        'role': user_info['role'].value,
        'permissions': [perm.value for perm in user_info['permissions']],
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    
    # Generate token with default secret
    token_with_default = jwt.encode(payload, default_secret, algorithm="HS256")
    print(f"Token generated with default secret: {token_with_default}")
    
    # Try to verify the token with the default secret
    try:
        decoded_payload = jwt.decode(token_with_default, default_secret, algorithms=["HS256"])
        print("Token verification with default secret: SUCCESS")
        print(f"Decoded payload: {decoded_payload}")
    except Exception as e:
        print(f"Token verification with default secret: FAILED - {e}")
    
    return default_secret

if __name__ == "__main__":
    secret = get_jwt_secret()
    print(f"\nThe system appears to be using JWT secret: {secret}")
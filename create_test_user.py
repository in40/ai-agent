#!/usr/bin/env python3
"""
Script to create a test user for API testing
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from database.user_db import user_db

def create_test_user():
    """Create a test user with known credentials"""
    print("Creating test user...")
    
    # Create a test user with known credentials
    username = "testuser"
    password = "testpass123"
    email = "test@example.com"
    
    # Check if user already exists
    existing_user = user_db.get_user(username)
    if existing_user:
        print(f"✓ Test user '{username}' already exists")
        return True
    
    # Create the user
    success = user_db.create_user(username, password, email, "admin")
    if success:
        print(f"✓ Test user '{username}' created successfully with password '{password}'")
        return True
    else:
        print(f"✗ Failed to create test user '{username}'")
        return False

if __name__ == "__main__":
    create_test_user()
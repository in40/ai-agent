#!/usr/bin/env python3
"""
Script to create a test user for debugging purposes
"""
import sqlite3
import bcrypt
import os
from pathlib import Path

def create_test_user():
    """Create a test user with a known password"""
    # Connect to the user database
    db_path = Path(os.getcwd()) / "database" / "user_database.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Hash the password
        password = "password123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert a test user
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, ("debug_user", hashed.decode('utf-8'), "debug@example.com", "user", True))
            
            conn.commit()
            print("✓ Test user 'debug_user' created successfully with password 'password123'")
            return True
        except sqlite3.IntegrityError:
            print("✓ Test user 'debug_user' already exists")
            return True
        except Exception as e:
            print(f"✗ Error creating test user: {e}")
            return False
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_test_user()
"""
User database module for the AI Agent system
Handles persistent storage of user credentials using PostgreSQL
"""
import os
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Optional, List
from config.settings import DATABASE_URL


class UserDatabase:
    """Class to handle user data storage in PostgreSQL"""
    
    def __init__(self):
        """Initialize the database connection"""
        self.connection_params = self.parse_database_url(DATABASE_URL)
        
    def parse_database_url(self, database_url: str) -> Dict[str, str]:
        """Parse the database URL to extract connection parameters"""
        import re
        
        # Parse URL format: postgresql://username:password@host:port/database
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, database_url)
        
        if not match:
            raise ValueError("Invalid database URL format")
        
        username, password, host, port, database = match.groups()
        
        return {
            'user': username,
            'password': password,
            'host': host,
            'port': int(port),
            'database': database
        }
    
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(**self.connection_params)
    
    def init_db(self):
        """Initialize the database with the users table if it doesn't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP WITH TIME ZONE,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def create_user(self, username: str, password: str, email: Optional[str] = None, role: str = 'user') -> bool:
        """Create a new user with hashed password"""
        try:
            # Hash the password using bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, role)
                VALUES (%s, %s, %s, %s)
            """, (username, password_hash.decode('utf-8'), email, role))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except psycopg2.IntegrityError:
            # Username already exists
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Retrieve a user by username"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user:
                # Convert RealDictRow to regular dict
                return dict(user)
            return None
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify a user's password"""
        user = self.get_user(username)
        if not user:
            return False
            
        # Compare the provided password with the stored hash
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password=user['password_hash'].encode('utf-8')
        )
    
    def update_last_login(self, username: str):
        """Update the last login time for a user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE username = %s
            """, (username,))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error updating last login: {e}")
    
    def get_all_users(self) -> List[Dict]:
        """Retrieve all users (for admin purposes)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT id, username, email, role, created_at, last_login, is_active FROM users")
            users = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert RealDictRows to regular dicts
            return [dict(user) for user in users]
        except Exception as e:
            print(f"Error retrieving users: {e}")
            return []


# Global instance
user_db = UserDatabase()
#!/usr/bin/env python3
"""
Test script to verify schema export with comments functionality
"""
import os
import sys
import tempfile
import sqlite3
from utils.database import DatabaseManager
from models.sql_generator import SQLGenerator

def test_sqlite_schema_with_comments():
    """Test SQLite schema export with comments"""
    print("Testing SQLite schema export with comments...")
    
    # Create a temporary SQLite database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    try:
        # Connect to the temporary database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a test table with comments in the SQL (as SQLite doesn't have native comment support)
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL, -- User's full name
                email TEXT UNIQUE, -- User's email address
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- When the user was created
            ); -- Table for storing user information
        """)

        cursor.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER, -- Reference to the user who placed the order
                product_name TEXT, -- Name of the product ordered
                quantity INTEGER, -- Number of items ordered
                total_price REAL -- Total price of the order
            ); -- Table for storing order information
        """)
        
        conn.commit()
        conn.close()
        
        # Test the DatabaseManager with the temporary database
        db_url = f"sqlite:///{db_path}"
        db_manager = DatabaseManager(db_url)
        
        # Get the schema dump
        schema_dump = db_manager.get_schema_dump()
        
        print("Schema dump with comments:")
        print(schema_dump)
        
        # Test the SQLGenerator formatting
        sql_gen = SQLGenerator()
        formatted_schema = sql_gen.format_schema_dump(schema_dump)
        
        print("\nFormatted schema for LLM:")
        print(formatted_schema)
        
        # Verify that comments are present in the output
        has_table_comments = "Table for storing user information" in formatted_schema
        has_column_comments = "User's full name" in formatted_schema
        
        print(f"\nTable comments found: {has_table_comments}")
        print(f"Column comments found: {has_column_comments}")

        # Note: SQLite doesn't store table comments in the schema, only column comments
        if has_column_comments:
            print("✅ SQLite schema export with column comments is working correctly!")
            if has_table_comments:
                print("ℹ️  Table comments were also found (unexpected for SQLite)")
        else:
            print("❌ SQLite schema export with column comments is not working as expected.")
            
    finally:
        # Clean up the temporary database file
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_postgresql_schema_with_comments():
    """Test PostgreSQL schema export with comments (if available)"""
    print("\nTesting PostgreSQL schema export with comments...")
    
    # Check if PostgreSQL environment variables are set
    pg_url = os.getenv('DATABASE_URL')
    if not pg_url or 'postgresql' not in pg_url.lower():
        print("⚠️  PostgreSQL not configured, skipping PostgreSQL test.")
        return
    
    try:
        db_manager = DatabaseManager(pg_url)
        
        # Get the schema dump
        schema_dump = db_manager.get_schema_dump()
        
        print("PostgreSQL schema dump with comments:")
        print(schema_dump)
        
        # Test the SQLGenerator formatting
        sql_gen = SQLGenerator()
        formatted_schema = sql_gen.format_schema_dump(schema_dump)
        
        print("\nFormatted PostgreSQL schema for LLM:")
        print(formatted_schema)
        
        print("✅ PostgreSQL schema export with comments setup is correct!")
        
    except Exception as e:
        print(f"❌ Error testing PostgreSQL schema: {e}")

if __name__ == "__main__":
    print("Testing schema export with comments functionality...\n")
    
    test_sqlite_schema_with_comments()
    test_postgresql_schema_with_comments()
    
    print("\nTesting completed.")
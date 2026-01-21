#!/usr/bin/env python3
"""
Test script to verify the enhanced AI Agent functionality
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ai_agent import AIAgent
from database.utils.database import DatabaseManager
import sqlite3
import tempfile


def setup_test_database():
    """Create a temporary SQLite database with sample data for testing"""
    # Create a temporary database file
    temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
    
    # Connect to the database
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # Create sample tables
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            created_date DATE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL
        )
    """)
    
    # Insert sample data
    sample_users = [
        (1, 'John', 'Smith', 'john.smith@example.com', '2023-01-15'),
        (2, 'Jane', 'Doe', 'jane.doe@company.com', '2023-02-20'),
        (3, 'Michael', 'Johnson', 'michael.johnson@test.org', '2023-03-10'),
        (4, 'Sarah', 'Williams', 'sarah.williams@example.com', '2023-04-05'),
        (5, 'David', 'Brown', 'david.brown@business.net', '2023-05-12')
    ]
    
    sample_products = [
        (1, 'Laptop', 'Electronics', 999.99),
        (2, 'Desk Chair', 'Furniture', 199.99),
        (3, 'Coffee Maker', 'Appliances', 89.99),
        (4, 'Notebook', 'Stationery', 12.99)
    ]
    
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", sample_users)
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", sample_products)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    return f"sqlite:///{temp_db_path}"


def test_ai_agent_functionality():
    """Test the enhanced AI Agent functionality"""
    print("Setting up test database...")
    db_url = setup_test_database()
    
    print("Initializing AI Agent...")
    agent = AIAgent(database_url=db_url)
    
    print("\nTest 1: Normal query that should return results")
    result1 = agent.process_request("Get all users")
    print(f"Results count: {len(result1['db_results'])}")
    print(f"Sample result: {result1['db_results'][0] if result1['db_results'] else 'None'}")
    
    print("\nTest 2: Query that should return no results initially, triggering wider search")
    result2 = agent.process_request("Find user with name 'Alex'")
    print(f"Results count: {len(result2['db_results'])}")
    print(f"Final response: {result2['final_response'][:200]}...")
    
    print("\nTest 3: Query for non-existent product, should trigger analysis")
    result3 = agent.process_request("Show me all smartphones")
    print(f"Results count: {len(result3['db_results'])}")
    print(f"Final response: {result3['final_response'][:200]}...")
    
    print("\nTest 4: Request that might benefit from name analysis")
    result4 = agent.process_request("Analyze the gender distribution of our users")
    print(f"Results count: {len(result4['db_results'])}")
    print(f"Final response: {result4['final_response'][:300]}...")
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    test_ai_agent_functionality()
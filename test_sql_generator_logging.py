#!/usr/bin/env python3
"""
Simple test to verify that the logging changes work properly
"""
import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.sql_generator import SQLGenerator
from utils.database import DatabaseManager

def test_sql_generator_logging():
    """Test that SQL generator logs full schema without truncation"""
    
    print("Testing SQL Generator logging...")
    
    # Enable screen logging
    os.environ['ENABLE_SCREEN_LOGGING'] = 'true'
    
    # Set up logging to see the output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a sample schema dump
    sample_schema = {
        "users": [
            {"name": "id", "type": "integer", "nullable": False, "comment": "Primary key identifier"},
            {"name": "username", "type": "varchar(50)", "nullable": False, "comment": "Unique username"},
            {"name": "email", "type": "varchar(100)", "nullable": False, "comment": "Email address"},
            {"name": "created_at", "type": "timestamp", "nullable": True, "comment": "Account creation timestamp"}
        ],
        "orders": [
            {"name": "id", "type": "integer", "nullable": False, "comment": "Primary key identifier"},
            {"name": "user_id", "type": "integer", "nullable": False, "comment": "Foreign key to users table"},
            {"name": "order_date", "type": "date", "nullable": False, "comment": "Date of the order"},
            {"name": "total_amount", "type": "decimal(10,2)", "nullable": False, "comment": "Total order amount"}
        ],
        "products": [
            {"name": "id", "type": "integer", "nullable": False, "comment": "Primary key identifier"},
            {"name": "name", "type": "varchar(200)", "nullable": False, "comment": "Product name"},
            {"name": "price", "type": "decimal(8,2)", "nullable": False, "comment": "Product price"},
            {"name": "category", "type": "varchar(100)", "nullable": True, "comment": "Product category"},
            {"name": "description", "type": "text", "nullable": True, "comment": "Detailed product description"}
        ]
    }
    
    # Create an SQL generator instance
    sql_gen = SQLGenerator()
    
    # Generate SQL to trigger the logging
    print("\nGenerating SQL query to trigger full logging...")
    try:
        sql_query = sql_gen.generate_sql("Find all users who placed orders over $100", sample_schema)
        print(f"\nGenerated SQL: {sql_query}")
    except Exception as e:
        print(f"Expected error (due to missing LLM config): {e}")
    
    print("\nCompleted test of SQL generator logging.")
    print("Check the logs above to confirm that full schema details are displayed without truncation.")

if __name__ == "__main__":
    test_sql_generator_logging()
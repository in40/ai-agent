#!/usr/bin/env python3
"""
Database initialization script for the AI Agent application.
This script creates the required tables in the configured database.
"""

import os
import sys
from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL


def init_contacts_db():
    """Initialize the contacts database with required tables."""
    print("Initializing contacts database...")
    
    # Create database engine
    engine = create_engine(DATABASE_URL)
    
    # Create contacts table
    contacts_table_sql = """
    CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        phone VARCHAR(50),
        country VARCHAR(100),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Create arrest_records table
    arrest_records_table_sql = """
    CREATE TABLE IF NOT EXISTS arrest_records (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        full_name VARCHAR(255),
        race VARCHAR(50),
        sex VARCHAR(20),
        age INTEGER,
        arrest_date DATE,
        charge VARCHAR(255),
        case_status VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with engine.connect() as conn:
            # Execute table creation queries
            conn.execute(text(contacts_table_sql))
            conn.execute(text(arrest_records_table_sql))
            
            # Commit the transaction
            conn.commit()
            
        print("Tables created successfully!")
        
        # Insert sample data for testing
        insert_sample_data(engine)
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def insert_sample_data(engine):
    """Insert sample data into the tables."""
    print("Inserting sample data...")

    try:
        with engine.connect() as conn:
            # Insert sample contacts
            contacts_data = [
                {"id": 1, "name": 'John Doe', "phone": '555-1234', "country": 'USA', "is_active": True},
                {"id": 2, "name": 'Jane Smith', "phone": '555-5678', "country": 'Asia', "is_active": True},
                {"id": 3, "name": 'Bob Johnson', "phone": '555-9012', "country": 'Europe', "is_active": True},
                {"id": 4, "name": 'Alice Williams', "phone": '555-3456', "country": 'Asia', "is_active": True},
                {"id": 5, "name": 'Charlie Brown', "phone": '555-7890', "country": 'Africa', "is_active": False},
            ]

            for contact in contacts_data:
                conn.execute(
                    text("INSERT INTO contacts (id, name, phone, country, is_active) VALUES (:id, :name, :phone, :country, :is_active) "
                         "ON CONFLICT (id) DO NOTHING"),
                    contact
                )

            # Insert sample arrest records
            arrest_data = [
                {"id": 1, "first_name": 'Jane', "last_name": 'Smith', "full_name": 'Jane Smith', "race": 'Asian', "sex": 'Female', "age": 28, "arrest_date": '2023-05-15', "charge": 'Traffic Violation', "case_status": 'Closed'},
                {"id": 2, "first_name": 'Alice', "last_name": 'Williams', "full_name": 'Alice Williams', "race": 'Asian', "sex": 'Female', "age": 32, "arrest_date": '2023-06-20', "charge": 'Public Disturbance', "case_status": 'Open'},
                {"id": 3, "first_name": 'John', "last_name": 'Doe', "full_name": 'John Doe', "race": 'Caucasian', "sex": 'Male', "age": 35, "arrest_date": '2023-07-10', "charge": 'DUI', "case_status": 'Closed'},
            ]

            for arrest in arrest_data:
                conn.execute(
                    text("INSERT INTO arrest_records (id, first_name, last_name, full_name, race, sex, age, arrest_date, charge, case_status) "
                         "VALUES (:id, :first_name, :last_name, :full_name, :race, :sex, :age, :arrest_date, :charge, :case_status) ON CONFLICT (id) DO NOTHING"),
                    arrest
                )

            # Commit the transaction
            conn.commit()

        print("Sample data inserted successfully!")

    except Exception as e:
        print(f"Error inserting sample data: {e}")
        raise


def main():
    """Main function to run the database initialization."""
    print("Starting database initialization...")
    
    # Check if DATABASE_URL is configured
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not configured in environment variables.")
        return 1
    
    print(f"Using database URL: {DATABASE_URL}")
    
    try:
        init_contacts_db()
        print("\nDatabase initialization completed successfully!")
        return 0
    except Exception as e:
        print(f"\nDatabase initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Initialize Ingestion Jobs Database Tables
Creates tables for long-term job storage
"""
import os
import sys

# Add project root to path
sys.path.insert(0, '/root/qwen/ai_agent')

from sqlalchemy import text
from database.utils.database import get_db_manager

def init_ingestion_jobs_db():
    """Create ingestion jobs tables"""
    
    schema_file = '/root/qwen/ai_agent/database/ingestion_jobs_schema.sql'
    
    if not os.path.exists(schema_file):
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    # Read schema
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    
    # Get database manager
    db_manager = get_db_manager()
    if not db_manager:
        print("❌ Could not get database manager")
        return False
    
    try:
        # Execute schema using SQLAlchemy
        with db_manager.engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()
        print("✅ Ingestion jobs tables created successfully!")
        print("\nTables created:")
        print("  - ingestion_jobs (main job storage)")
        print("  - ingestion_job_files (processed files)")
        print("  - ingestion_job_chunks (text chunks)")
        print("  - ingestion_job_activity (audit trail)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Initializing Ingestion Jobs Database...")
    print("=" * 50)
    
    if init_ingestion_jobs_db():
        print("\n✅ Database initialization complete!")
        sys.exit(0)
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)

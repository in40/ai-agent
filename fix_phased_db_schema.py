#!/usr/bin/env python
"""Fix database schema for phased processing"""
from database.utils.database import get_db_manager
from sqlalchemy import text

db = get_db_manager()

print("Fixing database schema...")

try:
    with db.engine.connect() as conn:
        # 1. Drop the old unique constraint
        print("1. Dropping unique_doc_id constraint...")
        conn.execute(text('ALTER TABLE document_processing DROP CONSTRAINT IF EXISTS unique_doc_id'))
        conn.commit()
        print("   ✅ Done")
        
        # 2. Add composite unique constraint (ignore if exists)
        print("2. Adding composite unique constraint (doc_id, job_id)...")
        try:
            conn.execute(text('ALTER TABLE document_processing ADD CONSTRAINT unique_doc_job UNIQUE (doc_id, job_id)'))
            conn.commit()
            print("   ✅ Constraint added")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️  Constraint already exists (OK)")
            else:
                raise
        
        print()
        print("✅ Database schema fixed!")
except Exception as e:
    print(f"⚠️  Warning: {e}")
    print("   Continuing anyway (constraint may already be correct)")

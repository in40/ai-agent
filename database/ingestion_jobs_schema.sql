-- Ingestion Jobs Schema for Long-term Storage
-- Supports hybrid Redis + PostgreSQL job storage

-- Main jobs table
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    job_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    ingestion_mode VARCHAR(32) DEFAULT 'files',
    processing_mode VARCHAR(32) DEFAULT 'vector_db',
    chunking_strategy VARCHAR(32) DEFAULT 'smart_chunking',
    source_url TEXT,
    source_type VARCHAR(32),
    progress INTEGER DEFAULT 0,
    current_stage VARCHAR(64),
    documents_total INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    chunks_generated INTEGER DEFAULT 0,
    result JSONB,
    error TEXT,
    error_details JSONB,
    extraction_methods_used JSONB,
    processing_time_seconds FLOAT,
    encoding_fixes_applied INTEGER DEFAULT 0,
    neo4j_nodes_created INTEGER DEFAULT 0,
    neo4j_relationships_created INTEGER DEFAULT 0,
    neo4j_entities_extracted INTEGER DEFAULT 0,
    vector_db_chunks_ingested INTEGER DEFAULT 0,
    vector_db_collection_name VARCHAR(128)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_user_id ON ingestion_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_created_at ON ingestion_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_job_type ON ingestion_jobs(job_type);

-- Processed files table
CREATE TABLE IF NOT EXISTS ingestion_job_files (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL REFERENCES ingestion_jobs(job_id) ON DELETE CASCADE,
    original_filename VARCHAR(512) NOT NULL,
    stored_filename VARCHAR(512),
    file_path TEXT,
    file_size_bytes BIGINT,
    file_format VARCHAR(16),
    status VARCHAR(32) DEFAULT 'pending',
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    extraction_method VARCHAR(64),
    extraction_time_seconds FLOAT,
    text_length INTEGER,
    cyrillic_ratio FLOAT,
    encoding_was_fixed BOOLEAN DEFAULT FALSE,
    mojibake_detected BOOLEAN DEFAULT FALSE,
    chunks_created INTEGER DEFAULT 0,
    chunks_ingested BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    error_details JSONB
);

CREATE INDEX IF NOT EXISTS idx_job_files_job_id ON ingestion_job_files(job_id);
CREATE INDEX IF NOT EXISTS idx_job_files_status ON ingestion_job_files(status);
CREATE INDEX IF NOT EXISTS idx_job_files_format ON ingestion_job_files(file_format);

-- Job chunks table
CREATE TABLE IF NOT EXISTS ingestion_job_chunks (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL REFERENCES ingestion_jobs(job_id) ON DELETE CASCADE,
    file_id INTEGER REFERENCES ingestion_job_files(id) ON DELETE SET NULL,
    chunk_id VARCHAR(64) UNIQUE NOT NULL,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    content_length INTEGER,
    metadata JSONB,
    entities_extracted JSONB,
    vector_db_id VARCHAR(128),
    vector_db_collection VARCHAR(128),
    embedding_model VARCHAR(128),
    neo4j_node_id VARCHAR(128),
    neo4j_relationships JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_job_chunks_job_id ON ingestion_job_chunks(job_id);
CREATE INDEX IF NOT EXISTS idx_job_chunks_file_id ON ingestion_job_chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_job_chunks_chunk_id ON ingestion_job_chunks(chunk_id);

-- Job activity log
CREATE TABLE IF NOT EXISTS ingestion_job_activity (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL REFERENCES ingestion_jobs(job_id) ON DELETE CASCADE,
    activity_type VARCHAR(64) NOT NULL,
    activity_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    old_value TEXT,
    new_value TEXT,
    details JSONB,
    user_id VARCHAR(64),
    system_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_job_activity_job_id ON ingestion_job_activity(job_id);
CREATE INDEX IF NOT EXISTS idx_job_activity_timestamp ON ingestion_job_activity(activity_timestamp);
CREATE INDEX IF NOT EXISTS idx_job_activity_type ON ingestion_job_activity(activity_type);

-- Comments
COMMENT ON TABLE ingestion_jobs IS 'Long-term storage for smart ingestion jobs (hybrid with Redis)';
COMMENT ON TABLE ingestion_job_files IS 'Individual files processed within ingestion jobs';
COMMENT ON TABLE ingestion_job_chunks IS 'Text chunks created during job processing';
COMMENT ON TABLE ingestion_job_activity IS 'Audit trail for job state changes';

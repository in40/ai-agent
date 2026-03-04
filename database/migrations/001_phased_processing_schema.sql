-- Phased Document Processing Pipeline Schema
-- Migration: v0.8.16 - Phase-based processing with checkpointing
-- Date: 2026-03-01
-- 
-- This schema adds support for:
-- 1. Multi-phase document processing (upload → extract → chunk → vector → graph)
-- 2. Per-document phase tracking
-- 3. Checkpointing for recovery
-- 4. Versioning for re-processing
-- 5. Document Store integration

-- ============================================================================
-- TABLE: document_processing
-- Tracks individual documents through all processing phases
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_processing (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    
    -- File information
    original_filename VARCHAR(500) NOT NULL,
    display_name VARCHAR(200),
    file_path TEXT,
    file_size BIGINT,
    content_type VARCHAR(100),
    source_url TEXT,
    source_website VARCHAR(255),
    
    -- Phase status tracking (each phase: PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED)
    phase_upload VARCHAR(50) DEFAULT 'PENDING',
    phase_extract VARCHAR(50) DEFAULT 'PENDING',
    phase_chunk VARCHAR(50) DEFAULT 'PENDING',
    phase_vector VARCHAR(50) DEFAULT 'PENDING',
    phase_graph VARCHAR(50) DEFAULT 'PENDING',
    
    -- Current processing state
    current_phase VARCHAR(50) DEFAULT 'upload',
    overall_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED, PAUSED
    
    -- Extraction metadata (Phase 2)
    extraction_method VARCHAR(50),  -- pymupdf, pdfminer, pypdf, tesseract
    extraction_attempts INTEGER DEFAULT 0,
    page_count INTEGER,
    extracted_char_count INTEGER,
    encoding_issues_fixed INTEGER DEFAULT 0,
    
    -- Chunking metadata (Phase 3)
    chunk_count INTEGER DEFAULT 0,
    chunking_strategy VARCHAR(50),  -- smart_llm, fixed_size, paragraph
    chunking_model VARCHAR(100),
    
    -- Vector metadata (Phase 4)
    vector_collection VARCHAR(100),
    vector_chunk_count INTEGER DEFAULT 0,
    embedding_model VARCHAR(100),
    
    -- Graph metadata (Phase 5)
    entity_count INTEGER DEFAULT 0,
    relationship_count INTEGER DEFAULT 0,
    graph_model VARCHAR(100),
    
    -- Error tracking
    last_error TEXT,
    last_error_phase VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps for each phase
    uploaded_at TIMESTAMP WITH TIME ZONE,
    extracted_at TIMESTAMP WITH TIME ZONE,
    chunked_at TIMESTAMP WITH TIME ZONE,
    indexed_at TIMESTAMP WITH TIME ZONE,
    graph_built_at TIMESTAMP WITH TIME ZONE,
    
    -- System fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_doc_id UNIQUE (doc_id)
);

-- Indexes for document_processing
CREATE INDEX IF NOT EXISTS idx_doc_processing_job_id ON document_processing(job_id);
CREATE INDEX IF NOT EXISTS idx_doc_processing_user_id ON document_processing(user_id);
CREATE INDEX IF NOT EXISTS idx_doc_processing_doc_id ON document_processing(doc_id);
CREATE INDEX IF NOT EXISTS idx_doc_processing_status ON document_processing(overall_status);
CREATE INDEX IF NOT EXISTS idx_doc_processing_current_phase ON document_processing(current_phase);

-- ============================================================================
-- TABLE: phase_execution_log
-- Detailed execution log for each phase (audit trail + debugging)
-- ============================================================================

CREATE TABLE IF NOT EXISTS phase_execution_log (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,  -- Groups related executions (e.g., batch run)
    job_id VARCHAR(255) NOT NULL,
    doc_id VARCHAR(255),
    phase VARCHAR(50) NOT NULL,  -- upload, extract, chunk, vector, graph
    
    -- Execution details
    action VARCHAR(50) NOT NULL,  -- START, COMPLETE, FAIL, RETRY, SKIP
    status VARCHAR(50) NOT NULL,  -- SUCCESS, FAILURE, PARTIAL
    error_message TEXT,
    
    -- Performance metrics
    processing_time_ms INTEGER,
    items_processed INTEGER,  -- e.g., pages extracted, chunks created
    
    -- Configuration snapshot (what settings were used)
    config_snapshot JSONB,
    
    -- Additional metadata (phase-specific)
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for phase_execution_log
CREATE INDEX IF NOT EXISTS idx_phase_log_job_id ON phase_execution_log(job_id);
CREATE INDEX IF NOT EXISTS idx_phase_log_doc_id ON phase_execution_log(doc_id);
CREATE INDEX IF NOT EXISTS idx_phase_log_phase ON phase_execution_log(phase);
CREATE INDEX IF NOT EXISTS idx_phase_log_execution_id ON phase_execution_log(execution_id);
CREATE INDEX IF NOT EXISTS idx_phase_log_created_at ON phase_execution_log(created_at);

-- ============================================================================
-- TABLE: chunks_cache
-- Stores chunking results for recovery and re-processing
-- ============================================================================

CREATE TABLE IF NOT EXISTS chunks_cache (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) NOT NULL,
    chunk_id VARCHAR(100) NOT NULL,
    chunk_index INTEGER NOT NULL,
    
    -- Chunk content
    content TEXT NOT NULL,
    content_length INTEGER,
    
    -- Chunk metadata
    section VARCHAR(500),
    title VARCHAR(500),
    chunk_type VARCHAR(50) DEFAULT 'text',  -- text, table, formula, image
    token_count INTEGER,
    start_char INTEGER,
    end_char INTEGER,
    contains_formula BOOLEAN DEFAULT FALSE,
    contains_table BOOLEAN DEFAULT FALSE,
    
    -- Entity hints from LLM
    entity_hints TEXT[],  -- Array of entity names
    
    -- Versioning (for re-processing with different strategies)
    version VARCHAR(50) DEFAULT 'v1',
    version_label VARCHAR(200),  -- e.g., "smart_llm_test", "fixed_512"
    is_active BOOLEAN DEFAULT TRUE,  -- False if superseded by newer version
    
    -- Vector DB reference
    vector_id VARCHAR(255),  -- ID in Qdrant
    vector_collection VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_chunk UNIQUE (doc_id, chunk_id, version)
);

-- Indexes for chunks_cache
CREATE INDEX IF NOT EXISTS idx_chunks_cache_doc_id ON chunks_cache(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_cache_chunk_id ON chunks_cache(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunks_cache_version ON chunks_cache(doc_id, version);
CREATE INDEX IF NOT EXISTS idx_chunks_cache_active ON chunks_cache(doc_id, is_active);
CREATE INDEX IF NOT EXISTS idx_chunks_cache_vector_id ON chunks_cache(vector_id);

-- ============================================================================
-- TABLE: entities_cache
-- Stores extracted entities for recovery and re-processing
-- ============================================================================

CREATE TABLE IF NOT EXISTS entities_cache (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) NOT NULL,
    chunk_id VARCHAR(100),
    
    -- Entity details
    entity_name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(100),  -- PERSON, ORGANIZATION, CONCEPT, STANDARD, etc.
    relevance_score FLOAT,  -- 0.0 to 1.0
    
    -- Entity context
    context_snippet TEXT,  -- Surrounding text
    mentions_count INTEGER DEFAULT 1,
    
    -- Neo4j references
    neo4j_node_id VARCHAR(255),
    neo4j_labels TEXT[],
    
    -- Versioning
    version VARCHAR(50) DEFAULT 'v1',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_entity UNIQUE (doc_id, entity_name, version)
);

-- Indexes for entities_cache
CREATE INDEX IF NOT EXISTS idx_entities_cache_doc_id ON entities_cache(doc_id);
CREATE INDEX IF NOT EXISTS idx_entities_cache_entity_name ON entities_cache(entity_name);
CREATE INDEX IF NOT EXISTS idx_entities_cache_type ON entities_cache(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_cache_neo4j_id ON entities_cache(neo4j_node_id);

-- ============================================================================
-- TABLE: relationships_cache
-- Stores extracted relationships for recovery and re-processing
-- ============================================================================

CREATE TABLE IF NOT EXISTS relationships_cache (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) NOT NULL,
    
    -- Relationship endpoints
    source_entity VARCHAR(500) NOT NULL,
    target_entity VARCHAR(500) NOT NULL,
    
    -- Relationship details
    relationship_type VARCHAR(100) NOT NULL,  -- RELATED_TO, EXTENDS, SUPERSEDES, etc.
    relationship_properties JSONB,  -- Additional properties
    
    -- Neo4j reference
    neo4j_relationship_id VARCHAR(255),
    
    -- Versioning
    version VARCHAR(50) DEFAULT 'v1',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for relationships_cache
CREATE INDEX IF NOT EXISTS idx_relationships_cache_doc_id ON relationships_cache(doc_id);
CREATE INDEX IF NOT EXISTS idx_relationships_cache_source ON relationships_cache(source_entity);
CREATE INDEX IF NOT EXISTS idx_relationships_cache_target ON relationships_cache(target_entity);

-- ============================================================================
-- TABLE: reprocessing_history
-- Tracks re-processing operations for audit and rollback
-- ============================================================================

CREATE TABLE IF NOT EXISTS reprocessing_history (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) NOT NULL,
    job_id VARCHAR(255) NOT NULL,
    
    -- What was re-processed
    phases_rerun TEXT[],  -- e.g., ['chunk', 'vector']
    phases_preserved TEXT[],  -- e.g., ['extract']
    
    -- Configuration changes
    old_config JSONB,
    new_config JSONB,
    
    -- Versioning
    previous_version VARCHAR(50),
    new_version VARCHAR(50),
    
    -- Result
    status VARCHAR(50) NOT NULL,  -- SUCCESS, FAILURE, PARTIAL
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for reprocessing_history
CREATE INDEX IF NOT EXISTS idx_reprocessing_doc_id ON reprocessing_history(doc_id);
CREATE INDEX IF NOT EXISTS idx_reprocessing_job_id ON reprocessing_history(job_id);

-- ============================================================================
-- VIEWS for common queries
-- ============================================================================

-- View: Document processing status summary
CREATE OR REPLACE VIEW v_document_status AS
SELECT 
    doc_id,
    job_id,
    original_filename,
    display_name,
    overall_status,
    current_phase,
    phase_upload,
    phase_extract,
    phase_chunk,
    phase_vector,
    phase_graph,
    chunk_count,
    entity_count,
    last_error,
    retry_count,
    created_at,
    updated_at
FROM document_processing;

-- View: Job-level phase progress
CREATE OR REPLACE VIEW v_job_phase_progress AS
SELECT 
    job_id,
    COUNT(*) AS documents_total,
    
    -- Upload phase
    COUNT(*) FILTER (WHERE phase_upload = 'COMPLETED') AS upload_completed,
    COUNT(*) FILTER (WHERE phase_upload = 'FAILED') AS upload_failed,
    COUNT(*) FILTER (WHERE phase_upload = 'PENDING') AS upload_pending,
    
    -- Extract phase
    COUNT(*) FILTER (WHERE phase_extract = 'COMPLETED') AS extract_completed,
    COUNT(*) FILTER (WHERE phase_extract = 'FAILED') AS extract_failed,
    COUNT(*) FILTER (WHERE phase_extract = 'PENDING') AS extract_pending,
    
    -- Chunk phase
    COUNT(*) FILTER (WHERE phase_chunk = 'COMPLETED') AS chunk_completed,
    COUNT(*) FILTER (WHERE phase_chunk = 'FAILED') AS chunk_failed,
    COUNT(*) FILTER (WHERE phase_chunk = 'PENDING') AS chunk_pending,
    
    -- Vector phase
    COUNT(*) FILTER (WHERE phase_vector = 'COMPLETED') AS vector_completed,
    COUNT(*) FILTER (WHERE phase_vector = 'FAILED') AS vector_failed,
    COUNT(*) FILTER (WHERE phase_vector = 'PENDING') AS vector_pending,
    
    -- Graph phase
    COUNT(*) FILTER (WHERE phase_graph = 'COMPLETED') AS graph_completed,
    COUNT(*) FILTER (WHERE phase_graph = 'FAILED') AS graph_failed,
    COUNT(*) FILTER (WHERE phase_graph = 'PENDING') AS graph_pending,
    
    -- Overall
    COUNT(*) FILTER (WHERE overall_status = 'COMPLETED') AS fully_completed,
    COUNT(*) FILTER (WHERE overall_status = 'FAILED') AS fully_failed,
    COUNT(*) FILTER (WHERE overall_status = 'PROCESSING') AS in_progress
    
FROM document_processing
GROUP BY job_id;

-- ============================================================================
-- FUNCTIONS for common operations
-- ============================================================================

-- Function: Update document phase status
CREATE OR REPLACE FUNCTION update_document_phase(
    p_doc_id VARCHAR,
    p_phase VARCHAR,
    p_status VARCHAR,
    p_metadata JSONB DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    phase_column TEXT;
    update_query TEXT;
BEGIN
    -- Map phase name to column name
    phase_column := 'phase_' || p_phase;
    
    -- Update the phase status
    EXECUTE format(
        'UPDATE document_processing SET %s = %L, updated_at = NOW() WHERE doc_id = %L',
        phase_column,
        p_status,
        p_doc_id
    );
    
    -- Log the execution
    INSERT INTO phase_execution_log (execution_id, job_id, doc_id, phase, action, status, metadata, created_at)
    SELECT 
        gen_random_uuid()::TEXT,
        job_id,
        p_doc_id,
        p_phase,
        'COMPLETE',
        CASE WHEN p_status = 'COMPLETED' THEN 'SUCCESS' WHEN p_status = 'FAILED' THEN 'FAILURE' ELSE 'PARTIAL' END,
        p_metadata,
        NOW()
    FROM document_processing
    WHERE doc_id = p_doc_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get documents ready for next phase
CREATE OR REPLACE FUNCTION get_documents_ready_for_phase(
    p_job_id VARCHAR,
    p_phase VARCHAR
)
RETURNS TABLE (
    doc_id VARCHAR,
    original_filename VARCHAR,
    file_path TEXT,
    current_status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dp.doc_id,
        dp.original_filename,
        dp.file_path,
        dp.overall_status
    FROM document_processing dp
    WHERE dp.job_id = p_job_id
    AND dp.overall_status IN ('PENDING', 'PROCESSING')
    AND CASE 
        WHEN p_phase = 'extract' THEN dp.phase_upload = 'COMPLETED' AND dp.phase_extract IN ('PENDING', 'FAILED')
        WHEN p_phase = 'chunk' THEN dp.phase_extract = 'COMPLETED' AND dp.phase_chunk IN ('PENDING', 'FAILED')
        WHEN p_phase = 'vector' THEN dp.phase_chunk = 'COMPLETED' AND dp.phase_vector IN ('PENDING', 'FAILED')
        WHEN p_phase = 'graph' THEN dp.phase_chunk = 'COMPLETED' AND dp.phase_graph IN ('PENDING', 'FAILED')
        ELSE FALSE
    END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS for documentation
-- ============================================================================

COMMENT ON TABLE document_processing IS 'Tracks individual documents through all processing phases (upload, extract, chunk, vector, graph)';
COMMENT ON TABLE phase_execution_log IS 'Detailed audit trail for phase executions with configuration snapshots';
COMMENT ON TABLE chunks_cache IS 'Persistent storage for chunking results, supports versioning and recovery';
COMMENT ON TABLE entities_cache IS 'Extracted entities with Neo4j references, supports versioning';
COMMENT ON TABLE relationships_cache IS 'Extracted relationships between entities with Neo4j references';
COMMENT ON TABLE reprocessing_history IS 'Audit trail for re-processing operations';

COMMENT ON FUNCTION update_document_phase IS 'Helper function to update phase status and log execution';
COMMENT ON FUNCTION get_documents_ready_for_phase IS 'Get documents that are ready to be processed in specified phase';

-- ============================================================================
-- MIGRATION NOTES
-- ============================================================================
-- 
-- To apply this migration:
-- 1. Ensure PostgreSQL connection is available
-- 2. Run: psql -d ai_agent -f 001_phased_processing_schema.sql
-- 
-- To rollback:
-- DROP TABLE IF EXISTS reprocessing_history CASCADE;
-- DROP TABLE IF EXISTS relationships_cache CASCADE;
-- DROP TABLE IF EXISTS entities_cache CASCADE;
-- DROP TABLE IF EXISTS chunks_cache CASCADE;
-- DROP TABLE IF EXISTS phase_execution_log CASCADE;
-- DROP TABLE IF EXISTS document_processing CASCADE;
-- DROP FUNCTION IF EXISTS get_documents_ready_for_phase CASCADE;
-- DROP FUNCTION IF EXISTS update_document_phase CASCADE;
-- DROP VIEW IF EXISTS v_job_phase_progress CASCADE;
-- DROP VIEW IF EXISTS v_document_status CASCADE;

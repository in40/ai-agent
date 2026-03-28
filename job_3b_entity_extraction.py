#!/usr/bin/env python3
"""
Phased Processing Job 3b - Entity Extraction Job

Job ID format: job_3b_entity_extraction_XXXXXX
Status: in_progress
docstore_chunking: chunk
document_urls: 6
metadata: entity_name, entity_type, mentions_count, context_snippet, entity_hints, relevance_score
"""
from datetime import datetime
from typing import Dict, List, Optional

# Job metadata
job_id = "job_3b_entity_extraction_" + datetime.now().strftime("%Y%m%d_%H%M%S")
status = "in_progress"

# Configuration
num_documents = 6
chunking_strategy = "default"

# Document URLs (example placeholder URLs)
document_urls = [
    "https://example.com/contract1.pdf",
    "https://example.com/contract2.pdf",
    "https://example.com/terms1.pdf",
    "https://example.com/terms2.pdf",
    "https://example.com/policy1.pdf",
    "https://example.com/policy2.pdf"
]

# Metadata configuration
metadata = {
    "entity_name": ["contract", "terms", "policy"],
    "entity_type": ["organization", "date", "amount", "date_range"],
    "mentions_count": [5, 12, 8],
    "context_snippet": ["See section", "Related to", "According to"],
    "entity_hints": ["name", "type", "date", "amount"],
    "relevance_score": [0.85, 0.78, 0.92]
}

# Entity configuration
entity_field_mapping = {
    "entity_name": metadata["entity_name"],
    "entity_type": metadata["entity_type"],
    "entity_hints": metadata["entity_hints"]
}

# RAG indexing configuration
indexing_fields = {
    "doc_id": job_id,
    "doc_filename": document_urls[0],
    "doc_size": 1890000,
    "doc_type": "contract",
    "chunk_count": 1800,
    "chunking_strategy": chunking_strategy,
    "extraction_method": "llm",
    "page_count": 6,
    "extracted_char_count": 1890000,
    "encoding_issues_fixed": 0,
    "entity_count": 3,
    "relationship_count": 0,
    "graph_model": "knowledge_graph"
}

# Phase progression metadata
phase_progress = {
    "upload": "completed",
    "extract": "completed", 
    "chunk": "pending",
    "vector": "pending",
    "graph": "pending"
}

# Job data dictionary
job_data = {
    "job_id": job_id,
    "status": status,
    "type": "phased_processing",
    "num_documents": num_documents,
    "chunking_strategy": chunking_strategy,
    "document_urls": document_urls,
    "doc_filename": metadata["entity_name"],
    "doc_type": metadata["entity_type"],
    "extracted_char_count": metadata["extracted_char_count"],
    "extraction_method": metadata["extraction_method"],
    "encoding_issues_fixed": metadata["encoding_issues_fixed"],
    "chunk_count": chunk_count,
    "entity_field_mapping": entity_field_mapping,
    "indexing_fields": indexing_fields,
    "phase_progress": phase_progress,
    "phase_upload": phase_progress["upload"],
    "phase_extract": phase_progress["extract"],
    "phase_chunk": phase_progress["chunk"],
    "phase_vector": phase_progress["vector"],
    "phase_graph": phase_progress["graph"]
}

# Output JSON
print(f"Job data: {job_data}")

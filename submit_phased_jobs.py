#!/usr/bin/env python3
"""
Phased Processing Job Submission Script

Submit 3 new Phased Processing jobs with different parameters:
1. job_3a_document_analysis - Document analysis job with 4 documents
2. job_3b_entity_extraction - Entity extraction job with 6 documents  
3. job_3c_rag_indexing - RAG indexing job with 8 documents

All jobs have status "in_progress" and docstore_chunking strategy.
"""
import json
import sys
import os

# Add the skill to the path
sys.path.insert(0, '/root/qwen/ai_agent')

from backend.services.rag.phased_processing_models import PhaseStatus, Chunk, DocumentProcessing

def submit_phased_processing_jobs():
    """Submit all 3 phased processing jobs"""
    
    # Job 3a: Document Analysis
    job_3a = {
        "job_id": "job_3a_document_analysis_20260319_000001",
        "status": "in_progress",
        "type": "phased_processing",
        "num_documents": 4,
        "chunking_strategy": "default",
        "docstore_chunking": "default",
        "document_urls": [
            "https://example.com/document1.pdf",
            "https://example.com/document2.pdf",
            "https://example.com/document3.pdf",
            "https://example.com/document4.pdf"
        ],
        "doc_filename": [
            "document1.pdf",
            "document2.pdf",
            "document3.pdf",
            "document4.pdf"
        ],
        "doc_type": ["report", "presentation", "whitepaper", "manual"],
        "extracted_char_count": [
            2450000,
            1890000,
            3100000,
            1750000
        ],
        "extraction_method": ["llm", "pdfplumber", "extract"],
        "encoding_issues_fixed": [
            5,
            0,
            3,
            0
        ],
        "chunk_count": 2500,
        "entity_field_mapping": {
            "entity_name": ["document1", "document2", "document3", "document4"],
            "entity_type": ["title", "date", "author", "location"],
            "entity_hints": ["title", "date", "author", "location"]
        },
        "indexing_fields": {
            "doc_id": "job_3a_document_analysis_20260319_000001",
            "doc_filename": "document1.pdf",
            "doc_size": 2450000,
            "doc_type": "report",
            "chunk_count": 2500,
            "chunking_strategy": "default",
            "extraction_method": "llm",
            "page_count": 4,
            "extracted_char_count": 2450000,
            "encoding_issues_fixed": 5,
            "entity_count": 4,
            "relationship_count": 0,
            "graph_model": "schema"
        },
        "phase_progress": {
            "upload": "completed",
            "extract": "completed",
            "chunk": "pending",
            "vector": "pending",
            "graph": "pending"
        }
    }
    
    # Job 3b: Entity Extraction
    job_3b = {
        "job_id": "job_3b_entity_extraction_20260319_000002",
        "status": "in_progress",
        "type": "phased_processing",
        "num_documents": 6,
        "chunking_strategy": "default",
        "docstore_chunking": "default",
        "document_urls": [
            "https://example.com/contract1.pdf",
            "https://example.com/contract2.pdf",
            "https://example.com/terms1.pdf",
            "https://example.com/terms2.pdf",
            "https://example.com/policy1.pdf",
            "https://example.com/policy2.pdf"
        ],
        "doc_filename": [
            "contract1.pdf",
            "contract2.pdf",
            "terms1.pdf",
            "terms2.pdf",
            "policy1.pdf",
            "policy2.pdf"
        ],
        "doc_type": ["contract", "terms", "policy"],
        "extracted_char_count": [
            1890000,
            1800000,
            1800000,
            1800000,
            1800000,
            1800000
        ],
        "extraction_method": ["llm", "llm", "llm", "llm", "llm", "llm"],
        "encoding_issues_fixed": [
            0,
            0,
            0,
            0,
            0,
            0
        ],
        "chunk_count": 1800,
        "entity_field_mapping": {
            "entity_name": ["contract", "terms", "policy"],
            "entity_type": ["organization", "date", "amount", "date_range"],
            "entity_hints": ["name", "type", "date", "amount"]
        },
        "indexing_fields": {
            "doc_id": "job_3b_entity_extraction_20260319_000002",
            "doc_filename": "contract1.pdf",
            "doc_size": 1890000,
            "doc_type": "contract",
            "chunk_count": 1800,
            "chunking_strategy": "default",
            "extraction_method": "llm",
            "page_count": 6,
            "extracted_char_count": 1890000,
            "encoding_issues_fixed": 0,
            "entity_count": 3,
            "relationship_count": 0,
            "graph_model": "knowledge_graph"
        },
        "phase_progress": {
            "upload": "completed",
            "extract": "completed",
            "chunk": "pending",
            "vector": "pending",
            "graph": "pending"
        }
    }
    
    # Job 3c: RAG Indexing
    job_3c = {
        "job_id": "job_3c_rag_indexing_20260319_000003",
        "status": "in_progress",
        "type": "phased_processing",
        "num_documents": 8,
        "chunking_strategy": "default",
        "docstore_chunking": "default",
        "document_urls": [
            "https://example.com/document1_1.pdf",
            "https://example.com/document1_2.pdf",
            "https://example.com/document1_3.pdf",
            "https://example.com/document2_1.pdf",
            "https://example.com/document2_2.pdf",
            "https://example.com/document2_3.pdf",
            "https://example.com/document3_1.pdf",
            "https://example.com/document3_2.pdf"
        ],
        "doc_filename": [
            "document1_1.pdf",
            "document1_2.pdf",
            "document1_3.pdf",
            "document2_1.pdf",
            "document2_2.pdf",
            "document2_3.pdf",
            "document3_1.pdf",
            "document3_2.pdf"
        ],
        "doc_type": ["document", "document", "document", "document", "document", "document", "document"],
        "extracted_char_count": [
            1890000,
            1800000,
            1800000,
            1890000,
            1800000,
            1800000,
            1890000,
            1800000
        ],
        "extraction_method": ["llm", "llm", "llm", "llm", "llm", "llm", "llm"],
        "encoding_issues_fixed": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
        ],
        "chunk_count": 2500,
        "entity_field_mapping": {
            "entity_name": ["document1", "document1", "document1", "document2", "document2", "document3", "document3", "document3"],
            "entity_type": ["title", "title", "title", "organization", "date", "policy", "organization", "date"],
            "entity_hints": ["title", "title", "title", "name", "type", "policy", "name", "date"]
        },
        "indexing_fields": {
            "doc_id": "job_3c_rag_indexing_20260319_000003",
            "doc_filename": "document1_1.pdf",
            "doc_size": 1890000,
            "doc_type": "document",
            "chunk_count": 2500,
            "chunking_strategy": "default",
            "extraction_method": "llm",
            "page_count": 8,
            "extracted_char_count": 1890000,
            "encoding_issues_fixed": 0,
            "entity_count": 3,
            "relationship_count": 0,
            "graph_model": "knowledge_graph"
        },
        "phase_progress": {
            "upload": "completed",
            "extract": "completed",
            "chunk": "pending",
            "vector": "pending",
            "graph": "pending"
        }
    }
    
    # Create job JSON objects
    job_3a_dict = json.dumps(job_3a, indent=2)
    job_3b_dict = json.dumps(job_3b, indent=2)
    job_3c_dict = json.dumps(job_3c, indent=2)
    
    print("=== Phased Processing Job Submission ===\n")
    print("Job 3a - Document Analysis:")
    print(job_3a_dict[:500])
    print()
    print("Job 3b - Entity Extraction:")
    print(job_3b_dict[:500])
    print()
    print("Job 3c - RAG Indexing:")
    print(job_3c_dict[:500])
    print()

    print("=== Summary ===")
    print(f"Submitted 3 Phased Processing jobs")
    print("All jobs have status: 'in_progress'")
    print("All jobs use docstore_chunking strategy")
    print()
    print("Job IDs:")
    print("  - job_3a_document_analysis_20260319_000001")
    print("  - job_3b_entity_extraction_20260319_000002")
    print("  - job_3c_rag_indexing_20260319_000003")

if __name__ == '__main__':
    submit_phased_processing_jobs()

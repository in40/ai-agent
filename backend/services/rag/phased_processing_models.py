"""
Phased Document Processing - Data Models

Data models for the phased document processing pipeline.
Supports: upload → extract → chunk → vector → graph
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class PhaseStatus(str, Enum):
    """Status for individual phases"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class DocumentStatus(str, Enum):
    """Overall document processing status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class ProcessingPhase(str, Enum):
    """Available processing phases"""
    UPLOAD = "upload"
    EXTRACT = "extract"
    CHUNK = "chunk"
    VECTOR = "vector"
    GRAPH = "graph"


@dataclass
class DocumentProcessing:
    """Represents a document being processed through the pipeline"""
    
    doc_id: str
    job_id: str
    user_id: str
    original_filename: str
    
    # Optional fields
    display_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    source_url: Optional[str] = None
    source_website: Optional[str] = None
    
    # Phase statuses
    phase_upload: PhaseStatus = PhaseStatus.PENDING
    phase_extract: PhaseStatus = PhaseStatus.PENDING
    phase_chunk: PhaseStatus = PhaseStatus.PENDING
    phase_vector: PhaseStatus = PhaseStatus.PENDING
    phase_graph: PhaseStatus = PhaseStatus.PENDING
    
    # Current state
    current_phase: str = ProcessingPhase.UPLOAD.value
    overall_status: DocumentStatus = DocumentStatus.PENDING
    
    # Extraction metadata
    extraction_method: Optional[str] = None
    extraction_attempts: int = 0
    page_count: Optional[int] = None
    extracted_char_count: Optional[int] = None
    encoding_issues_fixed: int = 0
    
    # Chunking metadata
    chunk_count: int = 0
    chunking_strategy: Optional[str] = None
    chunking_model: Optional[str] = None
    
    # Vector metadata
    vector_collection: Optional[str] = None
    vector_chunk_count: int = 0
    embedding_model: Optional[str] = None
    
    # Graph metadata
    entity_count: int = 0
    relationship_count: int = 0
    graph_model: Optional[str] = None
    
    # Error tracking
    last_error: Optional[str] = None
    last_error_phase: Optional[str] = None
    retry_count: int = 0
    
    # Timestamps
    uploaded_at: Optional[datetime] = None
    extracted_at: Optional[datetime] = None
    chunked_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    graph_built_at: Optional[datetime] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'doc_id': self.doc_id,
            'job_id': self.job_id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'display_name': self.display_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'source_url': self.source_url,
            'source_website': self.source_website,
            'phase_upload': self.phase_upload.value,
            'phase_extract': self.phase_extract.value,
            'phase_chunk': self.phase_chunk.value,
            'phase_vector': self.phase_vector.value,
            'phase_graph': self.phase_graph.value,
            'current_phase': self.current_phase,
            'overall_status': self.overall_status.value,
            'extraction_method': self.extraction_method,
            'extraction_attempts': self.extraction_attempts,
            'page_count': self.page_count,
            'extracted_char_count': self.extracted_char_count,
            'chunk_count': self.chunk_count,
            'chunking_strategy': self.chunking_strategy,
            'vector_collection': self.vector_collection,
            'entity_count': self.entity_count,
            'last_error': self.last_error,
            'last_error_phase': self.last_error_phase,
            'retry_count': self.retry_count,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'chunked_at': self.chunked_at.isoformat() if self.chunked_at else None,
            'indexed_at': self.indexed_at.isoformat() if self.indexed_at else None,
            'graph_built_at': self.graph_built_at.isoformat() if self.graph_built_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentProcessing':
        """Create from dictionary"""
        return cls(
            doc_id=data.get('doc_id'),
            job_id=data.get('job_id'),
            user_id=data.get('user_id'),
            original_filename=data.get('original_filename'),
            display_name=data.get('display_name'),
            file_path=data.get('file_path'),
            file_size=data.get('file_size'),
            content_type=data.get('content_type'),
            source_url=data.get('source_url'),
            source_website=data.get('source_website'),
            phase_upload=PhaseStatus(data.get('phase_upload', 'PENDING')),
            phase_extract=PhaseStatus(data.get('phase_extract', 'PENDING')),
            phase_chunk=PhaseStatus(data.get('phase_chunk', 'PENDING')),
            phase_vector=PhaseStatus(data.get('phase_vector', 'PENDING')),
            phase_graph=PhaseStatus(data.get('phase_graph', 'PENDING')),
            current_phase=data.get('current_phase', 'upload'),
            overall_status=DocumentStatus(data.get('overall_status', 'PENDING')),
            extraction_method=data.get('extraction_method'),
            extraction_attempts=data.get('extraction_attempts', 0),
            page_count=data.get('page_count'),
            extracted_char_count=data.get('extracted_char_count'),
            chunk_count=data.get('chunk_count', 0),
            chunking_strategy=data.get('chunking_strategy'),
            vector_collection=data.get('vector_collection'),
            entity_count=data.get('entity_count', 0),
            last_error=data.get('last_error'),
            last_error_phase=data.get('last_error_phase'),
            retry_count=data.get('retry_count', 0),
        )


@dataclass
class Chunk:
    """Represents a text chunk from document processing"""
    
    doc_id: str
    chunk_id: str
    chunk_index: int
    content: str
    
    # Optional fields
    content_length: Optional[int] = None
    section: Optional[str] = None
    title: Optional[str] = None
    chunk_type: str = 'text'
    token_count: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    contains_formula: bool = False
    contains_table: bool = False
    entity_hints: List[str] = field(default_factory=list)
    
    # Versioning
    version: str = 'v1'
    version_label: Optional[str] = None
    is_active: bool = True
    
    # Vector DB reference
    vector_id: Optional[str] = None
    vector_collection: Optional[str] = None
    
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'doc_id': self.doc_id,
            'chunk_id': self.chunk_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'content_length': self.content_length,
            'section': self.section,
            'title': self.title,
            'chunk_type': self.chunk_type,
            'token_count': self.token_count,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'contains_formula': self.contains_formula,
            'contains_table': self.contains_table,
            'entity_hints': self.entity_hints,
            'version': self.version,
            'version_label': self.version_label,
            'is_active': self.is_active,
            'vector_id': self.vector_id,
            'vector_collection': self.vector_collection,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class Entity:
    """Represents an extracted entity"""
    
    doc_id: str
    entity_name: str
    entity_type: str
    
    # Optional fields
    chunk_id: Optional[str] = None
    relevance_score: Optional[float] = None
    context_snippet: Optional[str] = None
    mentions_count: int = 1
    
    # Neo4j reference
    neo4j_node_id: Optional[str] = None
    neo4j_labels: List[str] = field(default_factory=list)
    
    # Versioning
    version: str = 'v1'
    is_active: bool = True
    
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'doc_id': self.doc_id,
            'entity_name': self.entity_name,
            'entity_type': self.entity_type,
            'chunk_id': self.chunk_id,
            'relevance_score': self.relevance_score,
            'context_snippet': self.context_snippet,
            'mentions_count': self.mentions_count,
            'neo4j_node_id': self.neo4j_node_id,
            'neo4j_labels': self.neo4j_labels,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class PhaseExecutionLog:
    """Log entry for phase execution"""
    
    execution_id: str
    job_id: str
    phase: str
    action: str
    status: str
    
    # Optional fields
    doc_id: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    items_processed: Optional[int] = None
    config_snapshot: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'execution_id': self.execution_id,
            'job_id': self.job_id,
            'doc_id': self.doc_id,
            'phase': self.phase,
            'action': self.action,
            'status': self.status,
            'error_message': self.error_message,
            'processing_time_ms': self.processing_time_ms,
            'items_processed': self.items_processed,
            'config_snapshot': self.config_snapshot,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class JobPhaseProgress:
    """Progress summary for a job's phases"""
    
    job_id: str
    documents_total: int
    
    # Upload phase
    upload_completed: int = 0
    upload_failed: int = 0
    upload_pending: int = 0
    
    # Extract phase
    extract_completed: int = 0
    extract_failed: int = 0
    extract_pending: int = 0
    
    # Chunk phase
    chunk_completed: int = 0
    chunk_failed: int = 0
    chunk_pending: int = 0
    
    # Vector phase
    vector_completed: int = 0
    vector_failed: int = 0
    vector_pending: int = 0
    
    # Graph phase
    graph_completed: int = 0
    graph_failed: int = 0
    graph_pending: int = 0
    
    # Overall
    fully_completed: int = 0
    fully_failed: int = 0
    in_progress: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'documents_total': self.documents_total,
            'phases': {
                'upload': {
                    'completed': self.upload_completed,
                    'failed': self.upload_failed,
                    'pending': self.upload_pending,
                },
                'extract': {
                    'completed': self.extract_completed,
                    'failed': self.extract_failed,
                    'pending': self.extract_pending,
                },
                'chunk': {
                    'completed': self.chunk_completed,
                    'failed': self.chunk_failed,
                    'pending': self.chunk_pending,
                },
                'vector': {
                    'completed': self.vector_completed,
                    'failed': self.vector_failed,
                    'pending': self.vector_pending,
                },
                'graph': {
                    'completed': self.graph_completed,
                    'failed': self.graph_failed,
                    'pending': self.graph_pending,
                },
            },
            'overall': {
                'completed': self.fully_completed,
                'failed': self.fully_failed,
                'in_progress': self.in_progress,
            }
        }

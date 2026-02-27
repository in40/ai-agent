"""File System Storage Backend for Documents"""
import os
import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import config


class FileStorage:
    """File system-based document storage"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or config.INGESTED_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_job_dir(self, job_id: str) -> Path:
        """Get job directory path"""
        return self.base_dir / job_id
    
    def _get_documents_dir(self, job_id: str) -> Path:
        """Get documents directory for a job"""
        return self._get_job_dir(job_id) / "documents"
    
    def _get_document_path(self, job_id: str, doc_id: str, format: str = "txt") -> Path:
        """Get document file path"""
        docs_dir = self._get_documents_dir(job_id)
        return docs_dir / f"{doc_id}.{format}"
    
    def _get_metadata_path(self, job_id: str, doc_id: str) -> Path:
        """Get metadata file path"""
        docs_dir = self._get_documents_dir(job_id)
        return docs_dir / f"{doc_id}.metadata.json"

    def get_metadata(self, job_id: str, doc_id: str) -> Dict[str, Any]:
        """Get metadata for a document"""
        try:
            metadata_path = self._get_metadata_path(job_id, doc_id)
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        # Return empty dict instead of None to prevent issues downstream
        return {}

    def save_document(
        self,
        job_id: str,
        doc_id: str,
        content: str,
        format: str = "txt",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a document to storage.

        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            content: Document content (string for text, base64-encoded for binary)
            format: File format (txt, pdf, md, json)
            metadata: Optional metadata dictionary

        Returns:
            Path to saved document
        """
        import base64
        
        # Create directories
        docs_dir = self._get_documents_dir(job_id)
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Save content - use binary mode for PDF and other binary formats
        doc_path = self._get_document_path(job_id, doc_id, format)
        
        if format.lower() in ['pdf', 'png', 'jpg', 'jpeg', 'gif']:
            # Binary format - decode from base64 and write as binary
            try:
                # Content should be base64-encoded for binary formats
                binary_content = base64.b64decode(content)
                with open(doc_path, 'wb') as f:
                    f.write(binary_content)
            except Exception as e:
                # If base64 decode fails, try latin-1 encoding (legacy support)
                binary_content = content.encode('latin-1')
                with open(doc_path, 'wb') as f:
                    f.write(binary_content)
        else:
            # Text format - write as text with UTF-8 encoding
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Save metadata if provided
        if metadata:
            self.save_metadata(job_id, doc_id, metadata)

        return str(doc_path)
    
    def get_document(
        self,
        job_id: str,
        doc_id: str,
        format: str = "txt"
    ) -> Optional[Dict[str, Any]]:
        """
        Get document content.

        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            format: File format

        Returns:
            Dict with content and metadata, or None if not found
        """
        doc_path = self._get_document_path(job_id, doc_id, format)

        if not doc_path.exists():
            return None

        # Read binary formats (pdf, etc.) in binary mode
        if format.lower() in ['pdf', 'png', 'jpg', 'jpeg', 'gif']:
            with open(doc_path, 'rb') as f:
                content = f.read()
            # Return binary content as base64 for safe JSON transport
            import base64
            content_b64 = base64.b64encode(content).decode('ascii')
            return {
                'content': content_b64,
                'content_length': len(content),
                'encoding': 'base64'
            }
        else:
            # Read text formats in text mode
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                'content': content,
                'content_length': len(content),
                'encoding': 'utf-8'
            }
    
    def delete_document(self, job_id: str, doc_id: str) -> bool:
        """
        Delete a document and its metadata.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        deleted = False
        
        # Delete all formats
        for format in ["txt", "pdf", "md", "json"]:
            doc_path = self._get_document_path(job_id, doc_id, format)
            if doc_path.exists():
                doc_path.unlink()
                deleted = True
        
        # Delete metadata
        metadata_path = self._get_metadata_path(job_id, doc_id)
        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True
        
        return deleted
    
    def list_documents(self, job_id: str) -> List[Dict[str, Any]]:
        """
        List all documents for a job.

        Args:
            job_id: Ingestion job ID

        Returns:
            List of document info dictionaries with original filenames from metadata
        """
        docs_dir = self._get_documents_dir(job_id)

        if not docs_dir.exists():
            return []

        documents = []
        seen_ids = set()

        for file_path in docs_dir.iterdir():
            if file_path.suffix == '.json' and 'metadata' in file_path.stem:
                continue

            doc_id = file_path.stem
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)

            # Get metadata if available
            metadata = self.get_metadata(job_id, doc_id) or {}

            # Get file size
            try:
                size = file_path.stat().st_size
            except:
                size = 0

            # Use original filename from metadata if available, otherwise use file path name
            original_filename = metadata.get('original_filename', file_path.name)
            
            # Get source website from metadata if available
            source_website = metadata.get('source_website', '')
            original_url = metadata.get('original_url', '')

            documents.append({
                "doc_id": doc_id,
                "filename": original_filename,  # Use original filename from metadata
                "original_url": original_url,  # Add source URL
                "source_website": source_website,  # Add source website
                "format": file_path.suffix[1:],  # Remove dot
                "size": size,
                "metadata": metadata
            })

        return sorted(documents, key=lambda x: x["doc_id"])
    
    def delete_job_documents(self, job_id: str) -> int:
        """
        Delete all documents for a job.
        
        Args:
            job_id: Ingestion job ID
            
        Returns:
            Number of documents deleted
        """
        job_dir = self._get_job_dir(job_id)
        
        if not job_dir.exists():
            return 0
        
        # Count documents before deletion
        count = len(list(self._get_documents_dir(job_id).glob("*"))) // 2  # Approximate
        
        # Delete entire job directory
        shutil.rmtree(job_dir)
        
        return count
    
    def job_exists(self, job_id: str) -> bool:
        """Check if a job exists"""
        return self._get_job_dir(job_id).exists()
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all ingestion jobs.
        
        Returns:
            List of job info dictionaries
        """
        jobs = []
        
        for job_dir in self.base_dir.iterdir():
            if job_dir.is_dir():
                job_id = job_dir.name
                docs_dir = self._get_documents_dir(job_id)
                
                # Count documents
                doc_count = 0
                if docs_dir and docs_dir.exists():
                    # Count all non-metadata JSON files in documents directory
                    doc_count = sum(1 for f in docs_dir.iterdir() if f.is_file() and not f.name.endswith('.json'))
                
                # Get index if available
                index_path = job_dir / "index.json"
                created_at = None
                if index_path.exists():
                    try:
                        with open(index_path, 'r') as f:
                            index = json.load(f)
                            created_at = index.get("created_at")
                    except:
                        pass
                
                jobs.append({
                    "job_id": job_id,
                    "document_count": doc_count,
                    "created_at": created_at,
                    "path": str(job_dir)
                })
        
        return sorted(jobs, key=lambda x: x.get("created_at") or "", reverse=True)

"""Metadata Management for Documents"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class MetadataManager:
    """Manages document metadata"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def _get_metadata_path(self, job_id: str, doc_id: str) -> Path:
        """Get metadata file path"""
        docs_dir = self.base_dir / job_id / "documents"
        return docs_dir / f"{doc_id}.metadata.json"
    
    def save_metadata(
        self, 
        job_id: str, 
        doc_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Save metadata for a document.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            metadata: Metadata dictionary
            
        Returns:
            True if saved successfully
        """
        try:
            metadata_path = self._get_metadata_path(job_id, doc_id)
            
            # Ensure directory exists
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp if not present
            if "saved_at" not in metadata:
                metadata["saved_at"] = datetime.utcnow().isoformat()
            
            # Save metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def get_metadata(
        self, 
        job_id: str, 
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a document.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            
        Returns:
            Metadata dictionary or None if not found
        """
        metadata_path = self._get_metadata_path(job_id, doc_id)
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading metadata: {e}")
            return None
    
    def update_metadata(
        self, 
        job_id: str, 
        doc_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update metadata for a document.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            updates: Dictionary of updates to apply
            
        Returns:
            Updated metadata or None if not found
        """
        metadata = self.get_metadata(job_id, doc_id)
        
        if metadata is None:
            return None
        
        # Apply updates
        metadata.update(updates)
        metadata["updated_at"] = datetime.utcnow().isoformat()
        
        # Save updated metadata
        self.save_metadata(job_id, doc_id, metadata)
        
        return metadata
    
    def delete_metadata(self, job_id: str, doc_id: str) -> bool:
        """
        Delete metadata for a document.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            
        Returns:
            True if deleted successfully
        """
        metadata_path = self._get_metadata_path(job_id, doc_id)
        
        if metadata_path.exists():
            metadata_path.unlink()
            return True
        
        return False

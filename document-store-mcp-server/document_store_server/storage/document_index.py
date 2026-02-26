"""Document Indexing and Search"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class DocumentIndex:
    """Manages document indexing and search"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def _get_index_path(self, job_id: str) -> Path:
        """Get index file path for a job"""
        return self.base_dir / job_id / "index.json"
    
    def create_job_index(
        self, 
        job_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create an index for a new job.
        
        Args:
            job_id: Ingestion job ID
            metadata: Optional job metadata
            
        Returns:
            True if created successfully
        """
        try:
            index_path = self._get_index_path(job_id)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            index = {
                "job_id": job_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "document_count": 0,
                "metadata": metadata or {},
                "documents": []
            }
            
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error creating job index: {e}")
            return False
    
    def add_document_to_index(
        self, 
        job_id: str, 
        doc_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a document to the job index.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            metadata: Optional document metadata
            
        Returns:
            True if added successfully
        """
        try:
            index_path = self._get_index_path(job_id)
            
            if not index_path.exists():
                self.create_job_index(job_id)
            
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            # Check if document already in index
            doc_ids = [d["doc_id"] for d in index.get("documents", [])]
            if doc_id not in doc_ids:
                index["documents"].append({
                    "doc_id": doc_id,
                    "added_at": datetime.utcnow().isoformat(),
                    "metadata": metadata or {}
                })
                index["document_count"] = len(index["documents"])
                index["updated_at"] = datetime.utcnow().isoformat()
                
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump(index, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error adding document to index: {e}")
            return False
    
    def get_job_index(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the index for a job.
        
        Args:
            job_id: Ingestion job ID
            
        Returns:
            Index dictionary or None if not found
        """
        index_path = self._get_index_path(job_id)
        
        if not index_path.exists():
            return None
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading job index: {e}")
            return None
    
    def search_index(
        self, 
        job_id: str, 
        query: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search within a job index (simple text search).
        
        Args:
            job_id: Ingestion job ID
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching document info
        """
        index = self.get_job_index(job_id)
        
        if not index:
            return []
        
        query_lower = query.lower()
        results = []
        
        # Search in document metadata
        for doc in index.get("documents", []):
            metadata = doc.get("metadata", {})
            
            # Check if query matches any metadata field
            match = False
            for key, value in metadata.items():
                if isinstance(value, str) and query_lower in value.lower():
                    match = True
                    break
            
            # Also check doc_id
            if query_lower in doc["doc_id"].lower():
                match = True
            
            if match:
                results.append({
                    "doc_id": doc["doc_id"],
                    "metadata": metadata,
                    "added_at": doc.get("added_at")
                })
            
            if len(results) >= limit:
                break
        
        return results
    
    def remove_document_from_index(self, job_id: str, doc_id: str) -> bool:
        """
        Remove a document from the index.
        
        Args:
            job_id: Ingestion job ID
            doc_id: Document ID
            
        Returns:
            True if removed successfully
        """
        try:
            index_path = self._get_index_path(job_id)
            
            if not index_path.exists():
                return False
            
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            # Remove document
            index["documents"] = [
                d for d in index.get("documents", []) 
                if d["doc_id"] != doc_id
            ]
            index["document_count"] = len(index["documents"])
            index["updated_at"] = datetime.utcnow().isoformat()
            
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error removing document from index: {e}")
            return False
    
    def delete_job_index(self, job_id: str) -> bool:
        """
        Delete the index for a job.
        
        Args:
            job_id: Ingestion job ID
            
        Returns:
            True if deleted successfully
        """
        index_path = self._get_index_path(job_id)
        
        if index_path.exists():
            index_path.unlink()
            return True
        
        return False

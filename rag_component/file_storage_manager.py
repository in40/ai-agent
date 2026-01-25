"""
File storage manager for the RAG component.
Handles storing and retrieving original files with preserved filenames.
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from config.settings import RAG_FILE_STORAGE_DIR


class FileStorageManager:
    """Class responsible for managing file storage with preserved original filenames."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the file storage manager.
        
        Args:
            storage_dir: Directory to store files. If None, uses the configured default.
        """
        self.storage_dir = storage_dir or RAG_FILE_STORAGE_DIR or './data/rag_files'
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def store_file(self, file_path: str, original_filename: str) -> str:
        """
        Store a file with its original filename preserved.
        
        Args:
            file_path: Path to the temporary file to store
            original_filename: Original filename to preserve
            
        Returns:
            Path to the stored file
        """
        # Create a unique subdirectory to avoid filename collisions
        subdir = str(uuid.uuid4())
        file_storage_dir = os.path.join(self.storage_dir, subdir)
        os.makedirs(file_storage_dir, exist_ok=True)
        
        # Sanitize the original filename to prevent path traversal
        sanitized_filename = self._sanitize_filename(original_filename)
        stored_file_path = os.path.join(file_storage_dir, sanitized_filename)
        
        # Copy the file to the storage location
        shutil.copy2(file_path, stored_file_path)
        
        return stored_file_path
    
    def store_files(self, file_paths: List[str], original_filenames: List[str]) -> List[str]:
        """
        Store multiple files with their original filenames preserved.
        
        Args:
            file_paths: List of paths to temporary files to store
            original_filenames: List of original filenames to preserve
            
        Returns:
            List of paths to the stored files
        """
        if len(file_paths) != len(original_filenames):
            raise ValueError("Number of file paths must match number of original filenames")
        
        stored_paths = []
        for file_path, original_filename in zip(file_paths, original_filenames):
            stored_path = self.store_file(file_path, original_filename)
            stored_paths.append(stored_path)
        
        return stored_paths
    
    def get_file_path(self, original_filename: str, file_id: str) -> Optional[str]:
        """
        Get the stored file path for a given original filename and file ID.
        
        Args:
            original_filename: The original filename
            file_id: The unique ID assigned to the file during storage
            
        Returns:
            Path to the stored file, or None if not found
        """
        # The file would be stored in a subdirectory named after the UUID
        file_storage_dir = os.path.join(self.storage_dir, file_id)
        sanitized_filename = self._sanitize_filename(original_filename)
        stored_file_path = os.path.join(file_storage_dir, sanitized_filename)
        
        if os.path.exists(stored_file_path):
            return stored_file_path
        else:
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal and other security issues.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        # Get the basename to prevent directory traversal
        filename = os.path.basename(filename)
        
        # Remove any potentially dangerous characters/sequences
        # Allow only alphanumeric, dots, dashes, underscores, and spaces
        import re
        filename = re.sub(r'[^\w\-_. ]', '_', filename)
        
        # Limit filename length to prevent potential issues
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def cleanup_temp_files(self, temp_paths: List[str]):
        """
        Clean up temporary files after they've been stored permanently.

        Args:
            temp_paths: List of temporary file paths to remove
        """
        for temp_path in temp_paths:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"Error removing temporary file {temp_path}: {str(e)}")

    def get_file_download_url(self, file_id: str, original_filename: str) -> str:
        """
        Generate a download URL for a stored file.

        Args:
            file_id: The unique ID of the file
            original_filename: The original filename

        Returns:
            Download URL for the file
        """
        from flask import request
        # This would need to be called within a Flask request context to get the base URL
        # In practice, you'd construct this differently based on your deployment setup
        return f"/download/{file_id}/{original_filename}"
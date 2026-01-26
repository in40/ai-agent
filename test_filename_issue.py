#!/usr/bin/env python3
"""
Test to verify the exact filename issue
"""
import os
from urllib.parse import quote

def test_filename_issue():
    """Test the exact filename issue"""
    print("=== Testing filename issue ===")
    
    # The actual file in the system
    actual_filename = "ГОСТ Р ИСО МЭК 27001-2021.pdf"  # With spaces
    print(f"Actual filename in storage: {actual_filename}")
    
    # What the URL would request after sanitization
    # Using the secure_filename function from the RAG service
    import re
    
    def secure_filename(filename: str) -> str:
        """
        Secure a filename by removing potentially dangerous characters and sequences.
        Preserves Unicode characters like Cyrillic letters.
        """
        if filename is None:
            return ''

        # Normalize the path to remove any Windows-style separators
        filename = filename.replace('\\', '/')

        # Get the basename to prevent directory traversal
        filename = os.path.basename(filename)

        # Remove leading dots and spaces
        filename = filename.lstrip('. ')

        # Replace any sequence of invalid characters with a single underscore
        # Allow Unicode word characters (letters, digits, underscores), dots, dashes, and spaces
        filename = re.sub(r'[^\w\-.]', '_', filename, flags=re.UNICODE)

        # Handle cases where the filename might be empty after sanitization
        if not filename:
            filename = "unnamed_file"

        # Prevent hidden files by ensuring the name doesn't start with a dot
        if filename.startswith('.'):
            filename = f"unnamed{filename}"

        return filename
    
    sanitized_filename = secure_filename(actual_filename)
    print(f"Sanitized filename (what URL would request): {sanitized_filename}")
    
    # Check if both files exist
    file_dir = "/root/qwen_test/ai_agent/data/rag_uploaded_files/d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d/"
    
    actual_file_path = os.path.join(file_dir, actual_filename)
    sanitized_file_path = os.path.join(file_dir, sanitized_filename)
    
    print(f"Actual file exists: {os.path.exists(actual_file_path)}")
    print(f"Sanitized file exists: {os.path.exists(sanitized_file_path)}")
    
    # List all files in the directory
    print(f"All files in directory:")
    for f in os.listdir(file_dir):
        print(f"  - {repr(f)}")
    
    # Test URL encoding
    encoded_actual = quote(actual_filename)
    encoded_sanitized = quote(sanitized_filename)
    print(f"URL encoded actual: {encoded_actual}")
    print(f"URL encoded sanitized: {encoded_sanitized}")

if __name__ == "__main__":
    test_filename_issue()
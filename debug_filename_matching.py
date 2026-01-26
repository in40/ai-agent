#!/usr/bin/env python3
"""
Debug script to check what files are being looked for
"""
import os
from urllib.parse import quote

def debug_filename_matching():
    """Debug the filename matching logic"""
    print("=== Debugging filename matching ===")
    
    # Define the file ID and filenames
    file_id = "d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    original_filename = "ГОСТ Р ИСО МЭК 27001-2021.pdf"  # With spaces
    sanitized_filename = "ГОСТ_Р_ИСО_МЭК_27001-2021.pdf"  # With underscores
    
    print(f"File ID: {file_id}")
    print(f"Original filename: {original_filename}")
    print(f"Sanitized filename: {sanitized_filename}")
    
    # Define the storage directory
    file_storage_dir = f"/root/qwen_test/ai_agent/data/rag_uploaded_files/{file_id}"
    print(f"Storage directory: {file_storage_dir}")
    
    # List all files in the directory
    print(f"Files in directory:")
    for f in os.listdir(file_storage_dir):
        print(f"  - {repr(f)}")
    
    # Check if the files exist
    original_path = os.path.join(file_storage_dir, original_filename)
    sanitized_path = os.path.join(file_storage_dir, sanitized_filename)
    
    print(f"\nChecking file paths:")
    print(f"Original path exists: {os.path.exists(original_path)} - {original_path}")
    print(f"Sanitized path exists: {os.path.exists(sanitized_path)} - {sanitized_path}")
    
    # Test the secure_filename function
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
    
    # Apply the function to the original filename
    result = secure_filename(original_filename)
    print(f"\nsecure_filename('{original_filename}') = '{result}'")
    
    # Test the logic from the updated download endpoint
    possible_filenames = [
        original_filename,  # Original filename as received
        secure_filename(original_filename)  # Sanitized version
    ]
    
    print(f"\nPossible filenames to check: {possible_filenames}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_filenames = []
    for fname in possible_filenames:
        if fname not in seen:
            seen.add(fname)
            unique_filenames.append(fname)

    print(f"Unique filenames to check: {unique_filenames}")
    
    # Check each filename
    for fname in unique_filenames:
        test_path = os.path.join(file_storage_dir, fname)
        exists = os.path.exists(test_path)
        print(f"  {fname} -> exists: {exists}, path: {test_path}")

if __name__ == "__main__":
    debug_filename_matching()
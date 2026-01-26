#!/usr/bin/env python3
"""
Test the specific fix logic for filename matching
"""
import os
import sys
import importlib.util

def test_filename_matching_logic():
    """Test the filename matching logic in isolation"""
    print("=== Testing filename matching logic ===")
    
    # Load the RAG app module to access the secure_filename function
    rag_app_path = "/root/qwen_test/ai_agent/backend/services/rag/app.py"
    
    # Load the module
    spec = importlib.util.spec_from_file_location("rag_app", rag_app_path)
    rag_app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rag_app_module)
    
    # Get the secure_filename function
    secure_filename = getattr(rag_app_module, 'secure_filename')
    
    # Test the specific scenario
    filename_from_url = "ГОСТ_Р_ИСО_МЭК_27001-2021.pdf"  # Sanitized version from URL
    file_storage_dir = "/root/qwen_test/ai_agent/data/rag_uploaded_files/d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    
    print(f"Filename from URL (sanitized): {filename_from_url}")
    
    # Apply the same logic as in the updated download endpoint
    possible_filenames = [
        filename_from_url,  # Original filename as received (could be sanitized or not)
    ]
    
    # Also try the desanitized version (underscores to spaces) for files that were stored with original names
    if '_' in filename_from_url:
        # Convert underscores back to spaces to check for original filename
        desanitized_filename = filename_from_url.replace('_', ' ')
        if desanitized_filename != filename_from_url:
            possible_filenames.append(desanitized_filename)
    
    # Also try the sanitized version in case file was stored with sanitized name
    sanitized_filename = secure_filename(filename_from_url)
    if sanitized_filename != filename_from_url:
        possible_filenames.append(sanitized_filename)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_filenames = []
    for fname in possible_filenames:
        if fname not in seen:
            seen.add(fname)
            unique_filenames.append(fname)
    
    print(f"Possible filenames to check: {unique_filenames}")
    
    # Check each filename
    found_file = None
    for fname in unique_filenames:
        test_path = os.path.join(file_storage_dir, fname)
        exists = os.path.exists(test_path)
        print(f"  {fname} -> exists: {exists}")
        if exists:
            found_file = test_path
            print(f"    ✓ FOUND: {test_path}")
            break
    
    if found_file:
        print("✓ SUCCESS: Logic correctly identifies the existing file!")
        return True
    else:
        print("✗ FAILED: Logic does not find any existing file!")
        return False

def test_manual_file_access():
    """Test accessing the file directly using the logic"""
    print("\n=== Testing manual file access ===")
    
    # The actual file name in the directory
    actual_file_name = "ГОСТ Р ИСО МЭК 27001-2021.pdf"
    file_path = f"/root/qwen_test/ai_agent/data/rag_uploaded_files/d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d/{actual_file_name}"
    
    print(f"Checking if file exists: {file_path}")
    exists = os.path.exists(file_path)
    print(f"File exists: {exists}")
    
    if exists:
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")
        print("✓ File exists and is accessible!")
        return True
    else:
        print("✗ File does not exist!")
        return False

if __name__ == "__main__":
    success1 = test_manual_file_access()
    success2 = test_filename_matching_logic()
    
    if success1 and success2:
        print("\n✓ All tests PASSED - the logic should work!")
    else:
        print("\n✗ Some tests FAILED")
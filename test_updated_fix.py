#!/usr/bin/env python3
"""
Test the updated download functionality fix
"""
import os
import requests
from urllib.parse import quote

def test_updated_fix():
    """Test the updated download functionality fix"""
    print("=== Testing updated download functionality fix ===")
    
    # Get a valid token
    auth_response = requests.post("http://localhost:5001/login", json={
        'username': 'debug_user',
        'password': 'password123'
    })
    
    if auth_response.status_code != 200:
        print("Could not get valid token")
        return
    
    token = auth_response.json()['token']
    print(f"Got valid token: {token[:20]}...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Test with the sanitized filename (what would be in the URL)
    file_id = "d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    sanitized_filename = "ГОСТ_Р_ИСО_МЭК_27001-2021.pdf"  # This is what's in the URL
    encoded_filename = quote(sanitized_filename)
    
    print(f"Testing download for file ID: {file_id}")
    print(f"Testing with sanitized filename (from URL): {sanitized_filename}")
    
    # Test direct RAG service
    url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    print(f"Direct RAG URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Direct RAG response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ SUCCESS: Direct RAG download worked!")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"  Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        elif "Token is missing!" in response.text:
            print("✗ FAILED: Token is missing!")
        else:
            print(f"✗ Response: {response.text}")
    except Exception as e:
        print(f"✗ Error in direct RAG download: {e}")
    
    # Test through gateway
    print(f"\nTesting through gateway...")
    gw_url = f"http://localhost:5000/download/{file_id}/{encoded_filename}"
    print(f"Gateway URL: {gw_url}")
    
    try:
        response = requests.get(gw_url, headers=headers, timeout=30)
        print(f"Gateway response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ SUCCESS: Gateway download worked!")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"  Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        elif "Token is missing!" in response.text:
            print("✗ FAILED: Token is missing at gateway!")
        else:
            print(f"✗ Response: {response.text}")
    except Exception as e:
        print(f"✗ Error in gateway download: {e}")

def test_manual_logic():
    """Test the logic manually to make sure it works"""
    print(f"\n=== Testing the manual logic ===")
    
    # Define the filename from the URL (sanitized)
    filename_from_url = "ГОСТ_Р_ИСО_МЭК_27001-2021.pdf"
    file_storage_dir = "/root/qwen_test/ai_agent/data/rag_uploaded_files/d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    
    print(f"Filename from URL: {filename_from_url}")
    
    # Apply the same logic as in the updated code
    possible_filenames = [
        filename_from_url,  # Original filename as received (could be sanitized or not)
    ]
    
    # Also try the desanitized version (underscores to spaces) for files that were stored with original names
    # This handles the case where URL has sanitized name but file was stored with original name
    if '_' in filename_from_url:
        # Convert underscores back to spaces to check for original filename
        desanitized_filename = filename_from_url.replace('_', ' ')
        if desanitized_filename != filename_from_url:
            possible_filenames.append(desanitized_filename)
    
    # Also try the sanitized version in case file was stored with sanitized name
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
    for fname in unique_filenames:
        test_path = os.path.join(file_storage_dir, fname)
        exists = os.path.exists(test_path)
        print(f"  {fname} -> exists: {exists}")
        if exists:
            print(f"    ✓ FOUND: {test_path}")
            break
    else:
        print("  ✗ None of the possible filenames exist!")

if __name__ == "__main__":
    test_updated_fix()
    test_manual_logic()
    print("\n=== Test Complete ===")
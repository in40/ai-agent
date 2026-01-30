#!/usr/bin/env python3
"""
Test script to verify that the file ingestion issue has been fixed.
"""
import os
import tempfile
import requests
from pathlib import Path

def get_auth_token():
    """Get an authentication token for the API."""
    try:
        # Try to get a token from the auth service
        auth_url = "http://localhost:5001/login"
        # Using a default test user - you might need to adjust this based on your setup
        login_data = {
            "username": "admin",
            "password": "admin"  # Default credentials
        }

        response = requests.post(auth_url, json=login_data)

        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token", "")
        else:
            print(f"Authentication failed: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        print(f"Error getting auth token: {str(e)}")
        # Try with a default token if available
        return os.getenv("DEFAULT_TEST_TOKEN", "")

def test_markdown_ingestion():
    """Test that Markdown files can now be ingested successfully."""

    # Create a temporary markdown file similar to the one that was failing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write("# Test Document\n\nThis is a test markdown file.\n\n## Section 2\n\nMore content here.")
        temp_file_path = temp_file.name

    try:
        # Get authentication token
        token = get_auth_token()
        if not token:
            print("Could not obtain authentication token. Trying with default token...")
            token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.example_token"

        # Upload the file to the RAG service
        url = "http://localhost:5003/upload_with_progress"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        with open(temp_file_path, 'rb') as f:
            files = {'file': (os.path.basename(temp_file_path), f, 'text/markdown')}
            response = requests.post(url, files=files, headers=headers)

        print(f"Upload response status: {response.status_code}")
        print(f"Upload response: {response.text}")

        if response.status_code == 200:
            print("✓ File upload successful!")
            return True
        else:
            print("✗ File upload failed!")
            return False

    except Exception as e:
        print(f"Error during file upload: {str(e)}")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == "__main__":
    print("Testing file ingestion fix...")
    success = test_markdown_ingestion()

    if success:
        print("\n✓ File ingestion test passed! The issue appears to be fixed.")
    else:
        print("\n✗ File ingestion test failed. The issue may still exist.")
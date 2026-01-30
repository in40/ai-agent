#!/usr/bin/env python3
"""
Solution script to fix the RAG similarity threshold issue
"""
import os
import sys
from pathlib import Path

def fix_similarity_threshold():
    """Fix the RAG similarity threshold issue."""
    print("=== FIXING RAG SIMILARITY THRESHOLD ISSUE ===")
    
    env_file_path = Path("/root/qwen/ai_agent/.env")
    
    if not env_file_path.exists():
        print(f"ERROR: .env file not found at {env_file_path}")
        return False
    
    # Read the current .env file
    with open(env_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Current .env file contains the line:")
    for line in content.split('\n'):
        if 'RAG_SIMILARITY_THRESHOLD' in line and '=' in line:
            print(f"  {line}")
    
    # Replace the threshold value
    import re
    updated_content = re.sub(
        r'(RAG_SIMILARITY_THRESHOLD=)0\.7',
        r'\g<1>0.6',
        content
    )

    # If the substitution didn't happen (meaning the exact pattern wasn't found),
    # try a more general approach
    if updated_content == content:
        # Look for any RAG_SIMILARITY_THRESHOLD setting and update it
        updated_content = re.sub(
            r'(RAG_SIMILARITY_THRESHOLD=)\d+(\.\d+)?',
            r'\g<1>0.6',
            content
        )
    
    # If still unchanged, append the setting
    if updated_content == content:
        updated_content += "\n# Updated to allow more flexible document matching\nRAG_SIMILARITY_THRESHOLD=0.6\n"
    
    # Write the updated content back to the file
    with open(env_file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"\nUpdated .env file with lower similarity threshold.")
    print(f"RAG_SIMILARITY_THRESHOLD changed to 0.6")
    print(f"This will allow documents with similarity scores as low as 0.6 to be returned.")
    
    print(f"\nTo apply this change:")
    print(f"1. Restart the RAG service: python -m backend.services.rag.app")
    print(f"2. Or restart all services if using the full system")
    print(f"3. The next document lookup should return results for the Russian query")
    
    # Show the updated line
    for line in updated_content.split('\n'):
        if 'RAG_SIMILARITY_THRESHOLD' in line and '=' in line:
            print(f"\nUpdated setting: {line}")
    
    return True

if __name__ == "__main__":
    success = fix_similarity_threshold()
    if success:
        print("\n✓ RAG similarity threshold issue fixed!")
        print("The threshold has been lowered from 0.7 to 0.6.")
    else:
        print("\n✗ Failed to fix the RAG similarity threshold issue.")
        sys.exit(1)
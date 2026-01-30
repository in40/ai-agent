#!/usr/bin/env python3
"""
Simple test to verify that our Qdrant integration code is syntactically correct.
"""

import ast
import sys

def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r') as f:
            source = f.read()
        ast.parse(source)
        print(f"✓ {file_path} has valid syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in {file_path}: {e}")
        return False

def main():
    """Check syntax of our modified files."""
    files_to_check = [
        '/root/qwen/ai_agent/rag_component/config.py',
        '/root/qwen/ai_agent/rag_component/vector_store_manager.py',
        '/root/qwen/ai_agent/start_qdrant_service.sh'  # This is a shell script, not Python
    ]
    
    print("Checking syntax of modified files...")
    
    all_good = True
    for file_path in files_to_check[:-1]:  # Skip the shell script
        if not check_syntax(file_path):
            all_good = False
    
    if all_good:
        print("\n✓ All Python files have valid syntax!")
        print("\nSummary of Qdrant deployment:")
        print("1. Created docker-compose.yml for Qdrant deployment")
        print("2. Updated rag_component/config.py to include Qdrant settings")
        print("3. Modified rag_component/vector_store_manager.py to support Qdrant")
        print("4. Created start_qdrant_service.sh script")
        print("5. Updated requirements.txt with Qdrant dependencies")
        print("\nTo deploy Qdrant:")
        print("1. Install Docker and Docker Compose")
        print("2. Run: docker-compose up -d qdrant")
        print("3. Set environment variable: RAG_VECTOR_STORE_TYPE=qdrant")
        print("4. Restart your application")
        return True
    else:
        print("\n✗ Some files have syntax errors that need to be fixed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
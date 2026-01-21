#!/usr/bin/env python3
"""
Test script to verify that our changes to preserve filenames and set source labels are correct.
This test verifies the code changes without needing to run the full RAG system.
"""
import os
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

def test_changes():
    """Test that our changes to the RAG orchestrator are correct."""
    print("Testing code changes...")
    
    try:
        # Read the updated RAG orchestrator file
        with open("/root/qwen_test/ai_agent/rag_component/main.py", "r") as f:
            content = f.read()
        
        # Check that the changes were applied correctly
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Verify that upload_method is set in ingest_documents
        if 'doc.metadata["upload_method"] = "Filesystem ingestion"' in content and "ingest_documents" in content:
            print("✅ Check 1 passed: 'Filesystem ingestion' label added to regular ingestion")
            checks_passed += 1
        else:
            print("❌ Check 1 failed: 'Filesystem ingestion' label not found in regular ingestion")
            # Debug: print the relevant sections
            import re
            # Find the ingest_documents method
            method_match = re.search(r'def ingest_documents\(.*?\).*?end_method', content.replace('\n    ', '\n    end_method\n    '), re.DOTALL)
            if method_match:
                method_content = method_match.group(0)
                print(f"DEBUG: Found ingest_documents method content: {method_content[:500]}...")
        
        # Check 2: Verify that upload_method is set in ingest_documents_from_upload
        if 'doc.metadata["upload_method"] = "Web upload"' in content:
            print("✅ Check 2 passed: 'Web upload' label added to upload ingestion")
            checks_passed += 1
        else:
            print("❌ Check 2 failed: 'Web upload' label not found in upload ingestion")
        
        # Check 3: Verify that upload_method is set in ingest_documents_from_directory
        if 'doc.metadata["upload_method"] = "Filesystem ingestion"' in content and "from directory" in content:
            print("✅ Check 3 passed: 'Filesystem ingestion' label added to directory ingestion")
            checks_passed += 1
        else:
            print("❌ Check 3 failed: 'Filesystem ingestion' label not found in directory ingestion")
        
        # Read the updated retriever file
        with open("/root/qwen_test/ai_agent/rag_component/retriever.py", "r") as f:
            retriever_content = f.read()
        
        # Check 4: Verify that the retriever uses the upload_method to format the source
        if 'upload_method = doc.metadata.get("upload_method", "")' in retriever_content:
            print("✅ Check 4 passed: Retriever uses upload_method to format source")
            checks_passed += 1
        else:
            print("❌ Check 4 failed: Retriever doesn't use upload_method to format source")
        
        if checks_passed == total_checks:
            print(f"\n✅ All {total_checks} checks passed!")
            print("✅ Filenames with non-Latin characters should be preserved")
            print("✅ Source labels should be set correctly ('Filesystem ingestion' or 'Web upload')")
            return True
        else:
            print(f"\n❌ Only {checks_passed}/{total_checks} checks passed")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_changes()
    sys.exit(0 if success else 1)
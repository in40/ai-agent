#!/usr/bin/env python3
"""
Unit test for the processed document import functionality
"""
import sys
import os
sys.path.insert(0, '/root/qwen/ai_agent')

def test_import_processed_endpoint_exists():
    """Test that the import_processed endpoint exists in the RAG app"""
    try:
        from backend.services.rag.app import app
        # Check if the endpoint exists by looking at the registered routes
        endpoint_found = False
        for rule in app.url_map.iter_rules():
            if 'import_processed' in str(rule):
                endpoint_found = True
                break
        
        if endpoint_found:
            print("✅ import_processed endpoint exists in RAG service")
            return True
        else:
            print("❌ import_processed endpoint NOT found in RAG service")
            return False
    except Exception as e:
        print(f"❌ Error checking RAG endpoint: {e}")
        return False

def test_gateway_route_exists():
    """Test that the gateway has the route for import_processed"""
    try:
        from backend.services.gateway.app import app
        # Check if the endpoint exists by looking at the registered routes
        endpoint_found = False
        for rule in app.url_map.iter_rules():
            if 'import_processed' in str(rule):
                endpoint_found = True
                break
        
        if endpoint_found:
            print("✅ import_processed route exists in Gateway service")
            return True
        else:
            print("❌ import_processed route NOT found in Gateway service")
            return False
    except Exception as e:
        print(f"❌ Error checking Gateway route: {e}")
        return False

def validate_sample_json():
    """Validate the sample JSON file structure"""
    try:
        import json
        sample_file_path = '/root/qwen/ai_agent/imports/GOST_R_52633.3-2011.json'
        
        with open(sample_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check required fields
        required_fields = ['document', 'chunks']
        for field in required_fields:
            if field not in data:
                print(f"❌ Sample JSON missing required field: {field}")
                return False
        
        if not isinstance(data['chunks'], list):
            print("❌ Sample JSON chunks field is not a list")
            return False
        
        if len(data['chunks']) == 0:
            print("❌ Sample JSON has empty chunks array")
            return False
        
        # Check first chunk has required fields
        first_chunk = data['chunks'][0]
        if 'content' not in first_chunk:
            print("❌ First chunk in sample JSON missing content field")
            return False
        
        print(f"✅ Sample JSON is valid with {len(data['chunks'])} chunks")
        return True
    except Exception as e:
        print(f"❌ Error validating sample JSON: {e}")
        return False

if __name__ == "__main__":
    print("Running unit tests for processed document import functionality...\n")
    
    test1 = test_import_processed_endpoint_exists()
    test2 = test_gateway_route_exists()
    test3 = validate_sample_json()
    
    print(f"\nResults:")
    print(f"- RAG endpoint exists: {'PASS' if test1 else 'FAIL'}")
    print(f"- Gateway route exists: {'PASS' if test2 else 'FAIL'}")
    print(f"- Sample JSON valid: {'PASS' if test3 else 'FAIL'}")
    
    if test1 and test2 and test3:
        print("\n🎉 All unit tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
#!/usr/bin/env python3
"""
Simple test to verify the MCP Search Server can be imported and instantiated
"""

import sys
import os
sys.path.insert(0, '/root/qwen_test/ai_agent')

from mcp_search_server import MCPSearchServer
from unittest.mock import patch, MagicMock


def test_import_and_instantiation():
    """Test that the search server can be imported and instantiated"""
    print("Testing import and instantiation of MCPSearchServer...")
    
    # Mock the environment variable to avoid errors
    with patch.dict(os.environ, {'BRAVE_SEARCH_API_KEY': 'test-key'}):
        try:
            # Create an instance of the server
            server = MCPSearchServer(
                host='127.0.0.1',
                port=8092,
                registry_url='http://127.0.0.1:8086',
                log_level='INFO'
            )
            
            print(f"✓ Successfully created MCPSearchServer instance")
            print(f"  Host: {server.host}")
            print(f"  Port: {server.port}")
            print(f"  Registry URL: {server.registry_url}")
            print(f"  API Key available: {'Yes' if server.brave_api_key else 'No'}")
            
            # Verify that the perform_search method exists
            assert hasattr(server, 'perform_search'), "perform_search method should exist"
            print("✓ perform_search method exists")
            
            # Verify that the start method exists
            assert hasattr(server, 'start'), "start method should exist"
            print("✓ start method exists")
            
            # Verify that the stop method exists
            assert hasattr(server, 'stop'), "stop method should exist"
            print("✓ stop method exists")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating MCPSearchServer instance: {str(e)}")
            return False


def test_perform_search_method():
    """Test the perform_search method with mocked API call"""
    print("\nTesting perform_search method...")
    
    with patch.dict(os.environ, {'BRAVE_SEARCH_API_KEY': 'test-key'}):
        server = MCPSearchServer(
            host='127.0.0.1',
            port=8092,
            registry_url='http://127.0.0.1:8086',
            log_level='INFO'
        )
        
        # Mock the requests.get call to avoid actual API call
        with patch('requests.get') as mock_get:
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'web': {
                    'results': [
                        {
                            'title': 'Test Result',
                            'url': 'https://example.com',
                            'description': 'This is a test result',
                            'date': '2023-01-01',
                            'language': 'en',
                            'thumbnail': {}
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            # Call the perform_search method
            success, results, error = server.perform_search("test query")
            
            print(f"Success: {success}")
            print(f"Number of results: {len(results)}")
            print(f"Error: {error}")
            
            if success and len(results) > 0:
                print("✓ perform_search method works correctly with mocked API")
                return True
            else:
                print("✗ perform_search method did not return expected results")
                return False


if __name__ == "__main__":
    print("Running basic tests for MCP Search Server...")
    
    test1_passed = test_import_and_instantiation()
    test2_passed = test_perform_search_method()
    
    if test1_passed and test2_passed:
        print("\n✓ All tests PASSED: MCP Search Server implementation looks good!")
        sys.exit(0)
    else:
        print("\n✗ Some tests FAILED")
        sys.exit(1)
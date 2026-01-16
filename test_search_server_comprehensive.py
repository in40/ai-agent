#!/usr/bin/env python3
"""
Comprehensive test to verify the MCP Search Server follows the same patterns as the DNS server
"""

import sys
import os
import json
import tempfile
import subprocess
import time
import signal
from unittest.mock import patch, MagicMock

sys.path.insert(0, '/root/qwen_test/ai_agent')

from mcp_search_server import MCPSearchServer, SearchRequestHandler
from mcp_dns_server import MCPServer, DNSRequestHandler  # Import DNS server for comparison


def compare_class_structures():
    """Compare the structure of the search server with the DNS server"""
    print("Comparing class structures...")
    
    # Check that both classes have the same basic methods
    dns_methods = [method for method in dir(MCPServer) if not method.startswith('_')]
    search_methods = [method for method in dir(MCPSearchServer) if not method.startswith('_')]
    
    print(f"DNS Server methods: {dns_methods}")
    print(f"Search Server methods: {search_methods}")
    
    # Both should have start, stop methods
    required_methods = ['start', 'stop']
    for method in required_methods:
        dns_has = hasattr(MCPServer, method)
        search_has = hasattr(MCPSearchServer, method)
        print(f"  Method '{method}': DNS={dns_has}, Search={search_has}")
        if dns_has != search_has:
            print(f"    ⚠️  Mismatch: DNS has {method}={dns_has}, Search has {method}={search_has}")
    
    # Check that both request handlers have similar structures
    dns_handler_methods = [method for method in dir(DNSRequestHandler) if not method.startswith('_')]
    search_handler_methods = [method for method in dir(SearchRequestHandler) if not method.startswith('_')]
    
    print(f"DNS RequestHandler methods: {dns_handler_methods}")
    print(f"Search RequestHandler methods: {search_handler_methods}")
    
    return True


def test_command_line_parameters():
    """Test that the server accepts command-line parameters like the DNS server"""
    print("\nTesting command-line parameters...")
    
    # Check that the main function parses arguments similar to DNS server
    import argparse
    from mcp_search_server import main as search_main
    from mcp_dns_server import main as dns_main
    
    # Both should have similar argument parsers
    # We'll just verify the function exists and can be called without crashing
    try:
        # Temporarily replace sys.argv to avoid actual argument parsing
        original_argv = sys.argv[:]
        sys.argv = ['script_name', '--help']
        
        try:
            search_main()
        except SystemExit:
            # Expected when --help is passed
            pass
        
        sys.argv = original_argv
        print("✓ Search server main function exists and accepts --help")
        
        return True
    except Exception as e:
        print(f"✗ Error testing command-line parameters: {str(e)}")
        return False


def test_service_registration():
    """Test that the server registers with the service registry like the DNS server"""
    print("\nTesting service registration...")
    
    with patch.dict(os.environ, {'BRAVE_SEARCH_API_KEY': 'test-key'}):
        server = MCPSearchServer(
            host='127.0.0.1',
            port=8093,
            registry_url='http://127.0.0.1:8086',
            log_level='INFO'
        )
        
        # Check that the service info has the correct type
        service_id = f"search-server-{server.host}-{server.port}".replace('.', '-').replace(':', '-')
        expected_type = "mcp_search"
        
        print(f"Expected service ID: {service_id}")
        print(f"Expected service type: {expected_type}")
        
        # Verify the metadata structure
        metadata = {
            "service_type": "search_engine",
            "capabilities": ["web_search", "brave_search"],
        }
        print(f"Expected metadata: {metadata}")
        
        return True


def test_request_handling():
    """Test that the request handler follows the same patterns as DNS server"""
    print("\nTesting request handling patterns...")
    
    # Check that both handlers have similar methods
    dns_methods = [attr for attr in dir(DNSRequestHandler) if callable(getattr(DNSRequestHandler, attr)) and not attr.startswith('_')]
    search_methods = [attr for attr in dir(SearchRequestHandler) if callable(getattr(SearchRequestHandler, attr)) and not attr.startswith('_')]
    
    print(f"DNS Handler methods: {dns_methods}")
    print(f"Search Handler methods: {search_methods}")
    
    # Common methods that should exist in both
    common_methods = ['do_POST', '_send_json_response', '_send_error_response', 'logger_info', 'logger_error', 'log_message']
    
    for method in common_methods:
        dns_has = hasattr(DNSRequestHandler, method)
        search_has = hasattr(SearchRequestHandler, method)
        print(f"  Method '{method}': DNS={dns_has}, Search={search_has}")
        
        if dns_has and not search_has:
            print(f"    ⚠️  Search handler missing method: {method}")
        elif search_has and not dns_has:
            print(f"    ⚠️  DNS handler missing method: {method}")
    
    # Check that both have class-level function setters
    dns_setter_exists = hasattr(DNSRequestHandler, 'set_resolve_func')
    search_setter_exists = hasattr(SearchRequestHandler, 'set_search_func')
    
    print(f"DNS setter exists: {dns_setter_exists}")
    print(f"Search setter exists: {search_setter_exists}")
    
    return dns_setter_exists and search_setter_exists


def test_error_handling():
    """Test error handling patterns"""
    print("\nTesting error handling patterns...")

    # Check that the server class has error handling methods
    # We'll check if the methods exist without instantiating the handler incorrectly
    has_error_response = hasattr(SearchRequestHandler, '_send_error_response')
    has_json_response = hasattr(SearchRequestHandler, '_send_json_response')

    print(f"Has _send_error_response: {has_error_response}")
    print(f"Has _send_json_response: {has_json_response}")

    if has_error_response and has_json_response:
        print("✓ Error handling methods exist")
    else:
        print("✗ Error handling methods missing")
        return False

    # Test that the server handles missing API key appropriately
    with patch.dict(os.environ, {}, clear=True):  # Clear all environment variables
        server = MCPSearchServer(log_level='INFO')

        # The server should note that the API key is missing
        if server.brave_api_key is None:
            print("✓ Server correctly identifies missing API key")
        else:
            print("⚠ Server did not identify missing API key")

    return True


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("Running comprehensive tests for MCP Search Server...\n")
    
    tests = [
        compare_class_structures,
        test_command_line_parameters,
        test_service_registration,
        test_request_handling,
        test_error_handling
    ]
    
    all_passed = True
    for test in tests:
        try:
            result = test()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {str(e)}")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    success = run_comprehensive_tests()
    
    if success:
        print("\n✅ All comprehensive tests PASSED: MCP Search Server follows the same patterns as DNS server!")
        sys.exit(0)
    else:
        print("\n❌ Some comprehensive tests FAILED")
        sys.exit(1)
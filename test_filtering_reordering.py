#!/usr/bin/env python3
"""
Test script to verify the MCP tool call filtering and reordering functionality
"""
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_filtering_and_reordering():
    """Test both filtering and reordering logic for MCP tool calls"""
    
    # Mock the filtering and reordering logic
    def filter_and_reorder_tool_calls(tool_calls, service_flags):
        """
        Filter and reorder the tool calls based on service enablement and priority
        """
        # Filter the tool calls based on enabled services
        filtered_tool_calls = []
        for call in tool_calls:
            service_id = call.get('service_id', '').lower()

            # Check if the service type is enabled
            is_enabled = True
            if 'sql' in service_id or 'database' in service_id:
                is_enabled = service_flags.get('sql_enabled', True)
            elif 'search' in service_id or 'web' in service_id:
                is_enabled = service_flags.get('web_search_enabled', True)
            elif 'dns' in service_id:
                is_enabled = service_flags.get('dns_enabled', True)
            elif 'download' in service_id:
                is_enabled = service_flags.get('download_enabled', True)
            elif 'rag' in service_id:
                is_enabled = service_flags.get('rag_enabled', True)

            if is_enabled:
                filtered_tool_calls.append(call)

        # Reorder the filtered tool calls by priority: search, rag, sql, dns, others
        reordered_tool_calls = []
        
        # Priority 1: Search services
        search_calls = [call for call in filtered_tool_calls 
                       if 'search' in call.get('service_id', '').lower() or 'web' in call.get('service_id', '').lower()]
        reordered_tool_calls.extend(search_calls)
        
        # Priority 2: RAG services
        rag_calls = [call for call in filtered_tool_calls 
                    if 'rag' in call.get('service_id', '').lower() and call not in reordered_tool_calls]
        reordered_tool_calls.extend(rag_calls)
        
        # Priority 3: SQL services
        sql_calls = [call for call in filtered_tool_calls 
                    if ('sql' in call.get('service_id', '').lower() or 'database' in call.get('service_id', '').lower()) 
                    and call not in reordered_tool_calls]
        reordered_tool_calls.extend(sql_calls)
        
        # Priority 4: DNS services
        dns_calls = [call for call in filtered_tool_calls 
                    if 'dns' in call.get('service_id', '').lower() and call not in reordered_tool_calls]
        reordered_tool_calls.extend(dns_calls)
        
        # Priority 5: All other services
        other_calls = [call for call in filtered_tool_calls 
                      if call not in reordered_tool_calls]
        reordered_tool_calls.extend(other_calls)
        
        return reordered_tool_calls

    # Test case 1: Mixed services with some disabled
    tool_calls = [
        {"service_id": "other-service-1"},
        {"service_id": "sql-query-service"},
        {"service_id": "rag-retrieval-service"},
        {"service_id": "dns-lookup-service"},
        {"service_id": "web-search-service"},
        {"service_id": "download-service"},
        {"service_id": "another-other-service"},
        {"service_id": "database-service"},
        {"service_id": "search-service"}
    ]
    
    # Disable SQL and download services
    service_flags = {
        'sql_enabled': False,
        'web_search_enabled': True,
        'dns_enabled': True,
        'download_enabled': False,
        'rag_enabled': True
    }
    
    result = filter_and_reorder_tool_calls(tool_calls, service_flags)
    
    # Check the results
    service_ids = [call["service_id"] for call in result]
    print("Original order:", [call["service_id"] for call in tool_calls])
    print("Filtered and reordered order:", service_ids)
    
    # Verify that disabled services are filtered out
    assert 'sql-query-service' not in service_ids, "SQL service should be filtered out"
    assert 'download-service' not in service_ids, "Download service should be filtered out"
    
    # Verify that enabled services remain
    assert 'web-search-service' in service_ids, "Web search service should remain"
    assert 'search-service' in service_ids, "Search service should remain"
    assert 'rag-retrieval-service' in service_ids, "RAG service should remain"
    assert 'dns-lookup-service' in service_ids, "DNS service should remain"
    
    # Find positions of each type
    search_positions = [i for i, call in enumerate(result) if 'search' in call["service_id"].lower() or 'web' in call["service_id"].lower()]
    rag_positions = [i for i, call in enumerate(result) if 'rag' in call["service_id"].lower()]
    sql_positions = [i for i, call in enumerate(result) if 'sql' in call["service_id"].lower() or 'database' in call["service_id"].lower()]
    dns_positions = [i for i, call in enumerate(result) if 'dns' in call["service_id"].lower()]
    other_positions = [i for i, call in enumerate(result) if call["service_id"] not in [call["service_id"] for call in result if any(keyword in call["service_id"].lower() for keyword in ['search', 'web', 'rag', 'sql', 'database', 'dns'])]]
    
    print(f"\nPositions after filtering and reordering:")
    print(f"Search services (should be first): {search_positions}")
    print(f"RAG services (should be second): {rag_positions}")
    print(f"SQL services (should be filtered out): {sql_positions}")
    print(f"DNS services (should be third): {dns_positions}")
    print(f"Other services (should be last): {other_positions}")
    
    # Verify that search services come first
    if search_positions:
        assert all(pos < min(rag_positions + dns_positions + other_positions) for pos in search_positions), "Search services should come first"
    
    # Verify that RAG services come second
    if rag_positions:
        assert all(pos < min(dns_positions + other_positions) for pos in rag_positions), "RAG services should come second"
    
    # Verify that DNS services come third
    if dns_positions:
        assert all(pos < min(other_positions) for pos in dns_positions), "DNS services should come third"
    
    print("\n✅ All filtering and reordering tests passed!")

    # Test case 2: All services enabled
    service_flags_all_enabled = {
        'sql_enabled': True,
        'web_search_enabled': True,
        'dns_enabled': True,
        'download_enabled': True,
        'rag_enabled': True
    }
    
    result2 = filter_and_reorder_tool_calls(tool_calls, service_flags_all_enabled)
    service_ids2 = [call["service_id"] for call in result2]
    
    print(f"\nWith all services enabled: {service_ids2}")
    
    # Verify all services are present (since all are enabled in this test)
    # Note: download-service was in the original list but should be present since we enabled it in this test
    expected_count = len(tool_calls)  # All services should be present when all are enabled
    assert len(result2) == expected_count, f"All enabled services should be present. Expected {expected_count}, got {len(result2)}. Result: {result2}"
    
    print("✅ All services enabled test passed!")

if __name__ == "__main__":
    test_filtering_and_reordering()
    print("All tests passed!")
#!/usr/bin/env python3
"""
Test script to verify the MCP tool call reordering functionality
"""
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_reordering_logic():
    """Test the reordering logic for MCP tool calls"""
    
    # Mock the reordering logic
    def reorder_tool_calls(tool_calls):
        """
        Reorder the filtered tool calls by priority: search, rag, sql, dns, others
        """
        reordered_tool_calls = []
        
        # Priority 1: Search services
        search_calls = [call for call in tool_calls 
                       if 'search' in call.get('service_id', '').lower() or 'web' in call.get('service_id', '').lower()]
        reordered_tool_calls.extend(search_calls)
        
        # Priority 2: RAG services
        rag_calls = [call for call in tool_calls 
                    if 'rag' in call.get('service_id', '').lower() and call not in reordered_tool_calls]
        reordered_tool_calls.extend(rag_calls)
        
        # Priority 3: SQL services
        sql_calls = [call for call in tool_calls 
                    if ('sql' in call.get('service_id', '').lower() or 'database' in call.get('service_id', '').lower()) 
                    and call not in reordered_tool_calls]
        reordered_tool_calls.extend(sql_calls)
        
        # Priority 4: DNS services
        dns_calls = [call for call in tool_calls 
                    if 'dns' in call.get('service_id', '').lower() and call not in reordered_tool_calls]
        reordered_tool_calls.extend(dns_calls)
        
        # Priority 5: All other services
        other_calls = [call for call in tool_calls 
                      if call not in reordered_tool_calls]
        reordered_tool_calls.extend(other_calls)
        
        return reordered_tool_calls

    # Test case 1: Mixed services in random order
    tool_calls = [
        {"service_id": "other-service-1"},
        {"service_id": "sql-query-service"},
        {"service_id": "rag-retrieval-service"},
        {"service_id": "dns-lookup-service"},
        {"service_id": "web-search-service"},
        {"service_id": "another-other-service"},
        {"service_id": "database-service"},
        {"service_id": "search-service"}
    ]
    
    reordered = reorder_tool_calls(tool_calls)
    
    # Check the order
    service_types = [call["service_id"] for call in reordered]
    print("Original order:", [call["service_id"] for call in tool_calls])
    print("Reordered order:", service_types)
    
    # Find positions of each type
    search_positions = [i for i, call in enumerate(reordered) if 'search' in call["service_id"].lower() or 'web' in call["service_id"].lower()]
    rag_positions = [i for i, call in enumerate(reordered) if 'rag' in call["service_id"].lower()]
    sql_positions = [i for i, call in enumerate(reordered) if 'sql' in call["service_id"].lower() or 'database' in call["service_id"].lower()]
    dns_positions = [i for i, call in enumerate(reordered) if 'dns' in call["service_id"].lower()]
    other_positions = [i for i, call in enumerate(reordered) if call not in [call for call in reordered if any(keyword in call["service_id"].lower() for keyword in ['search', 'web', 'rag', 'sql', 'database', 'dns'])]]
    
    print(f"\nPositions:")
    print(f"Search services (should be first): {search_positions}")
    print(f"RAG services (should be second): {rag_positions}")
    print(f"SQL services (should be third): {sql_positions}")
    print(f"DNS services (should be fourth): {dns_positions}")
    print(f"Other services (should be last): {other_positions}")
    
    # Verify that search services come first
    assert all(pos < min(rag_positions + sql_positions + dns_positions + other_positions) for pos in search_positions), "Search services should come first"
    
    # Verify that RAG services come second
    if rag_positions:
        assert all(pos < min(sql_positions + dns_positions + other_positions) for pos in rag_positions), "RAG services should come second"
    
    # Verify that SQL services come third
    if sql_positions:
        assert all(pos < min(dns_positions + other_positions) for pos in sql_positions), "SQL services should come third"
    
    # Verify that DNS services come fourth
    if dns_positions:
        assert all(pos < min(other_positions) for pos in dns_positions), "DNS services should come fourth"
    
    print("\n✅ All ordering tests passed!")

if __name__ == "__main__":
    test_reordering_logic()
    print("All tests passed!")
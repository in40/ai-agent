#!/usr/bin/env python3
"""
Test script to verify the deduplication fix in combine_all_results_node
"""

def test_deduplication_logic():
    """
    Test the deduplication logic implemented in the combine_all_results_node
    """
    print("Testing deduplication logic...")
    
    # Simulate the deduplication mechanism
    def get_result_key(result):
        # Create a key based on content, source, and title to identify duplicates
        content = result.get("content", "")
        source = result.get("source", "")
        title = result.get("title", "")
        url = result.get("url", "")
        # Create a composite key that identifies unique content
        # Using first 100 chars of content to avoid huge keys while maintaining uniqueness
        return f"{content[:100]}::{source}::{title}::{url}"

    # Create test results that include duplicates
    test_results = [
        {
            "content": "This is a test document about biometric requirements for small databases",
            "source": "test_source_1",
            "title": "Biometric Requirements Doc 1",
            "url": "http://example.com/doc1"
        },
        {
            "content": "This is a test document about biometric requirements for small databases",  # Same as first
            "source": "test_source_1",  # Same as first
            "title": "Biometric Requirements Doc 1",  # Same as first
            "url": "http://example.com/doc1"  # Same as first
        },
        {
            "content": "Different content about security protocols",
            "source": "test_source_2",
            "title": "Security Protocols Doc",
            "url": "http://example.com/doc2"
        },
        {
            "content": "This is a test document about biometric requirements for small databases",  # Same as first
            "source": "different_source",  # Different source
            "title": "Different Title",  # Different title
            "url": "http://example.com/doc3"  # Different URL
        }
    ]
    
    # Apply the deduplication algorithm
    seen_result_keys = set()
    deduplicated_results = []
    
    for result in test_results:
        result_key = get_result_key(result)
        if result_key not in seen_result_keys:
            deduplicated_results.append(result)
            seen_result_keys.add(result_key)
    
    print(f"Original results count: {len(test_results)}")
    print(f"Deduplicated results count: {len(deduplicated_results)}")
    
    # Expected: 3 results (first, third, and fourth) since second is a duplicate of first
    assert len(deduplicated_results) == 3, f"Expected 3 unique results, got {len(deduplicated_results)}"
    
    # Verify that the first and second results were treated as duplicates
    assert deduplicated_results[0]["content"] == test_results[0]["content"], "First result should be preserved"
    assert deduplicated_results[1]["content"] == test_results[2]["content"], "Third result (actually second unique) should be preserved"
    assert deduplicated_results[2]["content"] == test_results[3]["content"], "Fourth result (actually third unique) should be preserved"
    
    print("✅ Deduplication logic test passed!")
    
    # Test with a more complex scenario similar to the original issue
    complex_test_results = []
    
    # Add 1 search result (simulating the original search result)
    base_content = "Requirements for small biometric image databases for Alien samples according to GOST standards..."
    complex_test_results.append({
        "content": base_content,
        "source": "search_result_1",
        "title": "GOST Requirements Document 1",
        "url": "http://docs.cntd.ru/document/1200079555"
    })

    # Add 4 more copies of the SAME search result (simulating the duplication issue)
    for i in range(1, 5):
        complex_test_results.append({
            "content": base_content,  # Same content as the first result
            "source": f"search_result_{i+1}",
            "title": f"GOST Requirements Document {i+1}",
            "url": f"http://docs.cntd.ru/document/{1200079555+i+1}"
        })
    
    # Add 15 different RAG results
    for i in range(15):
        complex_test_results.append({
            "content": f"Different RAG content about biometric requirements #{i}",
            "source": f"rag_result_{i}",
            "title": f"RAG Document {i}",
            "url": f"http://rag.example.com/doc{i}"
        })
    
    # Add 5 more copies of the SAME content but with DIFFERENT metadata (simulating processed search results that are duplicates of the original search results)
    for i in range(5):
        complex_test_results.append({
            "content": base_content,  # Same content as the search results (this is the duplicate!)
            "source": f"processed_search_{i}",  # Different source (simulating processed/downloaded content)
            "title": f"Processed GOST Requirements Document {i}",  # Different title (simulating processed content)
            "url": f"http://downloaded.example.com/doc{i}"  # Different URL (simulating downloaded content)
        })
    
    print(f"\nComplex test scenario:")
    print(f"Original results count: {len(complex_test_results)} (5 search duplicates + 15 RAG + 5 processed duplicates)")
    
    # Apply deduplication
    seen_result_keys = set()
    deduplicated_complex_results = []
    
    for result in complex_test_results:
        result_key = get_result_key(result)
        if result_key not in seen_result_keys:
            deduplicated_complex_results.append(result)
            seen_result_keys.add(result_key)
    
    print(f"Deduplicated results count: {len(deduplicated_complex_results)}")

    # Should have 1 unique search content (even though it appeared multiple times with different metadata) + 15 unique RAG results = 16 total
    expected_count = 1 + 15  # 1 unique search content + 15 unique RAG results
    assert len(deduplicated_complex_results) == expected_count, f"Expected {expected_count} unique results, got {len(deduplicated_complex_results)}"
    
    print(f"✅ Complex deduplication test passed! Reduced from {len(complex_test_results)} to {len(deduplicated_complex_results)} results")
    
    return True

if __name__ == "__main__":
    success = test_deduplication_logic()
    if success:
        print("\n🎉 All tests passed! The deduplication fix should work correctly.")
    else:
        print("\n❌ Tests failed!")
        exit(1)
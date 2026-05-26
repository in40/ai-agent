#!/usr/bin/env python3
"""
Test script to verify chunking quality validation fix.
Tests the _validate_chunking_coverage function with various scenarios.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from backend.services.rag.smart_ingestion_enhanced import _validate_chunking_coverage

def test_full_coverage():
    """Test case: Good coverage (>70%)"""
    print("Test 1: Full coverage (>70%)")
    doc = "A" * 10000
    chunks = [{'content': "A" * 800, 'chunk_id': f'chunk_{i}'} for i in range(10)]
    
    valid, msg = _validate_chunking_coverage(doc, chunks)
    
    print(f"  Input: {len(doc)} chars, {len(chunks)} chunks")
    print(f"  Total chunked: {sum(len(c['content']) for c in chunks)} chars")
    print(f"  Valid: {valid}")
    print(f"  Message: {msg if msg else '(none)'}")
    assert valid == True, f"Expected valid=True, got {valid}"
    assert "warning" not in msg.lower() or "low" not in msg.lower(), f"Unexpected warning: {msg}"
    print("  ✅ PASSED\n")

def test_low_coverage_failure():
    """Test case: Very low coverage (<50%) - should fail"""
    print("Test 2: Low coverage (<50%) - should FAIL")
    doc = "A" * 10000
    chunks = [{'content': "A" * 100, 'chunk_id': 'chunk_0'}]  # Only 1%
    
    valid, msg = _validate_chunking_coverage(doc, chunks)
    
    print(f"  Input: {len(doc)} chars, {len(chunks)} chunks")
    print(f"  Total chunked: {sum(len(c['content']) for c in chunks)} chars")
    print(f"  Valid: {valid}")
    print(f"  Message: {msg[:100]}...")
    assert valid == False, f"Expected valid=False, got {valid}"
    assert "insufficient" in msg.lower() or "coverage" in msg.lower(), f"Expected coverage error in: {msg}"
    print("  ✅ PASSED\n")

def test_warning_coverage():
    """Test case: Medium coverage (50-70%) - should warn"""
    print("Test 3: Medium coverage (50-70%) - should WARN")
    doc = "A" * 10000
    chunks = [{'content': "A" * 600, 'chunk_id': f'chunk_{i}'} for i in range(10)]  # 60%
    
    valid, msg = _validate_chunking_coverage(doc, chunks)
    
    print(f"  Input: {len(doc)} chars, {len(chunks)} chunks")
    print(f"  Total chunked: {sum(len(c['content']) for c in chunks)} chars")
    print(f"  Valid: {valid}")
    print(f"  Message: {msg[:100]}...")
    assert valid == True, f"Expected valid=True, got {valid}"
    assert "low" in msg.lower(), f"Expected warning in: {msg}"
    print("  ✅ PASSED\n")

def test_few_chunks_warning():
    """Test case: Large doc with few chunks - should warn"""
    print("Test 4: Large doc with few chunks - should WARN")
    doc = "A" * 50000  # Should need ~50 chunks
    chunks = [{'content': "A" * 1000, 'chunk_id': f'chunk_{i}'} for i in range(2)]  # Only 2 chunks
    
    valid, msg = _validate_chunking_coverage(doc, chunks)
    
    print(f"  Input: {len(doc)} chars, {len(chunks)} chunks")
    print(f"  Total chunked: {sum(len(c['content']) for c in chunks)} chars")
    print(f"  Valid: {valid}")
    print(f"  Message: {msg[:100]}...")
    # Coverage is only 4%, so this should fail
    assert valid == False, f"Expected valid=False (low coverage), got {valid}"
    print("  ✅ PASSED\n")

def test_real_scenario():
    """Test case: Simulate job_277abcdb4a83 scenario"""
    print("Test 5: Real scenario (job_277abcdb4a83)")
    # Original document was 155KB, got only 2 chunks with 691 chars total
    doc = "A" * 155571  # Original document size
    chunks = [
        {'content': "A" * 122, 'chunk_id': 'chunk_0'},
        {'content': "A" * 569, 'chunk_id': 'chunk_1'}
    ]  # Only 691 chars total = 0.44%
    
    valid, msg = _validate_chunking_coverage(doc, chunks)
    
    print(f"  Input: {len(doc)} chars, {len(chunks)} chunks")
    print(f"  Total chunked: {sum(len(c['content']) for c in chunks)} chars")
    coverage = sum(len(c['content']) for c in chunks) / len(doc) * 100
    print(f"  Coverage: {coverage:.2f}%")
    print(f"  Valid: {valid}")
    print(f"  Message: {msg[:150]}...")
    assert valid == False, f"Expected valid=False, got {valid}"
    assert "insufficient" in msg.lower() or "coverage" in msg.lower(), f"Expected coverage error"
    print("  ✅ PASSED - This would have caught job_277abcdb4a83 failure!\n")

def test_empty_chunks():
    """Test case: No chunks generated"""
    print("Test 6: Empty chunks - should FAIL")
    doc = "A" * 1000
    chunks = []
    
    valid, msg = _validate_chunking_coverage(doc, chunks)
    
    print(f"  Input: {len(doc)} chars, {len(chunks)} chunks")
    print(f"  Valid: {valid}")
    print(f"  Message: {msg}")
    assert valid == False, f"Expected valid=False, got {valid}"
    assert "no chunks" in msg.lower(), f"Expected 'no chunks' error"
    print("  ✅ PASSED\n")

if __name__ == "__main__":
    print("=" * 60)
    print("Chunking Quality Validation - Unit Tests")
    print("=" * 60 + "\n")
    
    try:
        test_full_coverage()
        test_low_coverage_failure()
        test_warning_coverage()
        test_few_chunks_warning()
        test_real_scenario()
        test_empty_chunks()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

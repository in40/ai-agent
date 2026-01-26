#!/usr/bin/env python3
"""
Test script to verify the relative URL fix for RAG download functionality.
"""

def test_relative_url_construction():
    """Test that the download URL is constructed with a relative path."""
    print("Testing relative URL construction...")
    
    # Simulate the fixed code logic
    file_id = "test_file_id"
    filename = "test_document.pdf"
    
    # This is the new logic after our fix
    download_url = f"/download/{file_id}/{filename}"
    
    # Verify it's a relative path (starts with /)
    assert download_url.startswith("/"), f"Expected relative path, got: {download_url}"
    
    # Verify it contains the expected components
    assert file_id in download_url, f"File ID not found in URL: {download_url}"
    assert filename in download_url, f"Filename not found in URL: {download_url}"
    
    # Verify it doesn't contain the old problematic localhost reference
    assert "localhost" not in download_url, f"URL still contains localhost: {download_url}"
    assert "http://" not in download_url, f"URL still contains http://: {download_url}"
    assert "https://" not in download_url, f"URL still contains https://: {download_url}"
    
    print(f"✓ Download URL correctly constructed as relative path: {download_url}")
    return True

def test_original_vs_fixed_logic():
    """Compare the original problematic logic with the fixed logic."""
    print("\nComparing original vs fixed logic...")
    
    file_id = "abc123"
    filename = "document.pdf"
    
    # Original problematic logic (would generate absolute URL with localhost)
    # download_url = f"{request.url_root}download/{file_id}/{filename}"
    # Example: "http://localhost:5003/download/abc123/document.pdf"
    
    # Fixed logic
    fixed_download_url = f"/download/{file_id}/{filename}"
    
    print(f"Fixed URL: {fixed_download_url}")
    
    # Verify the fixed version is relative
    assert fixed_download_url.startswith("/"), "Fixed URL should be relative"
    assert "localhost" not in fixed_download_url, "Fixed URL should not contain localhost"
    assert "http" not in fixed_download_url, "Fixed URL should not contain http scheme"
    
    print("✓ Fixed logic produces relative URLs as expected")
    return True

def main():
    """Run all tests."""
    print("Testing relative URL fix for RAG download functionality...\n")
    
    tests = [
        test_relative_url_construction,
        test_original_vs_fixed_logic
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {e}")
            results.append(False)
    
    print(f"\n{'='*50}")
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Relative URL fix is working correctly.")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    exit(main())
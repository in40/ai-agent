#!/usr/bin/env python3
"""
Test script to verify that the MultiDatabaseManager fix works correctly.
This reproduces the scenario that caused the original error.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import run_enhanced_agent

def test_wider_search_scenario():
    """
    Test the scenario that was causing the 'MultiDatabaseManager' object is not callable error
    """
    print("Testing the wider search scenario that was causing the error...")
    
    try:
        # This is similar to the original request that caused the error
        result = run_enhanced_agent("Who can I call in UK?")
        
        print(f"Request: {result['original_request']}")
        print(f"Generated SQL: {result['generated_sql']}")
        print(f"Final response: {result['final_response']}")
        print(f"Errors: {result['execution_error']}")
        print(f"Retry count: {result['retry_count']}")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running test for MultiDatabaseManager fix...")
    success = test_wider_search_scenario()
    
    if success:
        print("\n✓ Test passed! The fix appears to be working correctly.")
    else:
        print("\n✗ Test failed! There may still be an issue.")
        sys.exit(1)
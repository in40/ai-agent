#!/usr/bin/env python3
"""
Simple test to isolate the initialization issue.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_init():
    """
    Test just the initialization of DedicatedMCPModel
    """
    print("Testing DedicatedMCPModel initialization...")
    
    try:
        from models.dedicated_mcp_model import DedicatedMCPModel
        print("Import successful")
        
        # Initialize the DedicatedMCPModel
        print("Initializing DedicatedMCPModel...")
        mcp_model = DedicatedMCPModel()
        print("DedicatedMCPModel initialized successfully!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_init()
    if success:
        print("\n✓ Initialization test PASSED.")
    else:
        print("\n✗ Initialization test FAILED.")
        sys.exit(1)
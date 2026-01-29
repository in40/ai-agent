#!/usr/bin/env python3
"""
Test script to verify Qdrant cleanup functionality
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def test_script_exists():
    """Test that the cleanup script exists and is executable"""
    script_path = Path("qdrant_cleanup.py")
    if not script_path.exists():
        print(f"ERROR: {script_path} does not exist")
        return False
    
    # Check if it's a Python file with expected content
    with open(script_path, 'r') as f:
        content = f.read()
        if "Automated Qdrant Database Cleanup Script" not in content:
            print(f"ERROR: {script_path} does not contain expected header")
            return False
    
    print(f"✓ {script_path} exists and contains expected content")
    return True


def test_shell_script_exists():
    """Test that the shell wrapper exists and is executable"""
    script_path = Path("qdrant_cleanup.sh")
    if not script_path.exists():
        print(f"ERROR: {script_path} does not exist")
        return False
    
    # Check if it's executable
    if not os.access(script_path, os.X_OK):
        print(f"ERROR: {script_path} is not executable")
        return False
    
    with open(script_path, 'r') as f:
        content = f.read()
        if "Qdrant Cleanup Script" not in content:
            print(f"ERROR: {script_path} does not contain expected header")
            return False
    
    print(f"✓ {script_path} exists, is executable, and contains expected content")
    return True


def test_help_output():
    """Test that the script responds to --help"""
    try:
        result = subprocess.run([sys.executable, "qdrant_cleanup.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"ERROR: Help command failed with return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False
        
        if "Automate Qdrant database cleanup" not in result.stdout:
            print("ERROR: Help output doesn't contain expected text")
            return False
        
        print("✓ Help output test passed")
        return True
    except subprocess.TimeoutExpired:
        print("ERROR: Help command timed out")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run help test: {str(e)}")
        return False


def test_shell_help_output():
    """Test that the shell script responds to --help"""
    try:
        result = subprocess.run(["./qdrant_cleanup.sh", "--help"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"ERROR: Shell help command failed with return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False
        
        if "Usage:" not in result.stdout:
            print("ERROR: Shell help output doesn't contain expected text")
            return False
        
        print("✓ Shell help output test passed")
        return True
    except subprocess.TimeoutExpired:
        print("ERROR: Shell help command timed out")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run shell help test: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("Running tests on Qdrant cleanup scripts...")
    print()
    
    tests = [
        test_script_exists,
        test_shell_script_exists,
        test_help_output,
        test_shell_help_output
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
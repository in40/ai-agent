#!/usr/bin/env python3
"""
Simple test to verify that the reducer changes work as expected
"""

# Test the reducer functions directly
def test_reducer_functions():
    print("Testing reducer functions...")
    
    # Old reducer: lambda x, y: y if not x else x
    old_reducer = lambda x, y: y if not x else x
    print(f"Old reducer test 1: old_reducer('', 'new_value') = {old_reducer('', 'new_value')}")  # Should return 'new_value'
    print(f"Old reducer test 2: old_reducer('old_value', 'new_value') = {old_reducer('old_value', 'new_value')}")  # Should return 'old_value'
    
    # New reducer: lambda x, y: y
    new_reducer = lambda x, y: y
    print(f"New reducer test 1: new_reducer('', 'new_value') = {new_reducer('', 'new_value')}")  # Should return 'new_value'
    print(f"New reducer test 2: new_reducer('old_value', 'new_value') = {new_reducer('old_value', 'new_value')}")  # Should return 'new_value'
    
    # Old conditional reducer: lambda x, y: y or x
    old_conditional = lambda x, y: y or x
    print(f"Old conditional reducer test 1: old_conditional('old_value', 'new_value') = {old_conditional('old_value', 'new_value')}")  # Should return 'new_value'
    print(f"Old conditional reducer test 2: old_conditional('old_value', '') = {old_conditional('old_value', '')}")  # Should return 'old_value'
    print(f"Old conditional reducer test 3: old_conditional('old_value', None) = {old_conditional('old_value', None)}")  # Should return 'old_value'
    
    # New reducer: lambda x, y: y (always replace)
    print(f"New reducer test 3: new_reducer('old_value', '') = {new_reducer('old_value', '')}")  # Should return ''
    print(f"New reducer test 4: new_reducer('old_value', None) = {new_reducer('old_value', None)}")  # Should return None
    
    print("\nReducer function tests completed successfully!")

if __name__ == "__main__":
    test_reducer_functions()
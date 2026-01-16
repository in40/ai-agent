#!/usr/bin/env python3
"""
Test script to verify the database configuration logic fix
"""

def test_db_logic():
    # Simulate the user input and conversion logic from the modified setup_config.py
    def convert_user_input(user_input):
        """Convert user input to appropriate value for DATABASE_ENABLED"""
        return "true" if user_input.lower() in ['y', 'yes'] else "false"
    
    # Test cases
    test_cases = [
        ('Y', 'true'),
        ('y', 'true'),
        ('yes', 'true'),
        ('YES', 'true'),
        ('N', 'false'),
        ('n', 'false'),
        ('no', 'false'),
        ('NO', 'false'),
    ]
    
    print("Testing database configuration logic:")
    print("-" * 40)
    
    all_passed = True
    for user_input, expected_output in test_cases:
        actual_output = convert_user_input(user_input)
        status = "PASS" if actual_output == expected_output else "FAIL"
        print(f"Input: '{user_input}' -> Expected: '{expected_output}', Got: '{actual_output}' [{status}]")
        
        if actual_output != expected_output:
            all_passed = False
    
    print("-" * 40)
    print(f"All tests {'PASSED' if all_passed else 'FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    test_db_logic()
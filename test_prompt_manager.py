#!/usr/bin/env python3
"""
Test script to verify the prompt management system works correctly.
"""

from utils.prompt_manager import PromptManager

def test_prompt_management():
    """Test the prompt management functionality."""
    print("Testing Prompt Management System...")
    
    # Initialize the prompt manager
    pm = PromptManager()
    
    # List all prompts
    print("\n1. Listing all available prompts:")
    prompts = pm.list_prompts()
    for prompt in prompts:
        print(f"   - {prompt}")
    
    # Get a specific prompt
    print("\n2. Getting 'sql_generator' prompt:")
    sql_prompt = pm.get_prompt("sql_generator")
    if sql_prompt:
        print(f"   Content: {sql_prompt[:100]}...")  # Show first 100 chars
    else:
        print("   Prompt not found")
    
    # Test updating a prompt
    print("\n3. Testing prompt update:")
    original_content = pm.get_prompt("sql_generator")
    test_content = "This is a test update for the SQL generator prompt."
    
    if pm.update_prompt("sql_generator", test_content):
        print("   Update successful")
        # Verify the update
        updated_content = pm.get_prompt("sql_generator")
        if updated_content == test_content:
            print("   Verification successful")
        else:
            print("   Verification failed")
        
        # Restore original content
        pm.update_prompt("sql_generator", original_content)
        print("   Original content restored")
    else:
        print("   Update failed")
    
    # Test creating a new prompt
    print("\n4. Testing prompt creation:")
    new_prompt_name = "test_prompt"
    new_prompt_content = "This is a test prompt for testing purposes."
    
    if pm.create_prompt(new_prompt_name, new_prompt_content):
        print("   Creation successful")
        # Verify the creation
        created_content = pm.get_prompt(new_prompt_name)
        if created_content == new_prompt_content:
            print("   Verification successful")
        else:
            print("   Verification failed")
        
        # Clean up - delete the test prompt
        if pm.delete_prompt(new_prompt_name):
            print("   Test prompt deleted successfully")
        else:
            print("   Failed to delete test prompt")
    else:
        print("   Creation failed")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_prompt_management()
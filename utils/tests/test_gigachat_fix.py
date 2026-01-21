#!/usr/bin/env python3
"""
Test script to verify that the GigaChat structured output fix works correctly.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gigachat_structured_output():
    """
    Test that the GigaChat model supports structured output.
    """
    print("Testing GigaChat structured output fix...")
    
    # Set environment variables for GigaChat
    os.environ["SQL_LLM_PROVIDER"] = "GigaChat"
    os.environ["SQL_LLM_MODEL"] = "GigaChat:latest"
    os.environ["GIGACHAT_CREDENTIALS"] = os.getenv("GIGACHAT_CREDENTIALS", "fake_credentials")
    os.environ["GIGACHAT_SCOPE"] = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    os.environ["GIGACHAT_ACCESS_TOKEN"] = os.getenv("GIGACHAT_ACCESS_TOKEN", "")
    
    try:
        from utils.gigachat_integration import GigaChatModel
        from models.sql_generator import SQLOutput  # Import from the correct location
        from langchain_core.prompts import ChatPromptTemplate
        
        # Create a GigaChat model instance
        model = GigaChatModel(
            model="GigaChat:latest",
            temperature=0,
            credentials=os.environ["GIGACHAT_CREDENTIALS"],
            scope=os.environ["GIGACHAT_SCOPE"],
            access_token=os.environ["GIGACHAT_ACCESS_TOKEN"]
        )
        
        print("✓ GigaChat model created successfully")
        
        # Test with_structured_output method
        structured_model = model.with_structured_output(SQLOutput)
        print("✓ with_structured_output method works")
        
        # Test creating a simple chain (this is what was failing before)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an SQL generator. Respond with a JSON object containing a 'sql_query' field."),
            ("human", "Generate a simple SELECT query for a users table: {input}")
        ])
        
        chain = prompt | structured_model
        print("✓ Chain creation with structured output works")
        
        print("\n✓ All tests passed! The GigaChat structured output fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sql_generator_with_gigachat():
    """
    Test that the SQLGenerator works with GigaChat provider.
    """
    print("\nTesting SQLGenerator with GigaChat provider...")
    
    # Set environment variables for GigaChat
    os.environ["SQL_LLM_PROVIDER"] = "GigaChat"
    os.environ["SQL_LLM_MODEL"] = "GigaChat:latest"
    os.environ["GIGACHAT_CREDENTIALS"] = os.getenv("GIGACHAT_CREDENTIALS", "fake_credentials")
    os.environ["GIGACHAT_SCOPE"] = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    os.environ["GIGACHAT_ACCESS_TOKEN"] = os.getenv("GIGACHAT_ACCESS_TOKEN", "")
    os.environ["ENABLE_SCREEN_LOGGING"] = "false"
    
    try:
        from models.sql_generator import SQLGenerator
        
        # Create a SQLGenerator instance (this is where the error was occurring)
        sql_gen = SQLGenerator()
        print("✓ SQLGenerator created successfully with GigaChat provider")
        
        print("\n✓ SQLGenerator test passed!")
        return True
        
    except Exception as e:
        print(f"✗ SQLGenerator test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running GigaChat structured output fix tests...\n")
    
    success1 = test_gigachat_structured_output()
    success2 = test_sql_generator_with_gigachat()
    
    if success1 and success2:
        print("\n🎉 All tests passed! The fix is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
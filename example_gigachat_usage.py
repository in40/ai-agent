#!/usr/bin/env python3
"""
Example script demonstrating how to use GigaChat models with OAuth token authentication
in the AI Agent framework.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_gigachat_example():
    """
    Example of how to configure the AI Agent to use GigaChat models.
    """
    print("Setting up GigaChat example...")
    
    # Set environment variables for GigaChat
    os.environ["SQL_LLM_PROVIDER"] = "GigaChat"
    os.environ["SQL_LLM_MODEL"] = "GigaChat:latest"
    os.environ["RESPONSE_LLM_PROVIDER"] = "GigaChat"
    os.environ["RESPONSE_LLM_MODEL"] = "GigaChat:latest"
    os.environ["PROMPT_LLM_PROVIDER"] = "GigaChat"
    os.environ["PROMPT_LLM_MODEL"] = "GigaChat:latest"
    
    # Set GigaChat specific configurations
    # These would normally come from environment variables or a config file
    os.environ["GIGACHAT_CREDENTIALS"] = os.getenv("GIGACHAT_CREDENTIALS", "your_credentials_here")
    os.environ["GIGACHAT_SCOPE"] = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    os.environ["GIGACHAT_ACCESS_TOKEN"] = os.getenv("GIGACHAT_ACCESS_TOKEN", "")
    
    print("Environment configured for GigaChat usage.")
    print("Note: You need valid GigaChat credentials to make actual API calls.")
    
    # Import and create the AI Agent
    try:
        from ai_agent import AIAgent
        agent = AIAgent()
        print("✓ AI Agent created successfully with GigaChat configuration")
        
        # Show the configuration
        print(f"SQL Generator LLM Provider: {os.environ.get('SQL_LLM_PROVIDER')}")
        print(f"Response Generator LLM Provider: {os.environ.get('RESPONSE_LLM_PROVIDER')}")
        print(f"Prompt Generator LLM Provider: {os.environ.get('PROMPT_LLM_PROVIDER')}")
        
        return agent
    except Exception as e:
        print(f"✗ Error creating AI Agent: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("GigaChat Integration Example")
    print("=" * 30)
    
    agent = setup_gigachat_example()
    
    if agent:
        print("\n✓ GigaChat integration is properly configured!")
        print("\nTo use GigaChat with OAuth token authentication:")
        print("1. Set GIGACHAT_CREDENTIALS with your authorization credentials")
        print("2. Optionally set GIGACHAT_SCOPE (default: GIGACHAT_API_PERS)")
        print("3. Optionally set GIGACHAT_ACCESS_TOKEN if you have a pre-generated token")
        print("4. Set your LLM provider to 'GigaChat' for any of the model components")
        print("\nThe AI Agent will now use GigaChat models with OAuth authentication.")
    else:
        print("\n✗ Failed to set up GigaChat integration.")

if __name__ == "__main__":
    main()
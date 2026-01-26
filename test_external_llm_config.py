#!/usr/bin/env python3
"""
Test script to verify marker external LLM configuration
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_external_llm_config():
    """Test the external LLM configuration"""
    print("Testing external LLM configuration...")
    
    # Test different configurations
    configs = [
        {
            "name": "LM Studio (OpenAI Compatible)",
            "env_vars": {
                "MARKER_LLM_PROVIDER": "openai",
                "OPENAI_BASE_URL": "http://asus-tus:1234/v1",
                "OPENAI_MODEL": "gemini-2.5-flash",
                "OPENAI_API_KEY": "lm-studio"
            }
        },
        {
            "name": "Ollama",
            "env_vars": {
                "MARKER_LLM_PROVIDER": "ollama",
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "OLLAMA_MODEL": "llama3.2-vision"
            }
        },
        {
            "name": "OpenAI",
            "env_vars": {
                "MARKER_LLM_PROVIDER": "openai",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
                "OPENAI_MODEL": "gpt-4o",
                "OPENAI_API_KEY": "sk-..."
            }
        }
    ]
    
    for config in configs:
        print(f"\nTesting configuration: {config['name']}")
        for key, value in config['env_vars'].items():
            print(f"  {key}={value}")
    
    print("\nConfiguration test completed.")
    print("To use any of these configurations, set the environment variables before running the PDF conversion.")
    
    return True

def show_current_config():
    """Show the current environment configuration"""
    print("\nCurrent environment configuration:")
    
    env_vars = [
        "MARKER_LLM_PROVIDER",
        "OPENAI_BASE_URL", 
        "OPENAI_MODEL",
        "OPENAI_API_KEY",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "GEMINI_API_KEY",
        "CLAUDE_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_API_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "Not set")
        if "KEY" in var and value != "Not set":
            value = "*" * len(value)  # Mask key values
        print(f"  {var}={value}")

def main():
    print("Marker External LLM Configuration Test")
    print("="*50)
    
    show_current_config()
    test_external_llm_config()
    
    print("\nTo configure marker to use an external LLM:")
    print("1. Set the appropriate environment variables")
    print("2. Restart the RAG service")
    print("3. Upload a PDF file to test the configuration")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Demonstration script for the default model feature.
This script shows how the system can use a default model configuration
when specific model configurations are not provided.
"""

import os
from config.settings import (
    DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL, DEFAULT_LLM_HOSTNAME, DEFAULT_LLM_PORT, DEFAULT_LLM_API_PATH
)

def demo_default_model_feature():
    """Demonstrate the default model feature."""
    print("=== Default Model Feature Demonstration ===\n")
    
    print("1. Default Model Configuration:")
    print(f"   Provider: {DEFAULT_LLM_PROVIDER}")
    print(f"   Model: {DEFAULT_LLM_MODEL}")
    print(f"   Hostname: {DEFAULT_LLM_HOSTNAME}")
    print(f"   Port: {DEFAULT_LLM_PORT}")
    print(f"   API Path: {DEFAULT_LLM_API_PATH}")
    print()
    
    print("2. How the Default Model Feature Works:")
    print("   - When you don't specify a specific model for a task (like SQL generation),")
    print("     the system uses the default model configuration.")
    print("   - You can also explicitly set a provider to 'default' to force usage of the default model.")
    print()
    
    print("3. Environment Variables for Default Model:")
    print("   You can customize the default model by setting these environment variables:")
    print("   - DEFAULT_LLM_PROVIDER: The provider to use (e.g., 'LM Studio', 'OpenAI', 'Ollama')")
    print("   - DEFAULT_LLM_MODEL: The model name to use")
    print("   - DEFAULT_LLM_HOSTNAME: The hostname of the LLM service")
    print("   - DEFAULT_LLM_PORT: The port of the LLM service")
    print("   - DEFAULT_LLM_API_PATH: The API path for the LLM service")
    print()
    
    print("4. Example Usage:")
    print("   # To use the default model for all tasks, you can set:")
    print("   export SQL_LLM_PROVIDER='default'")
    print("   export RESPONSE_LLM_PROVIDER='default'")
    print("   export PROMPT_LLM_PROVIDER='default'")
    print("   # ... and so on for other model types")
    print()
    
    print("5. Benefits:")
    print("   - Simplifies configuration when using the same model for all tasks")
    print("   - Reduces the number of environment variables to manage")
    print("   - Provides a fallback when specific configurations are not set")
    print()
    
    print("The default model feature is now active in your system!")
    print("All model classes (SQLGenerator, ResponseGenerator, etc.) will use the default configuration")
    print("when specific configurations are not provided or are set to 'default'.")


if __name__ == "__main__":
    demo_default_model_feature()
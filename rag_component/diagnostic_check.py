#!/usr/bin/env python3
"""
Detailed diagnostic script to check marker configuration.
"""
import os

def detailed_diagnostic():
    print("DETAILED DIAGNOSTICS FOR MARKER LLM CONFIGURATION")
    print("=" * 50)
    
    # Check all relevant environment variables
    print("Environment Variables:")
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
        value = os.getenv(var, "NOT SET")
        print(f"  {var}: {value}")
    
    print()
    
    # Check specifically for MARKER_LLM_PROVIDER
    marker_provider = os.getenv("MARKER_LLM_PROVIDER", "")
    print(f"MARKER_LLM_PROVIDER value: '{marker_provider}'")
    print(f"Boolean evaluation: {bool(marker_provider)}")
    print(f"String length: {len(marker_provider)}")
    
    if marker_provider:
        print(f"Lowercase value: '{marker_provider.lower()}'")
        valid_providers = ["openai", "ollama", "gemini", "claude", "azure"]
        if marker_provider.lower() in valid_providers:
            print(f"✓ Valid provider: {marker_provider.lower()}")
        else:
            print(f"⚠ Possibly invalid provider: {marker_provider.lower()}")
    else:
        print("ℹ️  MARKER_LLM_PROVIDER is not set or is empty")
        print("   To enable external LLM, set one of these values:")
        print("   - openai, ollama, gemini, claude, azure")
    
    print()
    print("To fix this, you need to set the environment variable:")
    print("export MARKER_LLM_PROVIDER=openai  # or another provider")
    print()
    print("Then restart your services for the changes to take effect.")

if __name__ == "__main__":
    detailed_diagnostic()
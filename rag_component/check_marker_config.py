#!/usr/bin/env python3
"""
Script to check if marker library configuration is properly set up to use external LLMs.
"""

import os
import sys
sys.path.append('/root/qwen_test/ai_agent/rag_component')

def check_marker_config():
    """Check if marker library is configured to use external LLMs."""

    print("Checking marker library configuration for external LLM usage...")

    # Check if MARKER_LLM_PROVIDER is set
    marker_llm_provider = os.getenv("MARKER_LLM_PROVIDER", "")
    print(f"MARKER_LLM_PROVIDER: '{marker_llm_provider}'")

    if not marker_llm_provider:
        print("\nWARNING: MARKER_LLM_PROVIDER is not set!")
        print("To enable external LLM for marker, set one of these environment variables:")
        print("  export MARKER_LLM_PROVIDER=openai")
        print("  export MARKER_LLM_PROVIDER=ollama")
        print("  export MARKER_LLM_PROVIDER=gemini")
        print("  export MARKER_LLM_PROVIDER=claude")
        print("  export MARKER_LLM_PROVIDER=azure")
        return False

    # Check provider-specific environment variables
    provider = marker_llm_provider.lower()

    if provider == "openai":
        openai_base_url = os.getenv("OPENAI_BASE_URL", "http://asus-tus:1234/v1")
        openai_model = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
        openai_api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
        print(f"  OPENAI_BASE_URL: '{openai_base_url}'")
        print(f"  OPENAI_MODEL: '{openai_model}'")
        print(f"  OPENAI_API_KEY: '{openai_api_key}'")

    elif provider == "ollama":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2-vision")
        print(f"  OLLAMA_BASE_URL: '{ollama_base_url}'")
        print(f"  OLLAMA_MODEL: '{ollama_model}'")

    elif provider == "gemini":
        gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        print(f"  GEMINI_API_KEY: '{gemini_api_key}'")

    elif provider == "claude":
        claude_api_key = os.getenv("CLAUDE_API_KEY", "")
        print(f"  CLAUDE_API_KEY: '{claude_api_key}'")

    elif provider == "azure":
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        print(f"  AZURE_OPENAI_ENDPOINT: '{azure_endpoint}'")
        print(f"  AZURE_OPENAI_DEPLOYMENT: '{azure_deployment}'")
        print(f"  AZURE_OPENAI_API_KEY: '{azure_api_key}'")

    print(f"\nMarker library is configured to use {provider.upper()} as LLM provider.")
    print("Configuration appears to be set up correctly.")
    return True

if __name__ == "__main__":
    check_marker_config()
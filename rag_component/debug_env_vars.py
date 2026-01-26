#!/usr/bin/env python3
"""
Debug script to check environment variables during runtime.
"""
import os
import sys
sys.path.append('/root/qwen_test/ai_agent/rag_component')

def check_environment_vars():
    """Check if the required environment variables are set during runtime."""
    print("Checking environment variables during runtime...")
    
    # Check if MARKER_LLM_PROVIDER is set
    marker_llm_provider = os.getenv("MARKER_LLM_PROVIDER", "")
    print(f"MARKER_LLM_PROVIDER: '{marker_llm_provider}'")
    
    # Check provider-specific environment variables
    if marker_llm_provider:
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
    
    # Check if marker library is available
    try:
        from marker.models import create_model_dict
        print("✓ Marker library is available")
    except ImportError as e:
        print(f"✗ Marker library is not available: {e}")
    
    # Check if we can instantiate the PDF converter
    try:
        import importlib.util
        import sys

        # Load the pdf_converter module directly
        spec = importlib.util.spec_from_file_location("pdf_converter", "/root/qwen_test/ai_agent/rag_component/pdf_converter.py")
        pdf_converter_module = importlib.util.module_from_spec(spec)

        # Add to sys.modules to handle relative imports
        sys.modules["pdf_converter"] = pdf_converter_module

        # Execute the module to load it
        spec.loader.exec_module(pdf_converter_module)

        # Now import the class
        PDFToMarkdownConverter = pdf_converter_module.PDFToMarkdownConverter
        converter = PDFToMarkdownConverter()
        print("✓ PDFToMarkdownConverter can be instantiated")
    except Exception as e:
        print(f"✗ PDFToMarkdownConverter instantiation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_environment_vars()
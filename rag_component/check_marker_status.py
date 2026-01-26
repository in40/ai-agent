#!/usr/bin/env python3
"""
Script to check the status of marker models and LLM configuration.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_marker_models_status():
    """Check the status of marker models and LLM configuration."""
    print("=" * 60)
    print("MARKER LIBRARY STATUS CHECK")
    print("=" * 60)
    
    # Check if marker library is available
    try:
        import marker
        print(f"✓ Marker library version: {marker.__version__ if hasattr(marker, '__version__') else 'unknown'}")
    except ImportError:
        print("✗ Marker library is not installed")
        return False
    
    # Check environment variables
    print("\nENVIRONMENT VARIABLES:")
    print("-" * 30)
    
    marker_llm_provider = os.getenv("MARKER_LLM_PROVIDER", "")
    print(f"MARKER_LLM_PROVIDER: '{marker_llm_provider}'")
    
    if marker_llm_provider:
        provider = marker_llm_provider.lower()
        
        if provider == "openai":
            openai_base_url = os.getenv("OPENAI_BASE_URL", "http://asus-tus:1234/v1")
            openai_model = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")
            openai_api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
            print(f"  OPENAI_BASE_URL: '{openai_base_url}'")
            print(f"  OPENAI_MODEL: '{openai_model}'")
            print(f"  OPENAI_API_KEY: '{openai_api_key[:5]}...' (truncated)")
            
        elif provider == "ollama":
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2-vision")
            print(f"  OLLAMA_BASE_URL: '{ollama_base_url}'")
            print(f"  OLLAMA_MODEL: '{ollama_model}'")
            
        elif provider == "gemini":
            gemini_api_key = os.getenv("GEMINI_API_KEY", "")
            print(f"  GEMINI_API_KEY: '{gemini_api_key[:5]}...' (truncated)" if gemini_api_key else "  GEMINI_API_KEY: not set")
            
        elif provider == "claude":
            claude_api_key = os.getenv("CLAUDE_API_KEY", "")
            print(f"  CLAUDE_API_KEY: '{claude_api_key[:5]}...' (truncated)" if claude_api_key else "  CLAUDE_API_KEY: not set")
            
        elif provider == "azure":
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
            azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
            print(f"  AZURE_OPENAI_ENDPOINT: '{azure_endpoint}'")
            print(f"  AZURE_OPENAI_DEPLOYMENT: '{azure_deployment}'")
            print(f"  AZURE_OPENAI_API_KEY: '{azure_api_key[:5]}...' (truncated)" if azure_api_key else "  AZURE_OPENAI_API_KEY: not set")
    
    # Check if we can load the model dictionary (this triggers base model loading)
    print(f"\nBASE MODEL STATUS:")
    print("-" * 30)
    
    try:
        from marker.models import create_model_dict
        print("✓ Marker models module is accessible")
        
        # Test if we can create the model dictionary (this will trigger base model loading)
        print("\nAttempting to load base models (this may take a moment)...")
        import time
        start_time = time.time()
        
        model_dict = create_model_dict()
        
        elapsed_time = time.time() - start_time
        print(f"✓ Base models loaded successfully in {elapsed_time:.2f} seconds")
        
        # Show some information about the loaded models
        print(f"  Number of models loaded: {len(model_dict) if model_dict else 0}")
        
        # Check for specific model types
        model_types = []
        if model_dict:
            for key in model_dict.keys():
                model_types.append(key)
        print(f"  Model types loaded: {model_types}")
        
    except Exception as e:
        print(f"✗ Error loading base models: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check LLM configuration
    print(f"\nLLM ENHANCEMENT CONFIGURATION:")
    print("-" * 30)
    
    if marker_llm_provider:
        print(f"✓ LLM enhancement is ENABLED")
        print(f"  Provider: {provider.upper()}")
        print(f"  LLM service will be used during conversion")
    else:
        print("ℹ️  LLM enhancement is DISABLED (using only base models)")
    
    print(f"\nSUMMARY:")
    print("-" * 30)
    print(f"• Base models: {'LOADED' if 'model_dict' in locals() else 'FAILED TO LOAD'}")
    print(f"• LLM enhancement: {'ENABLED' if marker_llm_provider else 'DISABLED'}")
    if marker_llm_provider:
        print(f"• LLM provider: {marker_llm_provider.upper()}")
    
    print("\n" + "=" * 60)
    print("STATUS CHECK COMPLETE")
    print("=" * 60)
    
    return True

def check_conversion_simulation():
    """Simulate a conversion to see if everything works together."""
    print(f"\nCONVERSION SIMULATION:")
    print("-" * 30)
    
    try:
        # Import the PDF converter
        import importlib.util
        import sys
        
        # Load the pdf_converter module directly
        spec = importlib.util.spec_from_file_location("pdf_converter", "/root/qwen_test/ai_agent/rag_component/pdf_converter.py")
        pdf_converter_module = importlib.util.module_from_spec(spec)
        
        # Execute the module to load it
        spec.loader.exec_module(pdf_converter_module)
        
        # Import the class
        PDFToMarkdownConverter = pdf_converter_module.PDFToMarkdownConverter
        
        # Check if we can instantiate the converter
        converter = PDFToMarkdownConverter()
        print("✓ PDFToMarkdownConverter instantiated successfully")
        
        # Check if the LLM provider is configured in the converter
        llm_provider = os.getenv("MARKER_LLM_PROVIDER", "")
        if llm_provider:
            print(f"✓ External LLM provider configured: {llm_provider}")
        else:
            print("ℹ️  External LLM provider not configured")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during conversion simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting marker models status check...")
    
    success = check_marker_models_status()
    
    if success:
        check_conversion_simulation()
    
    print(f"\nFor more detailed logs, check your application logs during PDF conversion.")
    print(f"The 'Loading models (this may take several minutes on first use)...' message")
    print(f"appears when the create_model_dict() function is called in the conversion process.")
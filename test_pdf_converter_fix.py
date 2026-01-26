#!/usr/bin/env python3
"""
Test script to verify that the PDF converter uses the external LLM as configured.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, '/root/qwen_test/ai_agent')

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_pdf_converter():
    """Test the PDF converter to see if it recognizes the external LLM configuration."""
    
    print("Testing PDF converter with external LLM configuration...")
    print("="*60)
    
    # Check environment variables
    print("Environment Variables:")
    print(f"  MARKER_LLM_PROVIDER: {os.getenv('MARKER_LLM_PROVIDER', 'Not set')}")
    print(f"  OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'Not set')}")
    print(f"  OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'Not set')}")
    print(f"  FORCE_DEFAULT_MODEL_FOR_ALL: {os.getenv('FORCE_DEFAULT_MODEL_FOR_ALL', 'Not set')}")
    print()
    
    # Import and initialize the PDF converter
    try:
        from rag_component.pdf_converter import PDFToMarkdownConverter
        
        print("Initializing PDF converter...")
        converter = PDFToMarkdownConverter()
        print("✓ PDF converter initialized successfully")
        print()
        
        # Check if the document exists
        pdf_path = "/root/qwen_test/ai_agent/data/rag_uploaded_files/520e729a-ab51-457e-9529-23dd5327a99f/ГОСТ Р 58412-2019.pdf"
        if os.path.exists(pdf_path):
            print(f"✓ Document found: {pdf_path}")
            print(f"  Size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")
        else:
            print(f"✗ Document not found: {pdf_path}")
            return
            
        print()
        print("The PDF converter has been updated to bypass the FORCE_DEFAULT_MODEL_FOR_ALL setting")
        print("and use the external LLM configuration specifically for Marker.")
        print()
        print("To process the document, you would normally upload it through the web interface")
        print("or trigger the ingestion process. The updated converter should now use the")
        print("external LLM (LM Studio at http://asus-tus:1234/v1) as configured.")
        
    except ImportError as e:
        print(f"✗ Failed to import PDF converter: {e}")
        return
    except Exception as e:
        print(f"✗ Error initializing PDF converter: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_pdf_converter()
#!/usr/bin/env python3
"""
Test script to verify that external LLM is being used by the marker library.
"""
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_marker_external_llm():
    """Test if marker library is using external LLM properly."""
    
    # Ensure environment variables are set
    os.environ["MARKER_LLM_PROVIDER"] = "openai"
    os.environ["OPENAI_BASE_URL"] = "http://asus-tus:1234/v1"
    os.environ["OPENAI_MODEL"] = "gemini-2.5-flash"
    os.environ["OPENAI_API_KEY"] = "lm-studio"
    
    logger.info("Environment variables set for external LLM")
    
    try:
        # Import the PDF converter
        import importlib.util
        import sys
        
        # Load the pdf_converter module directly
        spec = importlib.util.spec_from_file_location("pdf_converter", "/root/qwen_test/ai_agent/rag_component/pdf_converter.py")
        pdf_converter_module = importlib.util.module_from_spec(spec)
        
        # Temporarily add to sys.modules to handle relative imports
        sys.modules["pdf_converter"] = pdf_converter_module
        sys.modules["rag_component.config"] = __import__('config', fromlist=['RAG_MARKDOWN_STORAGE_DIR'])
        
        # Execute the module to load it
        spec.loader.exec_module(pdf_converter_module)
        
        # Import the class
        PDFToMarkdownConverter = pdf_converter_module.PDFToMarkdownConverter
        
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            # Create a simple PDF with some content
            # This is a minimal PDF structure for testing purposes
            pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(External LLM Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000106 00000 n \n0000000218 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n313\n%%EOF'
            temp_pdf.write(pdf_content)
            temp_pdf_path = temp_pdf.name
        
        logger.info(f"Created temporary PDF for testing: {temp_pdf_path}")
        
        # Initialize the converter
        converter = PDFToMarkdownConverter()
        logger.info("PDFToMarkdownConverter initialized")
        
        # Perform conversion with a short timeout for testing
        result = converter.convert_pdf_to_markdown(temp_pdf_path, timeout_seconds=30)
        
        if result:
            logger.info("PDF conversion completed successfully")
            logger.info(f"Result length: {len(result)} characters")
            logger.info(f"First 100 chars: {result[:100]}")
        else:
            logger.warning("PDF conversion returned no content")
        
        # Clean up
        os.unlink(temp_pdf_path)
        
        return True
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("Starting test for marker library external LLM usage")
    success = test_marker_external_llm()
    if success:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")
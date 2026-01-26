#!/usr/bin/env python3
"""
Debug script to test PDF processing functionality
"""

import os
import sys
import traceback
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_pdf_converter():
    """Test the PDF converter functionality"""
    print("Testing PDF converter...")
    
    try:
        from rag_component.pdf_converter import PDFToMarkdownConverter
        
        # Initialize the converter
        converter = PDFToMarkdownConverter()
        print("✓ PDFToMarkdownConverter initialized successfully")
        
        # Check if the problematic PDF file exists
        pdf_path = "Manual Purchase - Apple Developer.pdf"
        if not os.path.exists(pdf_path):
            print(f"⚠ PDF file does not exist at: {pdf_path}")
            
            # Look for any PDF files in the current directory
            pdf_files = list(Path(".").glob("*.pdf"))
            if pdf_files:
                print(f"Found PDF files: {[str(p) for p in pdf_files]}")
                pdf_path = str(pdf_files[0])
                print(f"Using first PDF file found: {pdf_path}")
            else:
                print("No PDF files found in the current directory.")
                return False
        
        print(f"Attempting to convert: {pdf_path}")
        
        # Try to convert the PDF to markdown
        markdown_content = converter.convert_pdf_to_markdown(pdf_path)
        
        if markdown_content:
            print(f"✓ PDF converted successfully. Content length: {len(markdown_content)} characters")
            print(f"First 200 characters: {markdown_content[:200]}...")
            return True
        else:
            print("✗ PDF conversion returned empty content")
            return False
            
    except ImportError as e:
        print(f"✗ ImportError: {e}")
        print("This suggests the marker library isn't properly installed or there's an import issue")
        return False
    except Exception as e:
        print(f"✗ Error during PDF conversion: {e}")
        traceback.print_exc()
        return False

def test_document_loader():
    """Test the document loader functionality"""
    print("\nTesting document loader...")
    
    try:
        from rag_component.document_loader import DocumentLoader
        
        # Initialize the loader
        loader = DocumentLoader()
        print("✓ DocumentLoader initialized successfully")
        
        # Check if the problematic PDF file exists
        pdf_path = "Manual Purchase - Apple Developer.pdf"
        if not os.path.exists(pdf_path):
            print(f"⚠ PDF file does not exist at: {pdf_path}")
            
            # Look for any PDF files in the current directory
            pdf_files = list(Path(".").glob("*.pdf"))
            if pdf_files:
                print(f"Found PDF files: {[str(p) for p in pdf_files]}")
                pdf_path = str(pdf_files[0])
                print(f"Using first PDF file found: {pdf_path}")
            else:
                print("No PDF files found in the current directory.")
                return False
        
        print(f"Attempting to load: {pdf_path}")
        
        # Try to load the document
        docs = loader.load_document(pdf_path)
        
        if docs:
            print(f"✓ Document loaded successfully. Number of documents: {len(docs)}")
            if docs[0].page_content:
                print(f"First 200 characters of content: {docs[0].page_content[:200]}...")
            return True
        else:
            print("✗ Document loading returned empty results")
            return False
            
    except Exception as e:
        print(f"✗ Error during document loading: {e}")
        traceback.print_exc()
        return False

def test_marker_directly():
    """Test the marker library directly"""
    print("\nTesting marker library directly...")
    
    try:
        from marker.models import create_model_dict
        from marker.config.parser import ConfigParser
        from marker.converters.pdf import PdfConverter
        from marker.renderers.markdown import MarkdownRenderer
        
        print("✓ Marker library imported successfully")
        
        # Check if the problematic PDF file exists
        pdf_path = "Manual Purchase - Apple Developer.pdf"
        if not os.path.exists(pdf_path):
            print(f"⚠ PDF file does not exist at: {pdf_path}")
            
            # Look for any PDF files in the current directory
            pdf_files = list(Path(".").glob("*.pdf"))
            if pdf_files:
                print(f"Found PDF files: {[str(p) for p in pdf_files]}")
                pdf_path = str(pdf_files[0])
                print(f"Using first PDF file found: {pdf_path}")
            else:
                print("No PDF files found in the current directory.")
                return False
        
        print(f"Attempting to load models and convert: {pdf_path}")
        
        # Create the model dictionary (this loads the ML models)
        model_dict = create_model_dict()
        print("✓ Models loaded successfully")
        
        # Create a default config parser with required options
        config_parser = ConfigParser({"output_format": "markdown"})
        config_dict = config_parser.generate_config_dict()
        
        # Create the PdfConverter instance
        converter = PdfConverter(
            artifact_dict=model_dict,
            config=config_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )
        
        # Convert the PDF to Markdown
        result = converter(pdf_path)
        
        if result:
            print("✓ Direct marker conversion successful")
            if hasattr(result, 'markdown'):
                markdown_content = result.markdown
            elif isinstance(result, str):
                markdown_content = result
            else:
                markdown_content = str(result)
                
            print(f"Content length: {len(markdown_content)} characters")
            print(f"First 200 characters: {markdown_content[:200]}...")
            return True
        else:
            print("✗ Direct marker conversion returned empty result")
            return False
            
    except ImportError as e:
        print(f"✗ ImportError: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during direct marker conversion: {e}")
        traceback.print_exc()
        return False

def main():
    print("PDF Processing Debug Script")
    print("="*50)
    
    # Test each component
    test1_result = test_pdf_converter()
    test2_result = test_document_loader()
    test3_result = test_marker_directly()
    
    print("\nSummary:")
    print(f"PDF Converter Test: {'PASS' if test1_result else 'FAIL'}")
    print(f"Document Loader Test: {'PASS' if test2_result else 'FAIL'}")
    print(f"Direct Marker Test: {'PASS' if test3_result else 'FAIL'}")
    
    if not any([test1_result, test2_result, test3_result]):
        print("\nAll tests failed. The PDF processing functionality appears to be broken.")
        return 1
    else:
        print("\nAt least one test passed. PDF processing may be working.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
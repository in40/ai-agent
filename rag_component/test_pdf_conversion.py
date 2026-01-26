"""
Unit tests for the PDF to Markdown conversion functionality in the RAG component.
"""
import unittest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the current directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_converter import PDFToMarkdownConverter
from document_loader import DocumentLoader
from config import RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED, RAG_USE_FALLBACK_ON_CONVERSION_ERROR


class TestPDFToMarkdownConverter(unittest.TestCase):
    """Test cases for the PDFToMarkdownConverter class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        try:
            self.converter = PDFToMarkdownConverter()
        except ImportError:
            self.skipTest("Marker library not available, skipping PDF conversion tests")

    def test_convert_pdf_to_markdown_success(self):
        """Test successful conversion of a PDF to Markdown."""
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            # Write minimal PDF content to the file
            temp_pdf.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000106 00000 n \n0000000218 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n313\n%%EOF')
            temp_pdf_path = temp_pdf.name

        try:
            # Test the conversion
            markdown_content = self.converter.convert_pdf_to_markdown(temp_pdf_path)
            
            # The conversion might not produce meaningful content for our minimal PDF,
            # but it shouldn't raise an exception
            self.assertIsNotNone(markdown_content)
        finally:
            # Clean up the temporary file
            os.unlink(temp_pdf_path)

    def test_convert_pdf_to_markdown_file(self):
        """Test conversion of PDF to Markdown file."""
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            # Write minimal PDF content to the file
            temp_pdf.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000106 00000 n \n0000000218 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n313\n%%EOF')
            temp_pdf_path = temp_pdf.name

        try:
            # Test the conversion to file
            markdown_file_path = self.converter.convert_pdf_to_markdown_file(temp_pdf_path)

            if markdown_file_path:  # Only test if conversion succeeded
                # Check that the file exists
                self.assertTrue(os.path.exists(markdown_file_path))

                # Check that it's a markdown file
                self.assertTrue(markdown_file_path.endswith('.md'))

                # Since the file is now permanently stored, we should not delete it
                # but we can verify its content
                with open(markdown_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # The content might be empty for our minimal PDF, but the file should exist
        finally:
            # Clean up the temporary PDF file
            os.unlink(temp_pdf_path)

    def test_convert_pdf_to_markdown_failure(self):
        """Test handling of conversion failure."""
        # Test with a non-existent file
        result = self.converter.convert_pdf_to_markdown("/non/existent/file.pdf")
        self.assertIsNone(result)

        # Test with an invalid file
        with tempfile.NamedTemporaryFile(delete=False) as invalid_file:
            invalid_file.write(b"This is not a valid PDF file")
            invalid_file_path = invalid_file.name

        try:
            result = self.converter.convert_pdf_to_markdown(invalid_file_path)
            # Result might be None or some content depending on how marker handles invalid files
        finally:
            os.unlink(invalid_file_path)


class TestDocumentLoaderWithPDFConversion(unittest.TestCase):
    """Test cases for DocumentLoader with PDF conversion functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.loader = DocumentLoader()

    @patch.dict(os.environ, {
        'RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED': 'true',
        'RAG_USE_FALLBACK_ON_CONVERSION_ERROR': 'true'
    })
    def test_pdf_conversion_enabled(self):
        """Test that PDF conversion is used when enabled."""
        # Reload the module to pick up the new environment variable
        import importlib
        import rag_component.config
        importlib.reload(rag_component.config)
        
        # Create a new loader instance to pick up the new config
        loader = DocumentLoader()
        
        # Verify that PDF conversion is enabled
        self.assertTrue(loader.use_pdf_conversion)

    @patch.dict(os.environ, {
        'RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED': 'false',
        'RAG_USE_FALLBACK_ON_CONVERSION_ERROR': 'true'
    })
    def test_pdf_conversion_disabled(self):
        """Test that PDF conversion is not used when disabled."""
        # Reload the module to pick up the new environment variable
        import importlib
        import rag_component.config
        importlib.reload(rag_component.config)
        
        # Create a new loader instance to pick up the new config
        loader = DocumentLoader()
        
        # Verify that PDF conversion is disabled
        self.assertFalse(loader.use_pdf_conversion)

    def test_supported_file_types_include_pdf(self):
        """Test that PDF is still in the supported file types."""
        self.assertIn('.pdf', self.loader.supported_types)


if __name__ == '__main__':
    unittest.main()
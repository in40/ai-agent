"""
Test suite for multi-pass PDF extraction with Russian language support.
"""
import os
import pytest
from rag_component.document_loader import DocumentLoader


class TestPDFExtraction:
    """Test PDF extraction with various document types"""

    def setup_method(self):
        """Set up test fixtures"""
        self.loader = DocumentLoader()
        self.test_dir = "/root/qwen/ai_agent/test_data/pdfs"

    def test_encoding_fix_method(self):
        """Test mojibake detection and fix"""
        mojibake_text = "ÔÅÄÅÐÀËÜÍÎÅ ÀÃÅÍÒÑÒÂÎ"
        fixed = self.loader._fix_russian_encoding(mojibake_text)

        # The fix converts mojibake to proper Cyrillic (may be uppercase)
        assert "Федеральное" in fixed or "ФЕДЕРАЛЬНОЕ" in fixed
        assert "агентство" in fixed or "АГЕНТСТВО" in fixed
        assert fixed != mojibake_text

    def test_cyrillic_validation(self):
        """Test Cyrillic text validation"""
        valid_russian = "Федеральное агентство по технической защите"
        invalid_text = "This is English text only"
        mojibake = "ÔÅÄÅÐÀËÜÍÎÅ"

        assert self.loader._is_valid_text(valid_russian) == True
        assert self.loader._is_valid_text(invalid_text) == True  # Valid English
        assert self.loader._is_valid_text(mojibake) == False  # Before fix, invalid

    def test_english_text_validation(self):
        """Test that English text is also validated correctly"""
        english_text = "This is a document about information security standards"
        assert self.loader._is_valid_text(english_text) == True

    def test_short_text_rejection(self):
        """Test that very short text is rejected"""
        short_text = "abc"
        assert self.loader._is_valid_text(short_text) == False

    def test_empty_text_rejection(self):
        """Test that empty text is rejected"""
        assert self.loader._is_valid_text("") == False
        assert self.loader._is_valid_text(None) == False

    def test_mixed_language_validation(self):
        """Test validation of mixed Russian/English text"""
        mixed_text = "ГОСТ Р 52069: Introduction to Information Security"
        assert self.loader._is_valid_text(mixed_text) == True

    @pytest.mark.skipif(not os.path.exists("/root/qwen/ai_agent/test_data/pdfs"), 
                        reason="Test PDFs not available")
    def test_normal_russian_pdf(self):
        """Test extraction of properly encoded Russian PDF"""
        # Find any Russian PDF from the backup
        pdf_files = [f for f in os.listdir(self.test_dir) if f.endswith('.pdf')]
        if not pdf_files:
            pytest.skip("No test PDFs available")
        
        # Try first PDF
        pdf_path = os.path.join(self.test_dir, pdf_files[0])
        docs = self.loader.load_document(pdf_path)

        assert len(docs) > 0
        assert len(docs[0].page_content) > 100
        assert docs[0].metadata["extraction_method"] in ["PyMuPDF", "pdfminer", "PyPDFLoader", "Tesseract OCR"]

    @pytest.mark.skipif(not os.path.exists("/root/qwen/ai_agent/test_data/pdfs"), 
                        reason="Test PDFs not available")
    def test_extraction_method_metadata(self):
        """Test that extraction method is recorded in metadata"""
        pdf_files = [f for f in os.listdir(self.test_dir) if f.endswith('.pdf')]
        if not pdf_files:
            pytest.skip("No test PDFs available")
        
        pdf_path = os.path.join(self.test_dir, pdf_files[0])
        docs = self.loader.load_document(pdf_path)

        assert "extraction_method" in docs[0].metadata
        assert docs[0].metadata["extraction_method"] in [
            "PyMuPDF", "pdfminer", "PyPDFLoader", "Tesseract OCR"
        ]
        assert docs[0].metadata["file_type"] == "pdf"
        assert "source" in docs[0].metadata


class TestDocumentLoaderGeneral:
    """Test general document loader functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.loader = DocumentLoader()

    def test_unsupported_file_type(self):
        """Test handling of unsupported file types"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            self.loader.load_document("/path/to/file.xyz")

    def test_txt_file_loading(self, tmp_path):
        """Test loading of text files"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content in Russian: Федеральный")
        
        docs = self.loader.load_document(str(txt_file))
        
        assert len(docs) == 1
        assert "Test content" in docs[0].page_content

    def test_load_documents_from_directory(self, tmp_path):
        """Test loading multiple documents from a directory"""
        # Create test files
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content")
        
        docs = self.loader.load_documents_from_directory(str(tmp_path))
        
        assert len(docs) > 0

"""
Document loader module for the RAG component.
Handles loading and preprocessing of various document types.
"""
import os
import re
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)
from langchain_core.documents import Document as LCDocument
from .config import RAG_SUPPORTED_FILE_TYPES, RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED, RAG_USE_FALLBACK_ON_CONVERSION_ERROR

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Class responsible for loading documents of various types."""

    def __init__(self):
        self.supported_types = RAG_SUPPORTED_FILE_TYPES
        self.use_pdf_conversion = RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED

    def load_document(self, file_path: str) -> List[LCDocument]:
        """
        Load a document based on its file extension.

        Args:
            file_path: Path to the document file

        Returns:
            List of LangChain Document objects
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext not in self.supported_types:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported types: {self.supported_types}")

        if file_ext == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_ext == '.pdf':
            # Check if PDF-to-Markdown conversion is enabled
            if self.use_pdf_conversion:
                try:
                    # Import the PDF converter
                    from .pdf_converter import PDFToMarkdownConverter

                    # Initialize the converter
                    converter = PDFToMarkdownConverter()

                    # Convert PDF to Markdown file with a much longer timeout (e.g., 3600 seconds = 1 hour) to allow complex PDFs to process
                    markdown_file_path = converter.convert_pdf_to_markdown_file(file_path, timeout_seconds=3600)

                    if markdown_file_path:
                        # Use UnstructuredMarkdownLoader for the converted Markdown
                        loader = UnstructuredMarkdownLoader(markdown_file_path)
                    else:
                        # If conversion failed, fall back to multi-pass PDF extraction
                        logger.warning(f"PDF conversion failed for {file_path}, falling back to multi-pass extraction")
                        return self._load_pdf_with_fallback(file_path)
                except ImportError:
                    # If marker is not available, fall back to multi-pass PDF extraction
                    logger.warning("Marker library not available, using multi-pass PDF extraction")
                    return self._load_pdf_with_fallback(file_path)
                except Exception as e:
                    # If conversion fails, fall back to multi-pass PDF extraction
                    logger.warning(f"PDF conversion error for {file_path}, falling back to multi-pass extraction: {str(e)}")
                    return self._load_pdf_with_fallback(file_path)
            else:
                # Use multi-pass PDF extraction directly if conversion is disabled
                return self._load_pdf_with_fallback(file_path)
        elif file_ext == '.docx':
            loader = Docx2txtLoader(file_path)
        elif file_ext == '.html':
            loader = UnstructuredHTMLLoader(file_path)
        elif file_ext == '.md':
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            # Default to text loader for any other supported type
            loader = TextLoader(file_path, encoding='utf-8')

        return loader.load()

    def _load_pdf_with_fallback(self, file_path: str) -> List[LCDocument]:
        """
        Multi-pass PDF extraction with encoding validation and fix.

        Tries multiple extraction methods in order:
        1. PyMuPDF (fast, good for most PDFs)
        2. pdfminer.six (better for complex encodings)
        3. PyPDFLoader (fallback, existing behavior)
        4. Tesseract OCR (for scanned PDFs, last resort)

        Args:
            file_path: Path to PDF file

        Returns:
            List of LangChain Document objects with validated text and processing metadata
        """
        import time
        start_time = time.time()
        
        extraction_methods = [
            ("PyMuPDF", self._extract_with_pymupdf),
            ("pdfminer", self._extract_with_pdfminer),
            ("PyPDFLoader", self._extract_with_pypdf),
            ("Tesseract OCR", self._extract_with_tesseract),
        ]

        for method_name, extract_func in extraction_methods:
            try:
                method_start = time.time()
                logger.debug(f"Trying {method_name} for {file_path}")

                # Extract text
                text = extract_func(file_path)
                method_time = time.time() - method_start

                if not text or len(text.strip()) < 10:
                    logger.debug(f"{method_name}: No text extracted")
                    continue

                # Fix encoding issues (mojibake)
                text_before_fix = text
                text = self._fix_russian_encoding(text)
                encoding_was_fixed = (text != text_before_fix)

                # Validate extracted text
                if self._is_valid_text(text):
                    total_time = time.time() - start_time
                    logger.info(f"Successfully extracted text from {file_path} using {method_name} in {total_time:.2f}s")
                    
                    return [LCDocument(
                        page_content=text,
                        metadata={
                            "source": file_path,
                            "extraction_method": method_name,
                            "extraction_time_seconds": round(total_time, 2),
                            "method_time_seconds": round(method_time, 2),
                            "encoding_was_fixed": encoding_was_fixed,
                            "file_type": "pdf",
                            "text_length": len(text),
                            "pdf_processing_metadata": {
                                "extraction_method": method_name,
                                "extraction_time_seconds": round(total_time, 2),
                                "method_time_seconds": round(method_time, 2),
                                "encoding_was_fixed": encoding_was_fixed,
                                "text_length": len(text),
                                "fallback_chain_position": extraction_methods.index((method_name, extract_func)) + 1,
                                "total_methods_tried": extraction_methods.index((method_name, extract_func)) + 1
                            }
                        }
                    )]
                else:
                    logger.debug(f"{method_name}: Extracted text failed validation")

            except Exception as e:
                logger.warning(f"{method_name} failed for {file_path}: {str(e)}")
                continue

        # All methods failed
        total_time = time.time() - start_time
        error_msg = f"All PDF extraction methods failed for {file_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    def _extract_with_pymupdf(self, file_path: str, pages: Optional[range] = None) -> str:
        """
        Extract text from PDF using PyMuPDF (fitz).
        Fast and works well for most PDFs.
        
        Args:
            file_path: Path to PDF file
            pages: Optional range of pages to extract (0-indexed). None means all pages.

        Returns:
            Extracted text content
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF not installed. Run: pip install PyMuPDF")

        text_parts = []
        doc = fitz.open(file_path)

        try:
            # Determine which pages to extract
            if pages is not None:
                page_nums = list(pages)
                # Clamp to valid range
                page_nums = [p for p in page_nums if 0 <= p < len(doc)]
            else:
                page_nums = range(len(doc))
            
            for page_num in page_nums:
                page = doc[page_num]
                # Extract text with flags for better Cyrillic support
                page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                text_parts.append(page_text)
        finally:
            doc.close()

        return '\n'.join(text_parts)

    def _extract_with_pdfminer(self, file_path: str) -> str:
        """
        Extract text using pdfminer.six.
        Better handling of complex encodings.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        try:
            from pdfminer.high_level import extract_text
        except ImportError:
            raise ImportError("pdfminer.six not installed. Run: pip install pdfminer.six")

        # Extract text with laparams for better layout analysis
        from pdfminer.layout import LAParams
        laparams = LAParams(
            detect_vertical=True,
            all_texts=True,
            line_margin=0.5
        )

        text = extract_text(file_path, laparams=laparams)
        return text

    def _extract_with_pypdf(self, file_path: str) -> str:
        """
        Extract text using pypdf (PyPDFLoader).
        Existing fallback behavior.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        return '\n'.join([page.page_content for page in pages])

    def _extract_with_tesseract(self, file_path: str) -> str:
        """
        Extract text using Tesseract OCR.
        For scanned PDFs or when other methods fail.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content
        """
        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError("OCR dependencies not installed. Run: pip install pytesseract pdf2image")

        # Convert PDF pages to images (300 DPI for good OCR quality)
        images = convert_from_path(file_path, dpi=300)

        text_parts = []
        for image in images:
            # OCR with Russian + English language support
            text = pytesseract.image_to_string(
                image,
                lang='rus+eng',  # Russian + English
                config='--psm 6'  # Assume uniform block of text
            )
            text_parts.append(text)

        return '\n'.join(text_parts)

    def _extract_with_llm(self, file_path: str) -> str:
        """
        Send PDF file directly to LLM with specialized prompt.
        LLM converts PDF to markdown.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            Markdown text from LLM
        """
        import base64
        
        # Use PDF-specific LLM config, fall back to NLP LLM config
        llm_base_url = os.getenv("PDF_LLM_BASE_URL", os.getenv("NLP_LLM_BASE_URL", "http://localhost:1234/v1"))
        llm_model = os.getenv("PDF_LLM_MODEL", os.getenv("NLP_LLM_MODEL", "qwen3.5-35b"))
        api_key = os.getenv("PDF_LLM_API_KEY", os.getenv("NLP_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "not-needed")))
        
        logger.info(f"Sending PDF to LLM: url={llm_base_url}, model={llm_model}")
        
        # Read and encode PDF
        with open(file_path, 'rb') as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = "convert this pdf file to markdown .md file"
        
        from openai import OpenAI
        
        client = OpenAI(base_url=llm_base_url, api_key=api_key)
        
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=32000,
            timeout=600
        )
        
        return response.choices[0].message.content

    def _fix_russian_encoding(self, text: str) -> str:
        """
        Detect and fix common Russian encoding issues (mojibake).

        Common issue: CP1251 text decoded as Latin-1
        Example: "Федеральное" → "ÔÅÄÅÐÀËÜÍÎÅ"

        Args:
            text: Text that may have encoding issues

        Returns:
            Fixed text with proper Cyrillic encoding
        """
        # Common mojibake patterns (CP1251 decoded as Latin-1)
        mojibake_indicators = [
            'ÔÅÄ',  # Федер
            'ÐÅÃ',  # Рег
            'ÒÅÕ',  # Тех
            'ÇÀÙ',  # Защ
            'ÈÍÔ',  # Инф
            'ïî',   # по (common word)
            'íà',   # на (common word)
        ]

        # Check if text looks like mojibake
        is_mojibake = any(pattern in text for pattern in mojibake_indicators)

        if is_mojibake:
            try:
                # Re-encode as Latin-1, decode as CP1251 (Russian Windows)
                fixed = text.encode('latin-1').decode('cp1251')
                logger.debug("Fixed mojibake encoding (CP1251 → UTF-8)")
                return fixed
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                logger.warning(f"Encoding fix failed: {e}")
                pass

        return text

    def _is_valid_text(self, text: str, min_cyrillic_ratio: float = 0.3) -> bool:
        """
        Validate that extracted text contains valid characters.
        For Russian documents, checks for Cyrillic characters.
        For English documents, checks for sufficient alphabetic content.

        Args:
            text: Text to validate
            min_cyrillic_ratio: Minimum ratio of Cyrillic characters (0.0-1.0)

        Returns:
            True if text appears to be valid (Russian or English)
        """
        if not text or len(text.strip()) < 10:
            return False

        # Count Cyrillic characters (Unicode range U+0400 to U+04FF)
        cyrillic_pattern = re.compile(r'[\u0400-\u04FF]')
        cyrillic_matches = cyrillic_pattern.findall(text)
        cyrillic_count = len(cyrillic_matches)

        # Calculate ratio
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        if total_chars == 0:
            return False

        cyrillic_ratio = cyrillic_count / total_chars

        # For Russian documents, expect at least 30% Cyrillic
        # For English documents, check for sufficient alphabetic content
        is_valid_cyrillic = cyrillic_ratio >= min_cyrillic_ratio
        
        # Also check for English text (if little Cyrillic, check for English letters)
        if not is_valid_cyrillic:
            # Check if it's valid English text
            english_pattern = re.compile(r'[a-zA-Z]')
            english_matches = english_pattern.findall(text)
            english_ratio = len(english_matches) / total_chars if total_chars > 0 else 0
            is_valid_english = english_ratio >= 0.5  # At least 50% English letters
            
            if is_valid_english:
                logger.debug("Text validated as English")
                return True
            else:
                logger.debug(f"Cyrillic ratio {cyrillic_ratio:.2f} below threshold {min_cyrillic_ratio}")
                return False

        logger.debug(f"Text validated as Cyrillic (ratio: {cyrillic_ratio:.2f})")
        return True

    def load_documents_from_directory(self, directory_path: str) -> List[LCDocument]:
        """
        Load all supported documents from a directory.

        Args:
            directory_path: Path to the directory containing documents

        Returns:
            List of LangChain Document objects
        """
        documents = []

        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()

                if file_ext in self.supported_types:
                    try:
                        loaded_docs = self.load_document(file_path)
                        documents.extend(loaded_docs)
                    except Exception as e:
                        logger.error(f"Error loading document {file_path}: {str(e)}")

        return documents

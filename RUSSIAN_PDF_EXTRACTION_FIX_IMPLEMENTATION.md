# Russian PDF Text Extraction Fix - Implementation Specification

**Document Version:** 1.0  
**Date:** February 28, 2026  
**Priority:** HIGH  
**Estimated Effort:** 2-3 days  

---

## Executive Summary

### Problem Statement

Russian-language PDF documents are being extracted with **4 different text quality variants**:

| Variant | Description | Example | Frequency |
|---------|-------------|---------|-----------|
| **1. Normal** | Correctly decoded Cyrillic | `Федеральное агентство` | ~40% |
| **2. Mojibake** | Wrong encoding (CP1251 as Latin-1) | `ÔÅÄÅÐÀËÜÍÎÅ` | ~35% |
| **3. Raw Bytes** | Unreadable PDF byte sequences | `/G80/G7c/G76/G91` | ~15% |
| **4. English** | Translated or English metadata | `Federal Agency` | ~10% |

**Impact:** Users cannot search, query, or analyze Russian documents properly. RAG queries return garbage or miss relevant documents.

### Root Cause

The current PDF extraction pipeline uses **a single extraction method** (PyPDFLoader via Marker library) which:
- Does not handle multiple PDF encoding formats
- Has no fallback for failed extractions
- Does not detect or fix mojibake (encoding errors)
- Has no OCR capability for scanned PDFs

### Solution Overview

Implement a **multi-pass PDF extraction pipeline** with:
1. **Multiple extraction methods** (PyMuPDF → pdfminer → Tesseract OCR)
2. **Encoding detection and correction** for mojibake
3. **Validation** to ensure extracted text is valid Cyrillic
4. **Fallback chain** - try next method if current fails

---

## 1. Technical Background

### 1.1 PDF Encoding Issues

Russian PDFs can have text encoded in multiple ways:

| Encoding | Description | Detection Pattern |
|----------|-------------|-------------------|
| **UTF-8** | Modern standard | Valid Unicode |
| **CP1251** | Windows Cyrillic | Bytes 0xC0-0xFF |
| **KOI8-R** | Unix Cyrillic | Bytes 0x80-0xFF |
| **Identity-H** | PDF internal encoding | ToUnicode CMap required |

**Mojibake occurs when:**
- PDF text is encoded in CP1251 (Windows Russian)
- Extractor decodes it as Latin-1/ISO-8859-1
- Result: `Федеральное` → `ÔÅÄÅÐÀËÜÍÎÅ`

**Fix:** Re-encode as Latin-1, decode as CP1251:
```python
fixed = mojibake_text.encode('latin-1').decode('cp1251')
```

### 1.2 PDF Text Extraction Methods

| Method | Library | Speed | Accuracy | OCR | Best For |
|--------|---------|-------|----------|-----|----------|
| **PyMuPDF** | `fitz` | Fast (0.5s/page) | 85-95% | No | Digital PDFs |
| **pdfminer.six** | `pdfminer` | Medium (1s/page) | 90-97% | No | Complex encodings |
| **pypdf** | `pypdf` | Fast (0.5s/page) | 80-90% | No | Simple PDFs |
| **Tesseract OCR** | `pytesseract` | Slow (3s/page) | 90-95% | Yes | Scanned PDFs |

---

## 2. Current Architecture

### 2.1 PDF Loading Flow

```
User Uploads PDF
    ↓
backend/services/rag/app.py (upload endpoint)
    ↓
DocumentLoader.load_document(file_path)
    ↓
┌─────────────────────────────────────────┐
│ IF RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED │
│   ↓                                      │
│ PDFToMarkdownConverter                   │
│   ↓                                      │
│ Marker Library (PyMuPDF internally)      │
│   ↓                                      │
│ Markdown file                            │
│   ↓                                      │
│ UnstructuredMarkdownLoader               │
└─────────────────────────────────────────┘
    ↓
    OR (if conversion disabled/failed)
    ↓
PyPDFLoader(file_path)
    ↓
List[LCDocument]
```

### 2.2 Files Involved

| File | Role | Lines of Code |
|------|------|---------------|
| `rag_component/document_loader.py` | **PRIMARY TARGET** - Main PDF loading gateway | ~120 |
| `rag_component/pdf_converter.py` | PDF → Markdown conversion (optional) | ~270 |
| `backend/services/rag/app.py` | Calls DocumentLoader (5 locations) | ~3400 |
| `backend/services/rag/smart_ingestion.py` | Calls DocumentLoader | ~600 |
| `backend/services/rag/smart_ingestion_enhanced.py` | Calls DocumentLoader (2 locations) | ~1100 |

### 2.3 Current Code (Problematic Section)

**File:** `rag_component/document_loader.py` (Lines 40-80)

```python
def load_document(self, file_path: str) -> List[LCDocument]:
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        # Check if PDF-to-Markdown conversion is enabled
        if self.use_pdf_conversion:
            try:
                from .pdf_converter import PDFToMarkdownConverter
                converter = PDFToMarkdownConverter()
                markdown_file_path = converter.convert_pdf_to_markdown_file(file_path)
                loader = UnstructuredMarkdownLoader(markdown_file_path)
            except Exception as e:
                # Falls back to PyPDFLoader
                loader = PyPDFLoader(file_path)
        else:
            # Use PyPDFLoader directly
            loader = PyPDFLoader(file_path)
    
    return loader.load()
```

**Problems:**
1. ❌ Single extraction method (PyPDFLoader)
2. ❌ No encoding validation
3. ❌ No mojibake detection/fix
4. ❌ No OCR fallback for scanned PDFs
5. ❌ No quality check on extracted text

---

## 3. Implementation Requirements

### 3.1 New Dependencies

Add to `requirements.txt`:

```txt
# PDF Extraction (Multi-pass)
PyMuPDF>=1.24.0          # Fast PDF text extraction
pdfminer.six>=20231228   # Better encoding handling

# OCR (for scanned PDFs)
pytesseract>=0.3.10      # Python wrapper for Tesseract
pdf2image>=1.16.3        # PDF to image conversion

# System packages (install via apt-get)
# tesseract-ocr
# tesseract-ocr-rus
# tesseract-ocr-eng
# poppler-utils
```

**Installation Commands:**
```bash
# Python packages
pip install PyMuPDF pdfminer.six pytesseract pdf2image

# System packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
sudo apt-get install -y poppler-utils
```

**Verification:**
```bash
# Check Tesseract installation
tesseract --version
# Expected: v5.x.x

# Check Russian language pack
tesseract --list-langs
# Expected output includes: rus, eng

# Check Python packages
python -c "import fitz; print(fitz.__version__)"
python -c "from pdfminer.high_level import extract_text; print('OK')"
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

### 3.2 Code Changes Required

#### 3.2.1 Modify `rag_component/document_loader.py`

**Changes:**
1. Add new imports
2. Add helper methods for extraction and validation
3. Replace `load_document()` PDF handling with multi-pass approach

**Complete New File Content:**

```python
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
            # NEW: Multi-pass PDF extraction with encoding fix
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
            List of LangChain Document objects with validated text
        """
        extraction_methods = [
            ("PyMuPDF", self._extract_with_pymupdf),
            ("pdfminer", self._extract_with_pdfminer),
            ("PyPDFLoader", self._extract_with_pypdf),
            ("Tesseract OCR", self._extract_with_tesseract),
        ]
        
        for method_name, extract_func in extraction_methods:
            try:
                logger.debug(f"Trying {method_name} for {file_path}")
                
                # Extract text
                text = extract_func(file_path)
                
                if not text or len(text.strip()) < 10:
                    logger.debug(f"{method_name}: No text extracted")
                    continue
                
                # Fix encoding issues (mojibake)
                text = self._fix_russian_encoding(text)
                
                # Validate extracted text
                if self._is_valid_cyrillic(text):
                    logger.info(f"Successfully extracted text from {file_path} using {method_name}")
                    return [LCDocument(
                        page_content=text,
                        metadata={
                            "source": file_path,
                            "extraction_method": method_name,
                            "file_type": "pdf"
                        }
                    )]
                else:
                    logger.debug(f"{method_name}: Extracted text failed validation")
                    
            except Exception as e:
                logger.warning(f"{method_name} failed for {file_path}: {str(e)}")
                continue
        
        # All methods failed
        error_msg = f"All PDF extraction methods failed for {file_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    def _extract_with_pymupdf(self, file_path: str) -> str:
        """
        Extract text using PyMuPDF (fitz).
        Fast and works well for most PDFs.
        
        Args:
            file_path: Path to PDF file
            
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
            for page_num in range(len(doc)):
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

    def _is_valid_cyrillic(self, text: str, min_cyrillic_ratio: float = 0.3) -> bool:
        """
        Validate that extracted text contains valid Cyrillic characters.
        
        Args:
            text: Text to validate
            min_cyrillic_ratio: Minimum ratio of Cyrillic characters (0.0-1.0)
            
        Returns:
            True if text appears to be valid Russian/Cyrillic
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
        is_valid = cyrillic_ratio >= min_cyrillic_ratio
        
        if not is_valid:
            logger.debug(f"Cyrillic ratio {cyrillic_ratio:.2f} below threshold {min_cyrillic_ratio}")
        
        return is_valid

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
```

#### 3.2.2 Update `requirements.txt`

**File:** `/root/qwen/ai_agent/requirements.txt`

**Add these lines:**
```txt
# PDF Extraction (Multi-pass)
PyMuPDF>=1.24.0
pdfminer.six>=20231228

# OCR for scanned PDFs
pytesseract>=0.3.10
pdf2image>=1.16.3
```

#### 3.2.3 Add System Dependencies Installation Script

**Create:** `/root/qwen/ai_agent/install_ocr_dependencies.sh`

```bash
#!/bin/bash
# Install system dependencies for OCR and PDF processing

set -e  # Exit on error

echo "Installing OCR and PDF processing dependencies..."

# Update package list
sudo apt-get update

# Install Tesseract OCR with Russian language support
echo "Installing Tesseract OCR..."
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y tesseract-ocr-rus
sudo apt-get install -y tesseract-ocr-eng

# Install poppler-utils for PDF to image conversion
echo "Installing poppler-utils..."
sudo apt-get install -y poppler-utils

# Verify installation
echo "Verifying installation..."
tesseract --version
tesseract --list-langs | grep -E "rus|eng" || echo "Warning: Language packs may not be installed correctly"

echo "✓ OCR dependencies installed successfully!"
```

**Make executable:**
```bash
chmod +x /root/qwen/ai_agent/install_ocr_dependencies.sh
```

---

## 4. Configuration Changes

### 4.1 Environment Variables (Optional)

Add to `.env` file if you want to configure OCR behavior:

```bash
# PDF Extraction Configuration
RAG_PDF_EXTRACTION_METHOD=auto  # auto, pymupdf, pdfminer, pypdf, tesseract
RAG_OCR_ENABLED=true            # Enable Tesseract OCR fallback
RAG_OCR_LANGUAGE=rus+eng        # OCR language packs
RAG_MIN_CYRILLIC_RATIO=0.3      # Minimum Cyrillic character ratio
```

### 4.2 No Breaking Changes

**Important:** This implementation is **backward compatible**:
- Existing code continues to work without changes
- All 8 callers of `DocumentLoader.load_document()` automatically benefit
- No API changes
- No database schema changes

---

## 5. Testing Requirements

### 5.1 Test Cases

Create test file: `rag_component/test_pdf_extraction.py`

```python
"""
Test suite for multi-pass PDF extraction
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

    def test_normal_russian_pdf(self):
        """Test extraction of properly encoded Russian PDF"""
        pdf_path = os.path.join(self.test_dir, "gost-r-50922-2006-normal.pdf")
        docs = self.loader.load_document(pdf_path)
        
        assert len(docs) > 0
        assert "Федеральное" in docs[0].page_content  # Should have proper Cyrillic
        assert docs[0].metadata["extraction_method"] in ["PyMuPDF", "pdfminer"]

    def test_mojibake_pdf(self):
        """Test extraction and fix of mojibake-encoded PDF"""
        pdf_path = os.path.join(self.test_dir, "gost-r-50922-2006-mojibake.pdf")
        docs = self.loader.load_document(pdf_path)
        
        assert len(docs) > 0
        assert "Федеральное" in docs[0].page_content  # Should be fixed
        assert "ÔÅÄ" not in docs[0].page_content  # Should NOT have mojibake

    def test_scanned_pdf_with_ocr(self):
        """Test OCR extraction of scanned PDF"""
        pdf_path = os.path.join(self.test_dir, "scanned-gost-1995.pdf")
        docs = self.loader.load_document(pdf_path)
        
        assert len(docs) > 0
        assert "ГОСТ" in docs[0].page_content or "GOST" in docs[0].page_content
        assert docs[0].metadata["extraction_method"] == "Tesseract OCR"

    def test_raw_bytes_pdf(self):
        """Test PDF that previously returned raw byte sequences"""
        pdf_path = os.path.join(self.test_dir, "raw-bytes-test.pdf")
        docs = self.loader.load_document(pdf_path)
        
        assert len(docs) > 0
        assert "/G80/G7c" not in docs[0].page_content  # Should NOT have raw bytes
        assert self.loader._is_valid_cyrillic(docs[0].page_content)

    def test_english_pdf(self):
        """Test extraction of English PDF (should still work)"""
        pdf_path = os.path.join(self.test_dir, "english-document.pdf")
        docs = self.loader.load_document(pdf_path)
        
        assert len(docs) > 0
        assert len(docs[0].page_content) > 100

    def test_invalid_pdf(self):
        """Test handling of corrupted/invalid PDF"""
        pdf_path = os.path.join(self.test_dir, "corrupted.pdf")
        
        with pytest.raises(ValueError, match="All PDF extraction methods failed"):
            self.loader.load_document(pdf_path)

    def test_encoding_fix_method(self):
        """Test mojibake detection and fix"""
        mojibake_text = "ÔÅÄÅÐÀËÜÍÎÅ ÀÃÅÍÒÑÒÂÎ"
        fixed = self.loader._fix_russian_encoding(mojibake_text)
        
        assert fixed == "Федеральное агентство"
        assert fixed != mojibake_text

    def test_cyrillic_validation(self):
        """Test Cyrillic text validation"""
        valid_russian = "Федеральное агентство по технической защите"
        invalid_text = "This is English text only"
        mojibake = "ÔÅÄÅÐÀËÜÍÎÅ"
        
        assert self.loader._is_valid_cyrillic(valid_russian) == True
        assert self.loader._is_valid_cyrillic(invalid_text) == False
        assert self.loader._is_valid_cyrillic(mojibake) == False  # Before fix

    def test_extraction_method_metadata(self):
        """Test that extraction method is recorded in metadata"""
        pdf_path = os.path.join(self.test_dir, "gost-r-50922-2006-normal.pdf")
        docs = self.loader.load_document(pdf_path)
        
        assert "extraction_method" in docs[0].metadata
        assert docs[0].metadata["extraction_method"] in [
            "PyMuPDF", "pdfminer", "PyPDFLoader", "Tesseract OCR"
        ]
```

### 5.2 Manual Testing Procedure

**Step 1: Prepare Test PDFs**

Download these test PDFs to `/root/qwen/ai_agent/test_data/pdfs/`:
1. `gost-r-50922-2006.pdf` - Normal Russian PDF (should work with PyMuPDF)
2. `scanned-gost-1995.pdf` - Scanned PDF (requires OCR)
3. Any PDF that previously showed mojibake

**Step 2: Run Tests**

```bash
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate

# Run unit tests
pytest rag_component/test_pdf_extraction.py -v

# Run manual test
python rag_component/test_pdf_extraction_manual.py
```

**Step 3: Verify Results**

Expected output for each test PDF:

| PDF Type | Expected Method | Expected Result |
|----------|----------------|-----------------|
| Normal Russian | PyMuPDF | Valid Cyrillic text |
| Mojibake | PyMuPDF + encoding fix | Fixed Cyrillic text |
| Scanned | Tesseract OCR | OCR-extracted text |
| English | PyMuPDF | Valid English text |

### 5.3 Integration Testing

**Test via Web UI:**

1. Go to Data Scientist tab
2. Upload a Russian PDF that previously showed mojibake
3. Select "Upload File" option
4. Wait for processing
5. Query the document
6. Verify response contains proper Russian text (not mojibake)

**Test via API:**

```bash
curl -X POST http://localhost:5003/api/rag/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/russian-gost.pdf" \
  -F "job_id=test_job_001"

# Then query
curl -X POST http://localhost:5003/api/rag/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Что такое защита информации?"}'
```

Expected: Response in proper Russian, not mojibake.

---

## 6. Performance Considerations

### 6.1 Expected Processing Times

| PDF Type | Pages | Method | Expected Time |
|----------|-------|--------|---------------|
| Digital Russian | 10 | PyMuPDF | 5 seconds |
| Digital Russian | 50 | PyMuPDF | 25 seconds |
| Scanned (OCR) | 10 | Tesseract | 30 seconds |
| Scanned (OCR) | 50 | Tesseract | 150 seconds |
| Complex encoding | 10 | pdfminer | 10 seconds |

### 6.2 Memory Usage

| Operation | Memory Usage |
|-----------|--------------|
| PyMuPDF extraction | ~50MB |
| pdfminer extraction | ~100MB |
| Tesseract OCR (per page) | ~200MB |

### 6.3 Optimization Tips

1. **Set page limits for OCR:**
   ```python
   # In _extract_with_tesseract, limit to first N pages for large PDFs
   max_ocr_pages = int(os.getenv("RAG_MAX_OCR_PAGES", "20"))
   images = convert_from_path(file_path, dpi=300, first_page=1, last_page=max_ocr_pages)
   ```

2. **Cache extraction results:**
   ```python
   # Store extracted text to avoid re-extraction
   cache_key = hashlib.md5(file_path.encode()).hexdigest()
   cached = redis.get(f"pdf_extract:{cache_key}")
   if cached:
       return cached.decode('utf-8')
   ```

3. **Use GPU for OCR (optional):**
   ```bash
   # Install GPU version of Tesseract
   sudo apt-get install -y tesseract-ocr-opencl
   ```

---

## 7. Rollback Plan

### 7.1 If Issues Occur

**Immediate Rollback:**

```bash
# 1. Revert document_loader.py
cd /root/qwen/ai_agent
git checkout HEAD -- rag_component/document_loader.py

# 2. Restart RAG service
pkill -f "python.*rag.*app"
source ai_agent_env/bin/activate
nohup python -m backend.services.rag.app > rag_service.log 2>&1 &

# 3. Verify service is working
curl http://localhost:5003/health
```

**Partial Rollback (disable OCR only):**

```bash
# Comment out Tesseract in extraction_methods list
# In _load_pdf_with_fallback(), remove:
# ("Tesseract OCR", self._extract_with_tesseract),
```

### 7.2 Monitoring

**Watch for these issues:**

| Issue | Symptom | Solution |
|-------|---------|----------|
| PyMuPDF not installed | `ImportError: No module named 'fitz'` | `pip install PyMuPDF` |
| Tesseract not installed | `TesseractNotFoundError` | Run `install_ocr_dependencies.sh` |
| Russian lang pack missing | `Error opening data file rus.traineddata` | `apt-get install tesseract-ocr-rus` |
| Memory exhaustion | OOM killer terminates process | Reduce `max_ocr_pages` |

---

## 8. Success Criteria

### 8.1 Functional Requirements

- [ ] All 4 text variants are properly handled
- [ ] Mojibake is detected and fixed automatically
- [ ] Scanned PDFs are processed via OCR
- [ ] Extraction method is recorded in metadata
- [ ] All 8 callers of `DocumentLoader` work without changes

### 8.2 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Russian PDF success rate | >95% | Test with 100 Russian PDFs |
| Mojibake fix rate | >99% | Test with known mojibake PDFs |
| OCR accuracy | >90% | Manual review of OCR output |
| Processing time (10 pages) | <30 seconds | Benchmark test |

### 8.3 Acceptance Testing

**Must pass all tests:**
1. ✅ Unit tests (`test_pdf_extraction.py`)
2. ✅ Integration test (upload → query → verify)
3. ✅ Manual test with real GOST PDFs
4. ✅ No regression in existing functionality

---

## 9. Deployment Checklist

### Pre-Deployment

- [ ] Install Python dependencies (`pip install -r requirements.txt`)
- [ ] Install system dependencies (`./install_ocr_dependencies.sh`)
- [ ] Verify Tesseract installation (`tesseract --version`)
- [ ] Verify Russian language pack (`tesseract --list-langs`)
- [ ] Run unit tests (`pytest rag_component/test_pdf_extraction.py`)
- [ ] Backup current `document_loader.py`

### Deployment

- [ ] Deploy new `document_loader.py`
- [ ] Restart RAG service
- [ ] Verify service health (`curl http://localhost:5003/health`)
- [ ] Test with sample Russian PDF

### Post-Deployment

- [ ] Monitor logs for extraction errors
- [ ] Verify no increase in processing time
- [ ] Check memory usage is within limits
- [ ] Test with production PDFs
- [ ] Document any issues encountered

---

## 10. Troubleshooting Guide

### Common Issues

#### Issue 1: "PyMuPDF not installed"

**Error:**
```
ImportError: No module named 'fitz'
```

**Solution:**
```bash
source ai_agent_env/bin/activate
pip install PyMuPDF
```

#### Issue 2: "Tesseract not found"

**Error:**
```
TesseractNotFoundError: tesseract is not installed or not in PATH
```

**Solution:**
```bash
sudo apt-get install tesseract-ocr
export TESSERACT_PATH=/usr/bin/tesseract
```

#### Issue 3: "Russian language pack missing"

**Error:**
```
Error opening data file rus.traineddata
```

**Solution:**
```bash
sudo apt-get install tesseract-ocr-rus
tesseract --list-langs  # Should show 'rus'
```

#### Issue 4: "OCR produces garbage text"

**Symptoms:**
- OCR output contains random characters
- Low Cyrillic ratio

**Solutions:**
1. Increase DPI: `convert_from_path(file_path, dpi=400)`
2. Try different PSM mode: `config='--psm 3'` (fully automatic)
3. Check PDF quality (may be too low resolution)

#### Issue 5: "Memory error during OCR"

**Error:**
```
MemoryError: Unable to allocate 500MB
```

**Solutions:**
1. Limit pages: `last_page=10` in `convert_from_path()`
2. Reduce DPI: `dpi=200` instead of `300`
3. Process pages sequentially instead of all at once

---

## 11. Contact and Support

### Implementation Team

- **Technical Lead:** [Name]
- **Developer:** [Name]
- **QA:** [Name]

### Resources

- **Tesseract Documentation:** https://tesseract-ocr.github.io/
- **PyMuPDF Documentation:** https://pymupdf.readthedocs.io/
- **pdfminer.six Documentation:** https://pdfminersix.readthedocs.io/

### Escalation Path

1. Check this document's Troubleshooting section
2. Review test logs in `rag_component/test_logs/`
3. Contact implementation team via [communication channel]
4. Create issue ticket with:
   - PDF sample (if possible)
   - Error message
   - Extraction method that failed
   - System configuration

---

## Appendix A: Complete File Changes Summary

| File | Action | Lines Changed | Description |
|------|--------|---------------|-------------|
| `rag_component/document_loader.py` | **REPLACE** | 120 → 280 | Multi-pass extraction |
| `requirements.txt` | **APPEND** | +4 lines | New dependencies |
| `install_ocr_dependencies.sh` | **CREATE** | 30 lines | System deps installer |
| `rag_component/test_pdf_extraction.py` | **CREATE** | 150 lines | Test suite |

---

## Appendix B: Sample Test PDFs

Download these for testing:

1. **Normal Russian PDF:**
   - URL: https://docs.cntd.ru/document/1200050995
   - Expected: PyMuPDF extraction, valid Cyrillic

2. **Scanned PDF (requires OCR):**
   - Search: "ГОСТ scanned PDF test"
   - Expected: Tesseract OCR, 90%+ accuracy

3. **Mojibake PDF:**
   - Use any PDF that previously showed `ÔÅÄÅÐÀËÜÍÎÅ`
   - Expected: Encoding fix applied, valid Cyrillic

---

**Document End**

---

**Approval Signatures:**

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Technical Lead | | | |
| Project Manager | | | |
| QA Lead | | | |

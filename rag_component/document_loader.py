"""
Document loader module for the RAG component.
Handles loading and preprocessing of various document types.
"""

import os
import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import time
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document as LCDocument
from .config import (
    RAG_SUPPORTED_FILE_TYPES,
    RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED,
    RAG_USE_FALLBACK_ON_CONVERSION_ERROR,
)

logger = logging.getLogger(__name__)


def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    if isinstance(value, bool):
        return value
    return value.lower() in ("true", "1", "yes", "y")


# Streaming toggle for hallucination detection
LLM_STREAMING_ENABLED = str_to_bool(os.getenv("LLM_STREAMING_ENABLED", "true"))
logger.info(f"LLM streaming enabled: {LLM_STREAMING_ENABLED}")


class DocumentLoader:
    """Class responsible for loading documents of various types."""

    def __init__(
        self, job_id: Optional[str] = None, job_queue=None, doc_id: Optional[str] = None
    ):
        self.supported_types = RAG_SUPPORTED_FILE_TYPES
        self.use_pdf_conversion = RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED
        self.job_id = job_id
        self.job_queue = job_queue
        self.doc_id = doc_id

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
            raise ValueError(
                f"Unsupported file type: {file_ext}. Supported types: {self.supported_types}"
            )

        if file_ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_ext == ".pdf":
            # Check if PDF-to-Markdown conversion is enabled
            if self.use_pdf_conversion:
                try:
                    # Import the PDF converter
                    from .pdf_converter import PDFToMarkdownConverter

                    # Initialize the converter
                    converter = PDFToMarkdownConverter()

                    # Convert PDF to Markdown file with a much longer timeout (e.g., 3600 seconds = 1 hour) to allow complex PDFs to process
                    markdown_file_path = converter.convert_pdf_to_markdown_file(
                        file_path, timeout_seconds=3600
                    )

                    if markdown_file_path:
                        # Use UnstructuredMarkdownLoader for the converted Markdown
                        try:
                            loader = UnstructuredMarkdownLoader(markdown_file_path)
                        except ImportError:
                            logger.warning(
                                "unstructured not available, using TextLoader for converted .md"
                            )
                            loader = TextLoader(markdown_file_path, encoding="utf-8")
                    else:
                        # If conversion failed, fall back to multi-pass PDF extraction
                        logger.warning(
                            f"PDF conversion failed for {file_path}, falling back to multi-pass extraction"
                        )
                        return self._load_pdf_with_fallback(file_path)
                except ImportError:
                    # If marker is not available, fall back to multi-pass PDF extraction
                    logger.warning(
                        "Marker library not available, using multi-pass PDF extraction"
                    )
                    return self._load_pdf_with_fallback(file_path)
                except Exception as e:
                    # If conversion fails, fall back to multi-pass PDF extraction
                    logger.warning(
                        f"PDF conversion error for {file_path}, falling back to multi-pass extraction: {str(e)}"
                    )
                    return self._load_pdf_with_fallback(file_path)
            else:
                # Use multi-pass PDF extraction directly if conversion is disabled
                return self._load_pdf_with_fallback(file_path)
        elif file_ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif file_ext == ".html":
            loader = UnstructuredHTMLLoader(file_path)
        elif file_ext == ".md":
            # Try UnstructuredMarkdownLoader first, fall back to TextLoader
            try:
                loader = UnstructuredMarkdownLoader(file_path)
            except ImportError:
                logger.warning(
                    "unstructured not available, using TextLoader for .md files"
                )
                loader = TextLoader(file_path, encoding="utf-8")
        else:
            # Default to text loader for any other supported type
            loader = TextLoader(file_path, encoding="utf-8")

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
                encoding_was_fixed = text != text_before_fix

                # Validate extracted text
                if self._is_valid_text(text):
                    total_time = time.time() - start_time
                    logger.info(
                        f"Successfully extracted text from {file_path} using {method_name} in {total_time:.2f}s"
                    )

                    return [
                        LCDocument(
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
                                    "fallback_chain_position": extraction_methods.index(
                                        (method_name, extract_func)
                                    )
                                    + 1,
                                    "total_methods_tried": extraction_methods.index(
                                        (method_name, extract_func)
                                    )
                                    + 1,
                                },
                            },
                        )
                    ]
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

    def _extract_with_pymupdf(
        self, file_path: str, pages: Optional[range] = None
    ) -> str:
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

        return "\n".join(text_parts)

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
            raise ImportError(
                "pdfminer.six not installed. Run: pip install pdfminer.six"
            )

        # Extract text with laparams for better layout analysis
        from pdfminer.layout import LAParams

        laparams = LAParams(detect_vertical=True, all_texts=True, line_margin=0.5)

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
        return "\n".join([page.page_content for page in pages])

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
            raise ImportError(
                "OCR dependencies not installed. Run: pip install pytesseract pdf2image"
            )

        # Convert PDF pages to images (300 DPI for good OCR quality)
        images = convert_from_path(file_path, dpi=300)

        text_parts = []
        for image in images:
            # OCR with Russian + English language support
            text = pytesseract.image_to_string(
                image,
                lang="rus+eng",  # Russian + English
                config="--psm 6",  # Assume uniform block of text
            )
            text_parts.append(text)

        return "\n".join(text_parts)

    def _extract_with_llm(
        self,
        file_path: str,
        pages: Optional[range] = None,
        timeout_seconds: Optional[int] = None,
        job_id: Optional[str] = None,
        completed_pages: Optional[set] = None,
    ) -> str:
        """
        Send PDF to LLM for markdown conversion.
        Converts PDF pages to images, then sends to vision-capable LLM.
        Supports page-level resume by skipping already-completed pages.

        Args:
            file_path: Path to PDF file
            pages: Optional range of pages to extract (0-indexed). None means all pages.
            timeout_seconds: Optional timeout in seconds (default: from LLM_CHUNKING_TIMEOUT env var)
            job_id: Optional job ID for page-level resume support
            completed_pages: Optional set of 0-indexed page numbers already completed

        Returns:
            Clean markdown text from LLM (no code blocks or explanations)
        """
        import base64
        import io
        import re
        import time
        import shutil

        # Use PDF-specific LLM config, fall back to NLP LLM config
        llm_base_url = os.getenv(
            "PDF_LLM_BASE_URL",
            os.getenv("NLP_LLM_BASE_URL", "http://localhost:1234/v1"),
        )
        llm_model = os.getenv(
            "PDF_LLM_MODEL", os.getenv("NLP_LLM_MODEL", "qwen3.5-35b")
        )
        api_key = os.getenv(
            "PDF_LLM_API_KEY",
            os.getenv("NLP_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "not-needed")),
        )

        # Get timeout from parameter or environment variable (default: 43200 seconds = 12 hours)
        timeout = (
            timeout_seconds
            if timeout_seconds
            else int(os.getenv("LLM_CHUNKING_TIMEOUT", "43200"))
        )

        logger.info(
            f"Sending PDF to LLM: url={llm_base_url}, model={llm_model}, timeout={timeout}s"
        )
        logger.debug(
            f"LLM client init: base_url={llm_base_url}, api_key={'***' if api_key else None}"
        )

        # Setup temp directory for page-level resume (if job_id provided)
        temp_dir = None
        if job_id:
            temp_dir = os.path.join("/tmp/rag_page_resume", job_id)
            os.makedirs(temp_dir, exist_ok=True)
            logger.info(f"Page-level resume enabled: temp_dir={temp_dir}")

        # Convert PDF pages to images
        try:
            from pdf2image import convert_from_path

            # Determine which pages to convert
            if pages is not None:
                page_nums = list(pages)
                # Convert to 1-indexed for pdf2image (first_page, last_page)
                first_page = min(page_nums) + 1
                last_page = max(page_nums) + 1
                logger.info(f"Converting pages {first_page}-{last_page} to images")
                images = convert_from_path(
                    file_path, dpi=200, first_page=first_page, last_page=last_page
                )
            else:
                logger.info("Converting all pages to images")
                images = convert_from_path(
                    file_path, dpi=200
                )  # 200 DPI for faster processing

            logger.info(f"Converted PDF to {len(images)} images")
            logger.debug(f"Image DPI: 200, format: PNG")
        except ImportError:
            logger.error(
                "pdf2image not installed. Run: apt-get install poppler-utils && pip install pdf2image"
            )
            raise ImportError(
                "pdf2image required for PDF extraction. Install poppler-utils and pdf2image"
            )

        # System prompt instructs LLM to output ONLY markdown
        system_prompt = """You are a PDF to Markdown converter. Output ONLY the markdown content. Do not include explanations, code blocks around the output, or any text outside the markdown content.

IMPORTANT: Some PDF pages may contain watermarks (e.g., "DRAFT", "CONFIDENTIAL", "SAMPLE", or similar overlay text). These watermarks are NOT part of the actual document content and MUST be IGNORED. Do not extract or include any watermark text in your markdown output. Only extract the genuine document content."""

        user_prompt = "Convert this PDF page to clean markdown. Preserve all mathematical formulas and equations in LaTeX format. IMPORTANT: Ignore and do not extract any watermarks (such as DRAFT, CONFIDENTIAL, SAMPLE, or similar overlay text). Output ONLY the markdown content, nothing else."

        # Log prompts
        logger.info(f"LLM extraction prompt (system): {system_prompt[:200]}...")
        logger.info(f"LLM extraction prompt (user): {user_prompt[:200]}...")
        logger.debug(f"LLM extraction prompt (system, full): {system_prompt}")
        logger.debug(f"LLM extraction prompt (user, full): {user_prompt}")

        from openai import OpenAI

        client = OpenAI(base_url=llm_base_url, api_key=api_key)

        # Time entire LLM extraction
        llm_total_start = time.time()

        # Process all pages and combine into single document
        all_markdown_parts = []
        start_page = min(list(pages)) + 1 if pages else 1
        total_pages = len(images)
        pages_processed = 0
        pages_skipped = 0

        for page_idx, img in enumerate(images):
            page_num = start_page + page_idx
            page_idx_0based = page_num - 1  # 0-indexed for completed_pages set

            # Check if this page was already completed (page-level resume)
            if completed_pages and page_idx_0based in completed_pages:
                # Load from temp file
                page_file = (
                    os.path.join(temp_dir, f"page_{page_idx_0based:04d}.md")
                    if temp_dir
                    else None
                )
                if page_file and os.path.exists(page_file):
                    with open(page_file, "r", encoding="utf-8") as f:
                        page_markdown = f.read()
                    all_markdown_parts.append(
                        f"<!-- Page {page_num} -->\n\n{page_markdown}"
                    )
                    pages_skipped += 1
                    logger.info(
                        f"Page {page_num}: Skipped (already completed, loaded from temp)"
                    )
                    continue
                else:
                    logger.warning(
                        f"Page {page_num}: Marked as completed but temp file not found, re-processing"
                    )

            logger.info(f"Processing page {page_num}")

            # Convert image to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

            # Send to LLM with configurable timeout
            llm_start = time.time()
            logger.info(
                f"Page {page_num}: Sending image to LLM (base64 size: {len(img_base64)} bytes)"
            )
            logger.debug(
                f"Page {page_num}: LLM request: model={llm_model}, max_tokens=32000, timeout={timeout}s"
            )

            # Use streaming with hallucination detection if enabled
            if LLM_STREAMING_ENABLED:
                response = client.chat.completions.create(
                    model=llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    },
                                },
                            ],
                        },
                    ],
                    max_tokens=32000,
                    stream=True,  # Enable streaming
                )
                page_markdown = self._stream_llm_response_with_detection(
                    response,
                    page_num,
                    job_id,
                    self.doc_id,
                    self.job_queue,
                    temp_dir,
                    page_idx_0based,
                )
            else:
                response = client.chat.completions.create(
                    model=llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    },
                                },
                            ],
                        },
                    ],
                    max_tokens=32000,
                    timeout=timeout,  # Use configurable timeout
                )
                page_markdown = response.choices[0].message.content

            llm_time = time.time() - llm_start
            logger.info(f"Page {page_num}: LLM call {llm_time:.2f}s")

            page_markdown = response.choices[0].message.content

            # Log response metadata
            logger.info(f"Page {page_num}: LLM response: {len(page_markdown)} chars")
            if hasattr(response, "usage"):
                logger.debug(
                    f"Page {page_num}: LLM response usage: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, total={response.usage.total_tokens}"
                )
            logger.debug(
                f"Page {page_num}: LLM response finish_reason: {response.choices[0].finish_reason}"
            )
            logger.debug(
                f"Page {page_num}: LLM response (first 500 chars): {page_markdown[:500]}..."
            )

            # Clean up LLM response - remove markdown code block wrappers
            clean_start = time.time()
            page_markdown = self._clean_llm_markdown(page_markdown)
            clean_time = time.time() - clean_start
            logger.debug(f"Page {page_num}: Markdown cleanup {clean_time:.2f}s")

            # Save page to temp file immediately (for page-level resume)
            if temp_dir:
                page_file = os.path.join(temp_dir, f"page_{page_idx_0based:04d}.md")
                with open(page_file, "w", encoding="utf-8") as f:
                    f.write(page_markdown)
                logger.debug(f"Page {page_num}: Saved to temp file {page_file}")

            # Add page marker as comment (doesn't render in markdown)
            all_markdown_parts.append(f"<!-- Page {page_num} -->\n\n{page_markdown}")
            logger.info(f"Page {page_num}: LLM returned {len(page_markdown)} chars")
            pages_processed += 1

            # Update heartbeat after each page (for long-running jobs, prevents false "stuck" detection)
            if self.job_id and self.job_queue and self.doc_id:
                try:
                    current_job = self.job_queue.get_job(self.job_id)
                    if current_job:
                        progress_pct = (
                            int((page_num / total_pages) * 100) if total_pages else 0
                        )
                        # Track completed pages in job parameters
                        if "completed_pages" not in current_job.parameters:
                            current_job.parameters["completed_pages"] = []
                        if (
                            page_idx_0based
                            not in current_job.parameters["completed_pages"]
                        ):
                            current_job.parameters["completed_pages"].append(
                                page_idx_0based
                            )

                        current_job.parameters["heartbeat"] = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "phase": "extract",
                            "doc_id": self.doc_id,
                            "action": "page_processed",
                            "page_num": page_num,
                            "total_pages": total_pages,
                            "chars_extracted": len(page_markdown),
                            "progress_percent": progress_pct,
                            "pages_completed": len(
                                current_job.parameters["completed_pages"]
                            ),
                            "pages_remaining": total_pages
                            - len(current_job.parameters["completed_pages"]),
                        }
                        self.job_queue.update_job(current_job)
                        logger.info(
                            f"Page {page_num}: Heartbeat updated ({progress_pct}% complete, {pages_skipped} skipped, {pages_processed} processed)"
                        )
                except Exception as e:
                    # Log error but don't fail page processing
                    logger.error(f"Page {page_num}: Failed to update heartbeat: {e}")

        # Combine all pages into single markdown document
        full_markdown = "\n\n".join(all_markdown_parts)
        llm_total_time = time.time() - llm_total_start
        logger.info(
            f"LLM extraction complete: {len(full_markdown)} total chars in {llm_total_time:.2f}s ({len(full_markdown) / llm_total_time:.0f} chars/sec)"
        )
        logger.info(
            f"LLM extraction summary: {pages_processed} pages processed, {pages_skipped} pages skipped (resumed)"
        )

        # Cleanup temp directory after successful completion
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")

        return full_markdown

    def _clean_llm_markdown(self, markdown: str) -> str:
        """
        Clean LLM markdown output - remove code block wrappers and explanations.

        Args:
            markdown: Raw markdown from LLM

        Returns:
            Clean markdown content only
        """
        if not markdown:
            return ""

        # Remove outer markdown code block wrappers (```markdown ... ```)
        # This is the most common case - LLM wraps entire output
        match = re.search(r"^```(?:markdown)?\s*\n(.*?)\n```$", markdown, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Remove markdown code block wrappers (``` ... ```)
        # But preserve code blocks WITHIN the content
        lines = markdown.split("\n")
        cleaned_lines = []
        in_wrapper = False
        wrapper_start_found = False

        for line in lines:
            stripped = line.strip()

            # Detect wrapper start (```markdown or ``` at very beginning)
            if not wrapper_start_found and (
                stripped.startswith("```markdown") or stripped == "```"
            ):
                in_wrapper = True
                wrapper_start_found = True
                continue

            # Detect wrapper end
            if in_wrapper and stripped == "```" and len(cleaned_lines) > 0:
                in_wrapper = False
                continue

            # Skip common LLM explanation patterns
            if any(
                pattern in stripped.lower()
                for pattern in [
                    "here is the markdown",
                    "here's the markdown",
                    "converted to markdown",
                    "markdown output",
                    "output:",
                    "result:",
                ]
            ):
                continue

            cleaned_lines.append(line)

        result = "\n".join(cleaned_lines)

        # If still wrapped, try regex removal again
        if result.startswith("```"):
            match = re.search(r"^```(?:markdown)?\s*\n(.*?)\n```$", result, re.DOTALL)
            if match:
                result = match.group(1)

        return result.strip()

    def _detect_hallucination_pattern(self, text: str) -> Tuple[bool, str]:
        """
        Detect common hallucination patterns in LLM output.

        Args:
            text: Text to analyze for hallucination patterns

        Returns:
            Tuple of (is_hallucinated, reason)
        """
        # Pattern 1: Excessive zeros (>30% of content)
        zero_count = text.count("0")
        if zero_count > len(text) * 0.3:
            return True, "Excessive zeros (>30% of content)"

        # Pattern 2: Repeating characters (10+ consecutive)
        if re.search(r"(.)\1{10,}", text):
            return True, "Repeating characters detected (10+ consecutive)"

        # Pattern 3: Repeating words (5+ consecutive)
        words = text.split()
        for i in range(len(words) - 5):
            if words[i : i + 5] == [words[i]] * 5:
                return True, "Repeating words detected (5+ consecutive)"

        # Pattern 4: Unbalanced braces (too many unclosed)
        open_count = text.count("{")
        close_count = text.count("}")
        if open_count > close_count + 5:
            return True, "Unbalanced JSON braces"

        return False, ""

    def _stream_llm_response_with_detection(
        self,
        response,
        page_num: int,
        job_id: str,
        doc_id: str,
        job_queue,
        temp_dir: str = None,
        page_idx_0based: int = 0,
        max_attempts: int = 3,
    ) -> str:
        """
        Stream LLM response with hallucination detection.

        Args:
            response: OpenAI response object (streaming)
            page_num: Current page number
            job_id: Job ID for heartbeat updates
            doc_id: Document ID
            job_queue: Job queue for updating status
            temp_dir: Temporary directory for page-level resume
            page_idx_0based: 0-indexed page number
            max_attempts: Maximum retry attempts (default: 3)

        Returns:
            Clean markdown text from LLM

        Raises:
            ValueError: If hallucination detected after max attempts
        """
        buffer = ""
        consecutive_zeros = 0
        check_interval = 100
        tokens_since_check = 0
        last_error = None

        for attempt in range(max_attempts):
            try:
                # Clear buffer for new attempt
                if attempt > 0:
                    buffer = ""
                    consecutive_zeros = 0
                    tokens_since_check = 0
                    logger.info(
                        f"[Phased Job {job_id}] Page {page_num}: Retrying (attempt {attempt + 1}/{max_attempts})"
                    )

                for chunk in response:
                    if not chunk.choices or not chunk.choices[0].delta.content:
                        continue

                    content = chunk.choices[0].delta.content
                    buffer += content
                    tokens_since_check += len(content.split())

                    # Periodic hallucination detection
                    if tokens_since_check >= check_interval:
                        hallucination_detected, reason = (
                            self._detect_hallucination_pattern(buffer)
                        )
                        if hallucination_detected:
                            raise ValueError(
                                f"Hallucination detected on page {page_num}: {reason}"
                            )
                        tokens_since_check = 0

                    # Track consecutive zeros (common hallucination)
                    if re.match(r"^0+$", content.strip()):
                        consecutive_zeros += 1
                        if consecutive_zeros > 15:
                            raise ValueError(
                                f"Excessive consecutive zeros on page {page_num}"
                            )
                    else:
                        consecutive_zeros = 0

                # Success - break retry loop
                break

            except Exception as e:
                last_error = e
                logger.error(
                    f"[Phased Job {job_id}] Page {page_num}: Attempt {attempt + 1} failed: {e}"
                )

                if attempt < max_attempts - 1:
                    # Update heartbeat with retry info
                    if job_id and job_queue:
                        try:
                            current_job = job_queue.get_job(job_id)
                            if current_job:
                                current_job.parameters["heartbeat"] = {
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "phase": "extract",
                                    "doc_id": doc_id,
                                    "action": "llm_retry",
                                    "attempt": attempt + 2,
                                    "error": str(e),
                                }
                                job_queue.update_job(current_job)
                        except Exception as hb_error:
                            logger.warning(
                                f"[Phased Job {job_id}] Failed to update heartbeat: {hb_error}"
                            )

                    # Brief pause before retry
                    time.sleep(2)
                else:
                    logger.error(
                        f"[Phased Job {job_id}] Page {page_num}: Failed after {max_attempts} attempts: {last_error}"
                    )
                    raise

        # Clean up LLM response - remove markdown code block wrappers
        page_markdown = self._clean_llm_markdown(buffer)

        # Save page to temp file immediately (for page-level resume)
        if temp_dir:
            try:
                page_file = os.path.join(temp_dir, f"page_{page_idx_0based:04d}.md")
                with open(page_file, "w", encoding="utf-8") as f:
                    f.write(page_markdown)
                logger.debug(
                    f"[Phased Job {job_id}] Page {page_num}: Saved to temp file {page_file}"
                )
            except Exception as save_error:
                logger.warning(
                    f"[Phased Job {job_id}] Page {page_num}: Failed to save temp file: {save_error}"
                )

        return page_markdown

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
            "ÔÅÄ",  # Федер
            "ÐÅÃ",  # Рег
            "ÒÅÕ",  # Тех
            "ÇÀÙ",  # Защ
            "ÈÍÔ",  # Инф
            "ïî",  # по (common word)
            "íà",  # на (common word)
        ]

        # Check if text looks like mojibake
        is_mojibake = any(pattern in text for pattern in mojibake_indicators)

        if is_mojibake:
            try:
                # Re-encode as Latin-1, decode as CP1251 (Russian Windows)
                fixed = text.encode("latin-1").decode("cp1251")
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
        cyrillic_pattern = re.compile(r"[\u0400-\u04FF]")
        cyrillic_matches = cyrillic_pattern.findall(text)
        cyrillic_count = len(cyrillic_matches)

        # Calculate ratio
        total_chars = len(text.replace(" ", "").replace("\n", ""))
        if total_chars == 0:
            return False

        cyrillic_ratio = cyrillic_count / total_chars

        # For Russian documents, expect at least 30% Cyrillic
        # For English documents, check for sufficient alphabetic content
        is_valid_cyrillic = cyrillic_ratio >= min_cyrillic_ratio

        # Also check for English text (if little Cyrillic, check for English letters)
        if not is_valid_cyrillic:
            # Check if it's valid English text
            english_pattern = re.compile(r"[a-zA-Z]")
            english_matches = english_pattern.findall(text)
            english_ratio = len(english_matches) / total_chars if total_chars > 0 else 0
            is_valid_english = english_ratio >= 0.5  # At least 50% English letters

            if is_valid_english:
                logger.debug("Text validated as English")
                return True
            else:
                logger.debug(
                    f"Cyrillic ratio {cyrillic_ratio:.2f} below threshold {min_cyrillic_ratio}"
                )
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

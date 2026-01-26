"""
Document loader module for the RAG component.
Handles loading and preprocessing of various document types.
"""
import os
import logging
from typing import List, Optional
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
                        # If conversion failed, fall back to PyPDFLoader if enabled
                        if RAG_USE_FALLBACK_ON_CONVERSION_ERROR:
                            logger.warning(f"PDF conversion failed for {file_path}, falling back to PyPDFLoader")
                            loader = PyPDFLoader(file_path)
                        else:
                            raise ValueError(f"Failed to convert PDF to Markdown: {file_path}")
                except ImportError:
                    # If marker is not available, fall back to PyPDFLoader
                    loader = PyPDFLoader(file_path)
                except Exception as e:
                    # If conversion fails, fall back to PyPDFLoader if enabled
                    if RAG_USE_FALLBACK_ON_CONVERSION_ERROR:
                        logger.warning(f"PDF conversion error for {file_path}, falling back to PyPDFLoader: {str(e)}")
                        loader = PyPDFLoader(file_path)
                    else:
                        raise e
            else:
                # Use PyPDFLoader directly if conversion is disabled
                loader = PyPDFLoader(file_path)
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
                        print(f"Error loading document {file_path}: {str(e)}")
        
        return documents
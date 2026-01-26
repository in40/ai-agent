"""
PDF to Markdown converter module for the RAG component.
Handles conversion of PDF files to Markdown format for improved text extraction.
"""
import os
from pathlib import Path
from typing import Optional
import logging
import uuid
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

logger = logging.getLogger(__name__)

try:
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    from marker.converters.pdf import PdfConverter
    from marker.renderers.markdown import MarkdownRenderer
    MARKER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Marker library not available. PDF to Markdown conversion will not work. Error: {e}")
    MARKER_AVAILABLE = False

from .config import RAG_MARKDOWN_STORAGE_DIR


class PDFToMarkdownConverter:
    """Class responsible for converting PDF files to Markdown format."""

    def __init__(self):
        if not MARKER_AVAILABLE:
            raise ImportError(
                "Marker library is not installed. "
                "Please install it using: pip install marker-pdf"
            )

        # Create the markdown storage directory if it doesn't exist
        os.makedirs(RAG_MARKDOWN_STORAGE_DIR, exist_ok=True)

    def _perform_conversion(self, pdf_path: str) -> Optional[str]:
        """
        Internal method to perform the actual PDF conversion.

        Args:
            pdf_path: Path to the PDF file to convert

        Returns:
            Markdown text content, or None if conversion fails
        """
        try:
            # Create the model dictionary (this loads the ML models)
            model_dict = create_model_dict()

            # Create a config parser with options for external LLM if configured
            config_options = {"output_format": "markdown"}

            # Check if external LLM is configured for Marker specifically
            # NOTE: We bypass the global FORCE_DEFAULT_MODEL_FOR_ALL setting for Marker
            llm_provider = os.getenv("MARKER_LLM_PROVIDER", "").lower()

            if llm_provider:
                # Enable LLM usage
                config_options["use_llm"] = True

                if llm_provider == "openai":
                    # Configure for OpenAI-compatible API
                    config_options["llm_service"] = "marker.services.openai.OpenAIService"
                    config_options["openai_base_url"] = os.getenv("OPENAI_BASE_URL", "http://asus-tus:1234/v1")  # Default to LM Studio
                    config_options["openai_model"] = os.getenv("OPENAI_MODEL", "gemini-2.5-flash")  # Default model name
                    config_options["openai_api_key"] = os.getenv("OPENAI_API_KEY", "lm-studio")  # Default API key for LM Studio
                    logger.info(f"Configuring Marker to use OpenAI-compatible API at {config_options['openai_base_url']} with model {config_options['openai_model']}")
                elif llm_provider == "ollama":
                    # Configure for Ollama
                    config_options["llm_service"] = "marker.services.ollama.OllamaService"
                    config_options["ollama_base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                    config_options["ollama_model"] = os.getenv("OLLAMA_MODEL", "llama3.2-vision")
                    logger.info(f"Configuring Marker to use Ollama at {config_options['ollama_base_url']} with model {config_options['ollama_model']}")
                elif llm_provider == "gemini":
                    # Configure for Google Gemini
                    config_options["llm_service"] = "marker.services.gemini.GoogleGeminiService"
                    config_options["gemini_api_key"] = os.getenv("GEMINI_API_KEY", "")
                    logger.info("Configuring Marker to use Google Gemini API")
                elif llm_provider == "claude":
                    # Configure for Anthropic Claude
                    config_options["llm_service"] = "marker.services.claude.ClaudeService"
                    config_options["claude_api_key"] = os.getenv("CLAUDE_API_KEY", "")
                    logger.info("Configuring Marker to use Anthropic Claude API")
                elif llm_provider == "azure":
                    # Configure for Azure OpenAI
                    config_options["llm_service"] = "marker.services.azure_openai.AzureOpenAIService"
                    config_options["openai_base_url"] = os.getenv("AZURE_OPENAI_ENDPOINT", "")
                    config_options["openai_model"] = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
                    config_options["openai_api_key"] = os.getenv("AZURE_OPENAI_API_KEY", "")
                    logger.info(f"Configuring Marker to use Azure OpenAI at {config_options['openai_base_url']} with deployment {config_options['openai_model']}")

            config_parser = ConfigParser(config_options)

            # Generate the config dictionary
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

            # Extract markdown content from the result
            # The result is typically a RenderedFormat object with a markdown attribute
            if hasattr(result, 'markdown'):
                markdown_content = result.markdown
            elif isinstance(result, str):
                markdown_content = result
            else:
                # If it's a different format, try to extract the content
                markdown_content = str(result)

            if markdown_content and len(markdown_content.strip()) > 0:
                logger.info(f"Successfully converted PDF to Markdown: {pdf_path}")
                return markdown_content
            else:
                logger.warning(f"Conversion returned empty content for: {pdf_path}")
                return None

        except Exception as e:
            logger.error(f"Error converting PDF to Markdown ({pdf_path}): {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def convert_pdf_to_markdown(self, pdf_path: str, timeout_seconds: int = 120) -> Optional[str]:
        """
        Convert a PDF file to Markdown format with timeout protection.

        Args:
            pdf_path: Path to the PDF file to convert
            timeout_seconds: Maximum time to spend on conversion (default 120 seconds)

        Returns:
            Markdown text content, or None if conversion fails or times out
        """
        try:
            # Use ThreadPoolExecutor with timeout to prevent long-running conversions
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._perform_conversion, pdf_path)
                result = future.result(timeout=timeout_seconds)
                return result

        except FuturesTimeoutError:
            logger.error(f"PDF conversion timed out after {timeout_seconds} seconds for: {pdf_path}")
            return None
        except Exception as e:
            logger.error(f"Error during PDF conversion with timeout ({pdf_path}): {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def convert_pdf_to_markdown_file(self, pdf_path: str, timeout_seconds: int = 120) -> Optional[str]:
        """
        Convert a PDF file to Markdown and save to a permanent file.

        Args:
            pdf_path: Path to the PDF file to convert
            timeout_seconds: Maximum time to spend on conversion (default 120 seconds)

        Returns:
            Path to the permanent Markdown file, or None if conversion fails
        """
        markdown_content = self.convert_pdf_to_markdown(pdf_path, timeout_seconds)

        if not markdown_content:
            return None

        try:
            # Create a unique subdirectory to avoid filename collisions
            subdir = str(uuid.uuid4())
            markdown_storage_dir = os.path.join(RAG_MARKDOWN_STORAGE_DIR, subdir)
            os.makedirs(markdown_storage_dir, exist_ok=True)

            # Create a filename based on the original PDF name
            original_filename = Path(pdf_path).stem
            markdown_file_path = os.path.join(markdown_storage_dir, f"{original_filename}.md")

            # Write the Markdown content to the file
            with open(markdown_file_path, 'w', encoding='utf-8') as md_file:
                md_file.write(markdown_content)

            logger.info(f"Created permanent Markdown file: {markdown_file_path}")
            return markdown_file_path

        except Exception as e:
            logger.error(f"Error creating permanent Markdown file: {str(e)}")
            return None
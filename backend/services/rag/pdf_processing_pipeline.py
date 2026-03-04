"""
PDF Processing Pipeline for Document Store Import

This module contains utilities for processing PDF documents for the GraphRAG system.
It is a work-in-progress and has not been tested in production. The code may be 
incomplete or non-functional as it was extracted from a larger project without 
the corresponding dependencies.

The original implementation was part of a larger RAG stack that included:
- Document loading from various sources
- LLM-based chunking using external APIs
- Vector database ingestion with Qdrant

For production use, the missing components (DocumentLoader, VectorStoreManager, etc.) 
need to be implemented or replaced with available alternatives.
"""
import os
import re
import json
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# RAG Components - add these to make PDF processing work with Document Store
try:
    from rag_component.document_loader import DocumentLoader
except ImportError:
    logger.warning("DocumentLoader not available")
    
try:
    from rag_component.vector_store_manager import VectorStoreManager
except ImportError:
    logger.warning("VectorStoreManager not available")

# For LLM-based chunking
# Use settings from .env - NO HARDCODING
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL

from models.response_generator import ResponseGenerator

# Import logging for config
import sys
sys.path.insert(0, '/root/qwen/ai_agent')
try:
    from config.settings import str_to_bool
    # Use RAG settings if available
    try:
        from rag_component.config import RAG_EMBEDDING_PROVIDER, RAG_EMBEDDING_MODEL
        EMBEDDING_PROVIDER = RAG_EMBEDDING_PROVIDER
        EMBEDDING_MODEL = RAG_EMBEDDING_MODEL
    except ImportError:
        pass
except ImportError:
    pass


logger = logging.getLogger(__name__)

# Import required components (from RAG component)


# Default smart chunking prompt optimized for technical standards
DEFAULT_SMART_CHUNKING_PROMPT = """# ROLE
You are an expert document engineer specializing in semantic chunking of technical standards (GOST, ISO, IEC, RFC, etc.) for vector database ingestion. Your task is to split the provided document into search-optimized chunks while preserving semantic integrity.

## CORE PRINCIPLES
1. PRESERVE SEMANTIC UNITS: Never split complete concepts (formulas with context, tables, procedural steps, definitions)
2. TARGET SIZE: 200-450 tokens per chunk (prioritize semantic integrity over exact size)
3. MINIMAL OVERLAP: Apply overlap ONLY at procedural boundaries where step N output becomes step N+1 input (max 50 tokens). Zero overlap elsewhere.
4. CONTEXT ANCHORING: Always include section headers/subheaders at chunk start
5. FORMULA PRESERVATION: Keep all formulas WITH their explanatory context and variable definitions
6. TABLE INTEGRITY: Never split tables - keep entire table + caption in single chunk

## CHUNKING RULES (Priority Order)

### MUST PRESERVE TOGETHER
- Formulas + surrounding explanatory text (min. 2 sentences before/after)
- Complete tables (header + all rows + footnote)
- Algorithmic/procedural sequences (e.g., "Step 1 -> Step 2 -> Step 3")
- Definition + scope sentences (term + "-" explanation)
- Example + its numerical result/calculation
- Cross-referenced clauses (e.g., "as specified in 5.2.4" -> include 5.2.4 context if critical)

### OVERLAP ONLY AT THESE BOUNDARIES
Apply 30-50 token overlap ONLY when:
- Procedural step output directly feeds next step input
- Observation -> formula transition
- Generation forecasting -> numerical example

DO NOT overlap:
- Discrete trust levels/scenarios
- Structural requirement categories
- Appendices (keep self-contained)
- Reference sections

### NEVER SPLIT
- Mathematical expressions across lines
- "where:" variable definitions from their formula
- Critical constraint ranges
- Multi-sentence definitions
- Complete attack scenarios/methodologies

## METADATA REQUIREMENTS
For each chunk, generate structured metadata:
{
  "chunk_id": integer,
  "section": "X.Y.Z or appendix_X",
  "title": "Descriptive title in language of document",
  "chunk_type": "one of: header_and_scope | references_and_definitions | reference_table | trust_level | structural_requirements | testing_procedure | formula_with_context | security_procedure | appendix_example",
  "contains_formula": boolean,
  "contains_table": boolean,
  "formula_id": "1,2,3... or null",
  "formula_reference": "referenced formula number or null",
  "trust_level": "full | partial_zero | null",
  "testing_scenario": "small_db | medium_db | low_trust | null",
  "overlap_source": "chunk_X_end or null",
  "overlap_tokens": integer,
  "token_count": integer,
  "content": "chunk text with overlaps PREPENDED (not appended to previous chunk)"
}

## OUTPUT FORMAT
Return ONLY valid JSON matching this schema:
{
  "document": "extracted document identifier (e.g., GOST_R_XXXXX-YYYY)",
  "total_chunks": integer,
  "overlap_strategy": "targeted_procedural_only",
  "chunks": [ /* array of chunk objects per metadata requirements */ ],
  "embedding_recommendations": {
    "model": "text-embedding-3-large or equivalent multilingual",
    "chunk_size_target": "200-450 tokens",
    "overlap_strategy": "Apply overlaps ONLY at procedural boundaries to preserve algorithmic continuity",
    "metadata_indexing": "Index section, chunk_type, contains_formula fields for hybrid search"
  }
}

## SPECIAL HANDLING FOR RUSSIAN TECHNICAL STANDARDS
- Preserve "yolochki" quotes - critical semantic markers
- Keep GOST R XXXXX references intact with year
- Maintain mathematical notation: sigma(h), min(h), rho(h), E(.), sigma(.)
- Preserve footnote markers and "Primechaniye - " sections with parent content

## PROCESSING INSTRUCTIONS
1. First pass: Identify natural semantic boundaries (section breaks, formula clusters, procedural sequences)
2. Second pass: Apply overlap rules ONLY where procedural continuity requires it
3. Third pass: Generate metadata based on content analysis (detect formulas, tables, trust levels)
4. Final validation: Ensure no formula/table split; verify overlap only at 2-3 procedural boundaries max

## CRITICAL CONSTRAINT
If document contains morphing/generation procedures, apply overlap between generation steps to preserve causal chain. For all other boundaries: ZERO overlap.

---
TEXT TO CHUNK PROVIDED"""


class PDFProcessingPipeline:
    """
    Pipeline for processing PDF documents from Document Store.
    Handles extraction, chunking, and vector database ingestion.
    """

    def __init__(self, llm=None, vector_store_manager=None):
        """
        Initialize the PDF processing pipeline.

        Args:
            llm: LLM instance for chunking (optional, will create if not provided)
            vector_store_manager: VectorStoreManager instance (optional, will create if not provided)
        """
        self.llm = llm
        self.vector_store_manager = vector_store_manager

        # Initialize LLM if not provided
        if self.llm is None:
            try:
                response_generator = ResponseGenerator()
                self.llm = response_generator._get_llm_instance(
                    provider=RESPONSE_LLM_PROVIDER,
                    model=RESPONSE_LLM_MODEL
                )
                logger.info(f"Initialized LLM: provider={RESPONSE_LLM_PROVIDER}, model={RESPONSE_LLM_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise

        # Initialize vector store manager if not provided
        if self.vector_store_manager is None:
            try:
                self.vector_store_manager = VectorStoreManager()
                logger.info("Initialized VectorStoreManager")
            except Exception as e:
                logger.error(f"Failed to initialize VectorStoreManager: {e}")
                raise

        self.document_loader = DocumentLoader()

    def extract_text_from_pdf(self, pdf_content: bytes, filename: str = "document.pdf") -> Tuple[bool, str, Optional[str]]:
        """
        Extract text from PDF binary content.

        Args:
            pdf_content: Raw PDF binary content
            filename: Filename for the PDF (used for temp file)

        Returns:
            Tuple of (success, text_content, error_message)
        """
        temp_file_path = None
        try:
            # Ensure filename has .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename = filename + '.pdf'
            
            # Sanitize filename to remove any problematic characters
            import re
            safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
            if not safe_filename.lower().endswith('.pdf'):
                safe_filename = safe_filename + '.pdf'
            
            # Create temporary file to store PDF
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, safe_filename)

            logger.info(f"Creating temp file: {temp_file_path}")

            # Write PDF content to temp file
            with open(temp_file_path, 'wb') as f:
                f.write(pdf_content)

            logger.info(f"PDF written to temp file: {temp_file_path} ({len(pdf_content)} bytes)")

            # Verify file exists and has content
            if not os.path.exists(temp_file_path):
                return False, "", f"Temp file was not created: {temp_file_path}"
            
            file_size = os.path.getsize(temp_file_path)
            logger.info(f"Temp file size: {file_size} bytes")

            # Load document using DocumentLoader (handles PDF via PyPDF or Marker)
            docs = self.document_loader.load_document(temp_file_path)

            if not docs:
                return False, "", "Document loader returned empty result"

            # Extract text from all pages
            text_content = "\n".join([doc.page_content for doc in docs])

            if not text_content.strip():
                return False, "", "Extracted text is empty"

            logger.info(f"Successfully extracted {len(text_content)} characters from PDF")

            # Cleanup temp file
            try:
                os.unlink(temp_file_path)
                os.rmdir(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up temp file: {cleanup_error}")

            return True, text_content, None

        except Exception as e:
            logger.error(f"PDF text extraction failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

            # Cleanup on error
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            return False, "", f"PDF extraction error: {str(e)}"

    def chunk_text_with_llm(self, text: str, prompt: str, filename: str = "document") -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Chunk text using LLM with the provided prompt.

        Args:
            text: Text content to chunk
            prompt: Chunking prompt to use
            filename: Source filename for metadata

        Returns:
            Tuple of (success, chunks_list, error_message)
        """
        try:
            # Check text length and split if too large for LLM context
            max_text_length = 100000  # ~20K tokens to be safe

            if len(text) > max_text_length:
                logger.warning(f"Text too large ({len(text)} chars), splitting into segments")
                # Split text into manageable segments
                segments = self._split_text_into_segments(text, max_text_length)
                all_chunks = []

                for i, segment in enumerate(segments):
                    logger.info(f"Processing segment {i+1}/{len(segments)}")
                    success, segment_chunks, error = self._chunk_segment(segment, prompt, filename, i)
                    if success:
                        all_chunks.extend(segment_chunks)
                    else:
                        logger.error(f"Failed to chunk segment {i+1}: {error}")

                if not all_chunks:
                    return False, [], "Failed to chunk any segment"

                return True, all_chunks, None

            # Process as single segment
            return self._chunk_segment(text, prompt, filename, 0)

        except Exception as e:
            logger.error(f"LLM chunking failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, [], f"Chunking error: {str(e)}"

    def _split_text_into_segments(self, text: str, max_length: int) -> List[str]:
        """Split large text into overlapping segments at natural boundaries."""
        segments = []
        start = 0

        while start < len(text):
            end = min(start + max_length, len(text))

            # Try to find a natural break point (section header, paragraph break)
            if end < len(text):
                # Look for section breaks or newlines
                break_patterns = [r'\n\n(?=[A-Z])', r'\n\n', r'\n#', r'\n##', r'\n###']
                for pattern in break_patterns:
                    matches = list(re.finditer(pattern, text[start:end]))
                    if matches:
                        # Use the last match before the cutoff
                        last_match = matches[-1]
                        end = start + last_match.start()
                        break

            segment = text[start:end].strip()
            if segment:
                segments.append(segment)

            start = end
            # Add small overlap between segments
            if start < len(text):
                start = max(0, start - 500)

        return segments

    def _chunk_segment(self, text: str, prompt: str, filename: str, segment_index: int) -> Tuple[bool, List[Dict], Optional[str]]:
        """Chunk a single text segment using LLM."""
        try:
            # Build the full prompt
            full_prompt = f"{prompt}\n\n---\nTEXT TO CHUNK:\n{text}"

            logger.info(f"Calling LLM for chunking (segment {segment_index + 1})...")
            response = self.llm.invoke(full_prompt)

            # Extract response content
            response_content = response.content if hasattr(response, 'content') else str(response)

            logger.info(f"LLM response received ({len(response_content)} chars)")

            # Parse JSON from response
            try:
                json_match = re.search(r'\{[\s\S]*\}', response_content)
                json_str = json_match.group(0) if json_match else response_content
                chunking_result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Response content: {response_content[:500]}...")
                return False, [], f"Failed to parse LLM response: {str(e)}"

            # Extract chunks from result
            chunks = chunking_result.get('chunks', [])

            if not chunks:
                logger.warning("LLM returned no chunks")
                return False, [], "LLM returned empty chunks array"

            logger.info(f"Successfully chunked segment {segment_index + 1}: {len(chunks)} chunks")

            # Add metadata to each chunk
            document_id = chunking_result.get('document', filename)
            for i, chunk in enumerate(chunks):
                chunk['source_document'] = document_id
                chunk['filename'] = filename
                chunk['segment_index'] = segment_index

            return True, chunks, None

        except Exception as e:
            logger.error(f"Segment chunking failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, [], f"Segment chunking error: {str(e)}"

    def ingest_chunks_to_vector_db(self, chunks: List[Dict], metadata: Dict[str, Any]) -> Tuple[bool, int, Optional[str]]:
        """
        Ingest chunks into vector database.

        Args:
            chunks: List of chunk dictionaries from LLM
            metadata: Additional metadata to include (job_id, doc_id, etc.)

        Returns:
            Tuple of (success, chunks_ingested_count, error_message)
        """
        try:
            from langchain_core.documents import Document

            if not chunks:
                return False, 0, "No chunks to ingest"

            # Convert chunks to LangChain documents
            lc_documents = []
            for chunk_data in chunks:
                # Extract content
                content = chunk_data.get('content', '')

                if not content.strip():
                    logger.warning("Skipping empty chunk")
                    continue

                # Build metadata
                doc_metadata = {
                    'source': chunk_data.get('source_document', metadata.get('filename', 'unknown')),
                    'filename': metadata.get('filename', 'unknown'),
                    'job_id': metadata.get('job_id', ''),
                    'doc_id': metadata.get('doc_id', ''),
                    'chunk_id': chunk_data.get('chunk_id', ''),
                    'section': chunk_data.get('section', ''),
                    'title': chunk_data.get('title', ''),
                    'chunk_type': chunk_data.get('chunk_type', ''),
                    'token_count': chunk_data.get('token_count', 0),
                    'contains_formula': chunk_data.get('contains_formula', False),
                    'contains_table': chunk_data.get('contains_table', False),
                    'upload_method': 'Document Store Import',
                    'ingested_at': metadata.get('ingested_at', ''),
                }

                # Add optional metadata fields
                for key in ['formula_id', 'formula_reference', 'trust_level', 'testing_scenario',
                           'overlap_source', 'overlap_tokens', 'segment_index']:
                    if key in chunk_data:
                        doc_metadata[key] = chunk_data[key]

                # Create LangChain document
                lc_doc = Document(page_content=content, metadata=doc_metadata)
                lc_documents.append(lc_doc)

            if not lc_documents:
                return False, 0, "No valid chunks to ingest after filtering"

            # Add documents to vector store
            logger.info(f"Ingesting {len(lc_documents)} chunks to vector store...")
            self.vector_store_manager.add_documents(lc_documents)

            logger.info(f"Successfully ingested {len(lc_documents)} chunks to vector store")
            return True, len(lc_documents), None

        except Exception as e:
            logger.error(f"Vector DB ingestion failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False, 0, f"Vector DB ingestion error: {str(e)}"

    def process_document(self, pdf_content: bytes, filename: str, prompt: str,
                         metadata: Dict[str, Any], ingest_to_vector: bool = True) -> Dict[str, Any]:
        """
        Process a complete PDF document through the full pipeline.

        Args:
            pdf_content: Raw PDF binary content
            filename: Document filename
            prompt: Chunking prompt to use
            metadata: Document metadata (job_id, doc_id, etc.)
            ingest_to_vector: Whether to ingest chunks to vector DB

        Returns:
            Processing result dictionary
        """
        result = {
            'success': False,
            'filename': filename,
            'text_extracted': False,
            'text_length': 0,
            'chunks_generated': 0,
            'chunks_ingested': 0,
            'errors': []
        }

        # Step 1: Extract text from PDF
        logger.info(f"Step 1: Extracting text from PDF: {filename}")
        success, text_content, error = self.extract_text_from_pdf(pdf_content, filename)

        if not success:
            result['errors'].append(f"Text extraction failed: {error}")
            return result

        result['text_extracted'] = True
        result['text_length'] = len(text_content)
        logger.info(f"Extracted {len(text_content)} characters from {filename}")

        # Step 2: Chunk text with LLM
        logger.info(f"Step 2: Chunking text with LLM: {filename}")
        use_prompt = prompt if prompt else DEFAULT_SMART_CHUNKING_PROMPT
        success, chunks, error = self.chunk_text_with_llm(text_content, use_prompt, filename)

        if not success:
            result['errors'].append(f"Chunking failed: {error}")
            return result

        result['chunks_generated'] = len(chunks)
        logger.info(f"Generated {len(chunks)} chunks from {filename}")

        # Step 3: Ingest to vector database
        if ingest_to_vector:
            logger.info(f"Step 3: Ingesting chunks to vector DB: {filename}")
            success, ingested_count, error = self.ingest_chunks_to_vector_db(chunks, metadata)

            if not success:
                result['errors'].append(f"Vector DB ingestion failed: {error}")
                # Still return partial success if chunking worked
                result['success'] = True
                result['chunks_ingested'] = 0
                return result

            result['chunks_ingested'] = ingested_count
            logger.info(f"Ingested {ingested_count} chunks from {filename}")

        result['success'] = True
        return result


def process_document_from_store(pdf_content: bytes, filename: str, prompt: str,
                                 job_id: str, doc_id: str, ingest_to_vector: bool = True) -> Dict[str, Any]:
    """
    Convenience function to process a document from Document Store.

    Args:
        pdf_content: Raw PDF binary content
        filename: Document filename
        prompt: Chunking prompt
        job_id: Job ID for tracking
        doc_id: Document ID
        ingest_to_vector: Whether to ingest to vector DB

    Returns:
        Processing result dictionary
    """
    from datetime import datetime

    metadata = {
        'job_id': job_id,
        'doc_id': doc_id,
        'filename': filename,
        'ingested_at': datetime.utcnow().isoformat()
    }

    pipeline = PDFProcessingPipeline()
    return pipeline.process_document(pdf_content, filename, prompt, metadata, ingest_to_vector)

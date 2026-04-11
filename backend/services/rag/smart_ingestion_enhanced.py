"""
Smart Ingestion Service - Enhanced with Web Page Processing
Handles LLM-based document chunking for RAG ingestion with support for:
1. Direct file uploads
2. Web page URL processing (extract links → download → chunk → ingest)
"""
import os
import re
import json
import tempfile
import shutil
import threading
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Tuple, Optional
import requests
from bs4 import BeautifulSoup

# Import RAG components
import sys
from pathlib import Path

# Get project root for config imports
# For files in backend/services/rag/, we need to go up 3 levels to get to project root
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rag_component.main import RAGOrchestrator
from models.response_generator import ResponseGenerator

# Import from project root config.settings
try:
    import config.settings as settings
    RESPONSE_LLM_PROVIDER = settings.RESPONSE_LLM_PROVIDER
    RESPONSE_LLM_MODEL = settings.RESPONSE_LLM_MODEL
    LLM_CHUNKING_TIMEOUT = settings.LLM_CHUNKING_TIMEOUT
    str_to_bool = settings.str_to_bool
except (ImportError, ModuleNotFoundError):
    import importlib.util
    spec = importlib.util.spec_from_file_location("settings", project_root / "config" / "settings.py")
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    RESPONSE_LLM_PROVIDER = settings.RESPONSE_LLM_PROVIDER
    RESPONSE_LLM_MODEL = settings.RESPONSE_LLM_MODEL
    LLM_CHUNKING_TIMEOUT = settings.LLM_CHUNKING_TIMEOUT
    str_to_bool = settings.str_to_bool

# Import job queue for background processing
from .job_queue import job_queue, JobStatus, SmartIngestionJob

# Import security components
from backend.security import require_permission, validate_input, Permission

# Threshold for background processing
BACKGROUND_PROCESSING_THRESHOLD = int(os.getenv('SMART_INGESTION_BACKGROUND_THRESHOLD', 50))

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parallelism configuration
PARALLELISM = int(os.getenv('PARALLELISM', os.getenv('PARRALELISM', '4')))  # Support both spellings
DOWNLOAD_PARALLELISM = int(os.getenv('DOWNLOAD_PARALLELISM', PARALLELISM))
CHUNKING_PARALLELISM = int(os.getenv('CHUNKING_PARALLELISM', PARALLELISM))
INGESTION_PARALLELISM = int(os.getenv('INGESTION_PARALLELISM', PARALLELISM))

logger.info(f"Smart Ingestion configured with PARALLELISM={PARALLELISM}")
logger.info(f"  - DOWNLOAD_PARALLELISM={DOWNLOAD_PARALLELISM}")
logger.info(f"  - CHUNKING_PARALLELISM={CHUNKING_PARALLELISM}")
logger.info(f"  - INGESTION_PARALLELISM={INGESTION_PARALLELISM}")

# Default smart chunking prompt - COMPREHENSIVE EXPERT PROMPT
DEFAULT_SMART_CHUNKING_PROMPT = """# ROLE
You are an expert document engineer specializing in semantic chunking of technical standards (GOST, ISO, IEC, RFC, etc.) for vector database ingestion. Your task is to split the provided document into search-optimized chunks while preserving semantic integrity.

## CORE PRINCIPLES
1. PRESERVE SEMANTIC UNITS: Never split complete concepts (formulas with context, tables, procedural steps, definitions)
2. TARGET SIZE: 200-450 tokens per chunk (prioritize semantic integrity over exact size)
3. MINIMAL OVERLAP: Apply overlap ONLY at procedural boundaries where step N output becomes step N+1 input (max 50 tokens). Zero overlap elsewhere.
4. CONTEXT ANCHORING: Always include section headers/subheaders at chunk start
5. FORMULA PRESERVATION: Keep all formulas WITH their explanatory context and variable definitions
6. TABLE INTEGRITY: Never split tables – keep entire table + caption in single chunk

## CHUNKING RULES (Priority Order)

### ✅ MUST PRESERVE TOGETHER
- Formulas + surrounding explanatory text (min. 2 sentences before/after)
- Complete tables (header + all rows + footnote)
- Algorithmic/procedural sequences (e.g., "Step 1 → Step 2 → Step 3")
- Definition + scope sentences (term + "— " explanation)
- Example + its numerical result/calculation
- Cross-referenced clauses (e.g., "as specified in 5.2.4" → include 5.2.4 context if critical)

### ⚠️ OVERLAP ONLY AT THESE BOUNDARIES
Apply 30-50 token overlap ONLY when:
- Procedural step output directly feeds next step input (e.g., "morphing produces X" → "X is used in selection")
- Observation → formula transition ("min(h) ≤ 3σ" → "evaluate using formula (2)")
- Generation forecasting → numerical example ("exponential decrease" → "Appendix A example")

DO NOT overlap:
- Discrete trust levels/scenarios
- Structural requirement categories
- Appendices (keep self-contained)
- Reference sections (normative references, notations)

### 🚫 NEVER SPLIT
- Mathematical expressions across lines
- "where:" variable definitions from their formula
- Critical constraint ranges (e.g., "n - √n < h < n + √n")
- Multi-sentence definitions
- Complete attack scenarios/methodologies

### 🚫 NEVER SKIP (must include ALL content)
- Multi-line formulas, especially those split across lines with \backslash or \\ continuation markers
- Cryptographic key values (hex strings like $K_{{MAC}} = ...$, $S^{{C}}_{{MAC}} = ...$)
- Session keys, master keys, initialization vectors
- Any content inside $...$ or $$...$$ delimiters
- Appendix examples and test vectors (they contain critical reference data)

## METADATA REQUIREMENTS - CRITICAL FIELD DEFINITIONS

For each chunk, you MUST generate ALL of the following fields. **NO field can be omitted.**

### REQUIRED FIELDS (every chunk MUST have all of these):

{{
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
  "content": "ACTUAL TEXT FROM THE DOCUMENT - THIS FIELD IS MANDATORY"
}}

### ⚠️ CRITICAL: THE "content" FIELD ⚠️

**The "content" field is THE MOST IMPORTANT field. Without it, the chunk is USELESS.**

**Rules for "content" field:**

1. **MUST contain actual text from the document** - Copy the exact text from the input document
2. **CANNOT be empty or null** - Every chunk must have content
3. **CANNOT be a description** - Do NOT write "this chunk contains..." - just include the actual text
4. **Must be 200-450 tokens** - Each chunk should have substantial content
5. **Preserve formatting** - Keep headers, formulas, tables as they appear in the document
6. **Include section headers** - Start each chunk with relevant section/subsection headers

**Example of CORRECT content field:**
```json
{{
  "chunk_id": 1,
  "section": "1",
  "title": "Область применения",
  "content": "# 1 Область применения\\\\n\\\\nНастоящие рекомендации определяют криптографические алгоритмы... (actual document text follows)"
}}
```

**Example of WRONG content field (DO NOT DO THIS):**
```json
{{
  "chunk_id": 1,
  "section": "1", 
  "title": "Область применения",
  "content": "This section describes the scope of the standard..."  ← WRONG! This is a description, not actual content!
}}
```

**BEFORE SUBMITTING YOUR JSON, VERIFY:**
- □ Every chunk has a "content" field
- □ Every "content" field contains actual document text (not descriptions)
- □ Every "content" field is at least 200 tokens
- □ The content is copied from the input document, not generated/summarized

## OUTPUT FORMAT
Return ONLY valid JSON matching this schema:
{{
  "document": "extracted document identifier (e.g., GOST_R_XXXXX-YYYY)",
  "total_chunks": integer,
  "overlap_strategy": "targeted_procedural_only",
  "chunks": [ /* array of chunk objects per metadata requirements */ ],
  "embedding_recommendations": {{
    "model": "text-embedding-3-large or equivalent multilingual",
    "chunk_size_target": "200-450 tokens",
    "overlap_strategy": "Apply overlaps ONLY at procedural boundaries to preserve algorithmic continuity",
    "metadata_indexing": "Index section, chunk_type, contains_formula fields for hybrid search"
  }}
}}

## SPECIAL HANDLING FOR RUSSIAN TECHNICAL STANDARDS
- Preserve «ёлочки» quotes («Свой», «Чужой») – critical semantic markers
- Keep ГОСТ Р XXXXX references intact with year
- Maintain mathematical notation: σ(h), min(h), ρ(h), E(.), σ(.)
- Preserve footnote markers and "Примечание — " sections with parent content

## PROCESSING INSTRUCTIONS
1. First pass: Identify natural semantic boundaries (section breaks, formula clusters, procedural sequences)
2. Second pass: Apply overlap rules ONLY where procedural continuity requires it
3. Third pass: Generate metadata based on content analysis (detect formulas, tables, trust levels)
4. Final validation: Ensure no formula/table split; verify overlap only at 2-3 procedural boundaries max

## CRITICAL CONSTRAINT
If document contains morphing/generation procedures (e.g., "поколение потомков"), apply overlap between generation steps to preserve causal chain. For all other boundaries: ZERO overlap.

## COVERAGE REQUIREMENTS (CRITICAL - READ CAREFULLY)
1. You MUST process the ENTIRE document text provided in the TEXT TO CHUNK section
2. Every paragraph, section, sentence, and piece of content must appear in at least one chunk
3. Do NOT stop early - continue chunking until ALL content from the input is covered
4. The "total_chunks" field must reflect ALL chunks needed for the COMPLETE document
5. If the document is long, create MORE chunks (10, 20, 30+) - do not limit yourself
6. Typical technical standards require 15-50 chunks depending on length
7. Complete coverage is MORE IMPORTANT than having few chunks

## VALIDATION CHECKLIST (BEFORE RESPONDING)
Before finalizing your JSON response, you MUST verify:
□ Every section of the input text is included in at least one chunk
□ No paragraphs, sections, or content are skipped
□ The "total_chunks" count exactly matches the number of chunks in the "chunks" array
□ All content from the input appears in the chunks (mentally compare input vs output)
□ You have NOT stopped after only processing the first few paragraphs

## WARNING ABOUT COMMON MISTAKES
DO NOT make these errors:
✗ Processing only the title page and foreword, then stopping
✗ Ignoring content after the first few sections
✗ Creating only 2-5 chunks for a long document
✗ Counting "total_chunks" as a small number when more content remains

INSTEAD:
✓ Read through the ENTIRE input text from start to finish
✓ Create a chunk for EACH semantic section you find
✓ Continue until you reach the END of the input text
✓ Set "total_chunks" to the actual count of all chunks created

## TEXT TO CHUNK
{input_text}

## YOUR JSON RESPONSE (Remember: Process ENTIRE document, create ALL needed chunks)

**FINAL REMINDER BEFORE YOU RESPOND:**

⚠️ **THE "content" FIELD IS MANDATORY FOR EVERY CHUNK** ⚠️

If you submit JSON without the "content" field in any chunk:
- The chunking will FAIL
- The document will be marked as failed
- All your work will be wasted

**For each chunk in the "chunks" array, you MUST include:**
1. All metadata fields (chunk_id, section, title, etc.)
2. **THE "content" FIELD WITH ACTUAL DOCUMENT TEXT**

**DO NOT** submit JSON like this (WRONG):
```json
{{"chunk_id": 1, "section": "1", "title": "Scope"}}  ← MISSING content field!
```

**DO** submit JSON like this (CORRECT):
```json
{{"chunk_id": 1, "section": "1", "title": "Scope", "content": "# 1 Scope\\\\n\\\\nThis standard defines..."}}
```

**Your response must be valid JSON.**
"""

# Prompts storage directory
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'smart_ingestion_prompts')

def ensure_prompts_dir():
    """Ensure the prompts directory exists"""
    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR)


def secure_filename(filename: str) -> str:
    """
    Secure a filename by removing potentially dangerous characters and sequences.
    Preserves Unicode characters like Cyrillic letters.
    """
    if filename is None:
        return ''

    filename = filename.replace('\\', '/')
    filename = os.path.basename(filename)
    filename = filename.lstrip('. ')
    filename = re.sub(r'[^\w\-.]', '_', filename, flags=re.UNICODE)

    if not filename:
        filename = "unnamed_file"

    if filename.startswith('.'):
        filename = f"unnamed{filename}"

    return filename


def extract_document_links_from_page(page_url: str, html_content: str) -> List[str]:
    """
    Extract document links from HTML content.
    Looks for links to PDF, DOCX, TXT, HTML, MD files and file-service patterns.
    
    Args:
        page_url: Base URL for resolving relative links
        html_content: HTML content of the page
        
    Returns:
        List of absolute URLs to documents
    """
    supported_extensions = {'.pdf', '.docx', '.txt', '.html', '.md', '.htm'}
    document_urls = set()
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            
            # Resolve relative URLs
            absolute_url = urljoin(page_url, href)
            
            # Check if it's a document link
            parsed = urlparse(absolute_url)
            path_lower = parsed.path.lower()
            
            # Check extension
            for ext in supported_extensions:
                if path_lower.endswith(ext):
                    document_urls.add(absolute_url)
                    break
            
            # Also check for file-service patterns (common in government/corporate portals)
            if 'file-service' in path_lower or '/file/load/' in path_lower:
                document_urls.add(absolute_url)
            
            # Also check for common document patterns
            if any(pattern in path_lower for pattern in ['/doc/', '/docs/', '/document', '/paper/', '/std/', '/gost/', '/iso/']):
                if any(ext in path_lower for ext in supported_extensions):
                    document_urls.add(absolute_url)
        
        logger.info(f"Extracted {len(document_urls)} document links from {page_url}")
        return list(document_urls)
        
    except Exception as e:
        logger.error(f"Error extracting links from {page_url}: {str(e)}")
        return []


def download_document_via_mcp(url: str) -> Tuple[bool, str, str]:
    """
    Download a document using the Download MCP server.
    
    Args:
        url: URL to download
        
    Returns:
        Tuple of (success, temp_file_path or error_message, filename)
    """
    # Handle file:// URLs directly (local files)
    if url.startswith('file://'):
        import shutil
        local_path = url[7:]  # Remove 'file://' prefix
        if os.path.exists(local_path) and local_path.endswith('.pdf'):
            # Copy to temp file for processing
            import tempfile
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(temp_fd)
            shutil.copy2(local_path, temp_path)
            filename = os.path.basename(local_path)
            logger.info(f"Loaded local file: {local_path}")
            return True, temp_path, filename
        else:
            logger.warning(f"Local file not found or not PDF: {local_path}")
            return False, f"File not found: {local_path}", ""
    
    try:
        from registry.registry_client import ServiceRegistryClient
        from models.dedicated_mcp_model import DedicatedMCPModel
        
        # Get registry URL
        registry_url = os.getenv('MCP_REGISTRY_URL', 'http://127.0.0.1:8080')
        
        # Connect to registry
        registry_client = ServiceRegistryClient(registry_url)
        
        # Discover download services (try both service type names)
        download_services = registry_client.discover_services(service_type="download")
        
        # If not found, try alternative service type name
        if not download_services:
            download_services = registry_client.discover_services(service_type="mcp_download")
        
        if not download_services:
            logger.error("No download MCP services found in registry")
            return False, "No download MCP services available", ""
        
        # Use first available download service
        download_service = download_services[0]
        
        # Create MCP model instance
        mcp_model = DedicatedMCPModel()
        
        # Call download service
        download_params = {"url": url}
        
        download_result = mcp_model._call_mcp_service(
            {
                'id': download_service.id,
                'host': download_service.host,
                'port': download_service.port,
                'type': download_service.type,
                'metadata': download_service.metadata
            },
            "download",
            download_params
        )
        
        if download_result.get('status') == 'success':
            # Extract downloaded content - check multiple possible response structures
            result_data = download_result.get('result', {})
            
            # Check if the download itself was successful
            if result_data.get('success') == False:
                error_msg = result_data.get('error', 'Download failed')
                # Extract just the main error reason
                if 'Network error' in error_msg:
                    error_msg = error_msg.split(':')[0]  # Get "Network error" part
                elif 'Name or service not known' in error_msg:
                    error_msg = 'DNS resolution failed - hostname not reachable'
                elif 'Connection refused' in error_msg:
                    error_msg = 'Connection refused by server'
                elif 'timeout' in error_msg.lower():
                    error_msg = 'Download timeout - server too slow'
                return False, error_msg, ""
            
            # Download MCP server returns file_path, not content
            file_path = result_data.get('result', {}).get('file_path', '')
            if not file_path:
                file_path = result_data.get('file_path', '')
            
            if file_path and os.path.exists(file_path):
                # File was downloaded successfully
                filename = os.path.basename(file_path)
                return True, file_path, filename
            else:
                # Fallback: try to get content directly
                content = result_data.get('result', {}).get('content', '')
                if not content:
                    content = result_data.get('content', '')
                if not content:
                    content = result_data.get('data', '')
                
                if content:
                    # Save to temp file
                    temp_dir = tempfile.mkdtemp()
                    # Extract filename from URL
                    parsed_url = urlparse(url)
                    filename = os.path.basename(parsed_url.path) or 'downloaded_document.txt'
                    filename = secure_filename(filename)
                    temp_path = os.path.join(temp_dir, filename)

                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    return True, temp_path, filename
                else:
                    return False, "No content downloaded", ""
        else:
            error_msg = download_result.get('error', 'Unknown download error')
            return False, error_msg, ""
            
    except Exception as e:
        logger.error(f"Download error for {url}: {str(e)}")
        return False, str(e), ""


def _validate_chunking_coverage(document_content: str, chunks: List[Dict]) -> Tuple[bool, str]:
    """
    Validate that LLM chunking adequately covered the input document.
    
    This function performs two critical checks:
    1. Content coverage ratio - ensures chunks cover sufficient % of input
    2. Minimum chunk count - ensures document wasn't under-chunked
    
    Args:
        document_content: Original document text that was sent to LLM
        chunks: List of chunk dictionaries, each with a 'content' field
    
    Returns:
        Tuple of (is_valid, message)
        - is_valid: False means hard failure, True means success (may have warning)
        - message: Empty string if no issues, error message if invalid, or warning if suboptimal
    
    Validation thresholds:
        - < 50% coverage: HARD FAILURE (reject)
        - 50-70% coverage: WARNING (accept but notify)
        - < expected chunk count: WARNING (accept but notify)
    """
    if not chunks:
        return False, "No chunks generated by LLM"
    
    # Calculate total chunked content length
    total_chunked_length = sum(len(c.get('content', '')) for c in chunks)
    input_length = len(document_content)
    
    if input_length == 0:
        return False, "Empty document content"
    
    # Calculate coverage ratio
    coverage_ratio = total_chunked_length / input_length
    
    # === Minimum chunk count validation ===
    # Estimate expected chunks based on document size
    # Average chunk target: 200-450 tokens ≈ 800-1800 characters
    # Use conservative estimate: 1000 chars per chunk
    estimated_chunks_needed = max(1, input_length // 1000)
    min_expected_chunks = max(3, estimated_chunks_needed)  # At least 3 chunks
    
    chunk_count_warning = ""
    if len(chunks) < min_expected_chunks:
        chunk_count_warning = (
            f"Suspiciously few chunks: {len(chunks)} generated vs "
            f"~{min_expected_chunks} expected for {input_length}-char document. "
            f"Expected ~1 chunk per 1000 characters."
        )
        logger.warning(f"Chunk count validation WARNING: {chunk_count_warning}")
    # === END CHUNK COUNT VALIDATION ===
    
    # Log coverage for monitoring
    logger.info(
        f"Chunking coverage validation: "
        f"input={input_length} chars, "
        f"chunked={total_chunked_length} chars, "
        f"coverage={coverage_ratio:.1%}, "
        f"chunks={len(chunks)} (expected ~{min_expected_chunks})"
    )
    
    # Critical threshold: Less than 50% coverage is a hard failure
    if coverage_ratio < 0.50:
        error_msg = (
            f"Insufficient content coverage: {coverage_ratio:.1%} "
            f"({total_chunked_length}/{input_length} chars in {len(chunks)} chunks). "
            f"Expected >50%. LLM may have stopped prematurely or document is too large."
        )
        logger.error(f"Coverage validation FAILED: {error_msg}")
        return False, error_msg
    
    # Warning threshold: Less than 70% coverage OR insufficient chunk count
    warnings = []
    if coverage_ratio < 0.70:
        warnings.append(
            f"Low content coverage: {coverage_ratio:.1%} "
            f"({total_chunked_length}/{input_length} chars). "
            f"Expected >70%. Some content may be missing."
        )
    
    if chunk_count_warning:
        warnings.append(chunk_count_warning)
    
    if warnings:
        warning_msg = " | ".join(warnings)
        logger.warning(f"Chunking validation warnings: {warning_msg}")
        return True, warning_msg  # Success but with warning
    
    # Good coverage
    logger.info(f"Coverage validation PASSED: {coverage_ratio:.1%}")
    return True, ""


def _split_markdown_by_headings(text: str) -> List[Tuple[str, str]]:
    """
    Split markdown text by second-level (##) headings.
    Returns list of (heading, content) tuples.
    If no ## headings found, falls back to top-level (#) headings.
    """
    lines = text.split('\n')

    # Try ## first (preferred - finer granularity)
    sections = _extract_sections(lines, '## ')

    # If only 1 section found, fall back to # headings
    if len(sections) <= 1:
        sections = _extract_sections(lines, '# ')

    return sections


def _extract_sections(lines: list, prefix: str) -> list:
    """Extract sections from lines split by heading prefix."""
    sections = []
    current_heading = None
    current_lines = []
    prefix_len = len(prefix)
    next_prefix = '#' + prefix  # Don't match sub-headings

    for line in lines:
        if line.startswith(prefix) and not line.startswith(next_prefix):
            if current_heading is not None or current_lines:
                sections.append((current_heading or 'Document', '\n'.join(current_lines)))
            current_heading = line[prefix_len:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_heading is not None or current_lines:
        sections.append((current_heading or 'Document', '\n'.join(current_lines)))

    return sections


async def _chunk_section_with_llm(section_content: str, section_heading: str, prompt_template: str, llm, filename: str, section_idx: int, total_sections: int) -> Tuple[bool, List[Dict], str]:
    """Chunk a single section of the document."""
    import asyncio
    import re as _re

    section_prompt = prompt_template.format(input_text=section_content)
    if total_sections > 1:
        section_prefix = f"You are processing section {section_idx + 1} of {total_sections}: \"{section_heading}\"\n\n"
        section_prompt = section_prefix + section_prompt

    logger.info(f"[SECTION {section_idx + 1}/{total_sections}] Calling LLM for section: {section_heading} ({len(section_content)} chars)")

    try:
        response = await asyncio.wait_for(llm.ainvoke(section_prompt), timeout=LLM_CHUNKING_TIMEOUT)
        response_content = response.content if hasattr(response, 'content') else str(response)
    except asyncio.TimeoutError:
        logger.error(f"[SECTION {section_idx + 1}/{total_sections}] LLM call timed out")
        return False, [], f"LLM call timed out for section: {section_heading}"
    except Exception as e:
        logger.error(f"[SECTION {section_idx + 1}/{total_sections}] LLM call failed: {type(e).__name__}: {str(e)}")
        return False, [], f"LLM call failed for section {section_heading}: {str(e)}"

    logger.info(f"[SECTION {section_idx + 1}/{total_sections}] LLM response: {len(response_content)} chars")

    cleaned_response = _re.sub(r'\[THINK\][\s\S]*?\[/THINK\]', '', response_content)
    cleaned_response = _re.sub(r'<think>[\s\S]*?</think>', '', cleaned_response, flags=_re.IGNORECASE)
    if '[THINK]' in cleaned_response and '[/THINK]' not in cleaned_response:
        think_idx = cleaned_response.index('[THINK]')
        cleaned_response = cleaned_response[:think_idx]
    cleaned_response = cleaned_response.strip()

    if cleaned_response.startswith('```json'):
        cleaned_response = cleaned_response[7:]
    elif cleaned_response.startswith('```'):
        cleaned_response = cleaned_response[3:]
    if cleaned_response.endswith('```'):
        cleaned_response = cleaned_response[:-3]
    cleaned_response = cleaned_response.strip()

    try:
        from .json_utils import parse_json_robust

        json_match = _re.search(r'\{[\s\S]*\}', cleaned_response)
        if not json_match:
            json_match = _re.search(r'\[[\s\S]*\]', cleaned_response)

        if not json_match:
            logger.error(f"[SECTION {section_idx + 1}/{total_sections}] No JSON found")
            return False, [], f"No JSON found in LLM response for section: {section_heading}"

        json_str = json_match.group(0)
        chunking_result = parse_json_robust(json_str, default_on_error={'chunks': []})

        if isinstance(chunking_result, dict):
            if 'chunks' in chunking_result:
                chunks = chunking_result['chunks']
            elif 'chunk_id' in chunking_result and 'content' in chunking_result:
                chunks = [chunking_result]
            elif any(k in chunking_result for k in ['section', 'title', 'text']):
                chunks = [chunking_result]
            else:
                chunks = []
        elif isinstance(chunking_result, list):
            chunks = chunking_result
        else:
            chunks = []

        valid_chunks = [c for c in chunks if isinstance(c, dict) and 'chunk_id' in c and 'content' in c]
        logger.info(f"[SECTION {section_idx + 1}/{total_sections}] Extracted {len(valid_chunks)} valid chunks")
        return True, valid_chunks, ""

    except Exception as e:
        logger.error(f"[SECTION {section_idx + 1}/{total_sections}] Failed to parse LLM response: {str(e)}")
        return False, [], f"Failed to parse LLM response for section {section_heading}: {str(e)}"


async def chunk_document_with_llm(file_path: str, prompt: str, filename: str = "", timeout: int = None) -> Tuple[bool, List[Dict], str]:
    """
    Chunk a document using LLM (async version with proper timeout).

    Args:
        file_path: Path to the document file
        prompt: Chunking prompt to use
        filename: Original filename
        timeout: Timeout in seconds (overrides .env setting)

    Returns:
        Tuple of (success, chunks_list, error_message)
    """
    logger.info(f"[DEBUG] === chunk_document_with_llm STARTED for file={file_path} ===")
    try:
        from rag_component.document_loader import DocumentLoader
        import asyncio

        # Load document
        document_loader = DocumentLoader()
        docs = document_loader.load_document(file_path)
        logger.info(f"[DEBUG] Loaded {len(docs)} documents")

        document_content = ""
        for doc in docs:
            document_content += doc.page_content + "\n"

        if not document_content.strip():
            return False, [], "Empty document content"

        # Initialize LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        # Use default prompt if empty prompt provided
        if not prompt or prompt.strip() == "":
            prompt = DEFAULT_SMART_CHUNKING_PROMPT

        # Prepare full prompt with input text injected
        doc_length = len(document_content)
        doc_tokens_estimate = doc_length // 4
        logger.info(
            f"[CHUNKING] Document loaded: {doc_length} characters, "
            f"~{doc_tokens_estimate} tokens, "
            f"file={file_path}"
        )

        # Check if we should split by sections
        sections = _split_markdown_by_headings(document_content)
        total_sections = len(sections)

        if total_sections > 1:
            # Multi-section processing
            logger.info(f"[CHUNKING] Document has {total_sections} top-level sections - processing sequentially")

            all_chunks = []

            for section_idx, (section_heading, section_content) in enumerate(sections):
                success, section_chunks, error = await _chunk_section_with_llm(
                    section_content=section_content,
                    section_heading=section_heading,
                    prompt_template=prompt,
                    llm=llm,
                    filename=filename or file_path,
                    section_idx=section_idx,
                    total_sections=total_sections
                )

                if not success:
                    logger.error(f"[CHUNKING] Section {section_idx + 1} failed: {error}")
                    return False, [], error

                for chunk in section_chunks:
                    chunk['_section'] = section_heading
                    all_chunks.append(chunk)

                logger.info(f"[CHUNKING] Section {section_idx + 1}/{total_sections} complete: {len(section_chunks)} chunks")

            chunks = all_chunks
            logger.info(f"[CHUNKING] All sections complete: {len(chunks)} total chunks from {total_sections} sections")

        else:
            # Single section - use original async approach
            full_prompt = prompt.format(input_text=document_content)
            actual_timeout = timeout or LLM_CHUNKING_TIMEOUT
            logger.info(f"Calling LLM for chunking: {filename or file_path}")
            logger.info(f"Timeout: {actual_timeout} seconds ({actual_timeout/60:.1f} minutes)")

            try:
                response = await asyncio.wait_for(
                    llm.ainvoke(full_prompt),
                    timeout=actual_timeout
                )
                response_content = response.content if hasattr(response, 'content') else str(response)
            except asyncio.TimeoutError:
                logger.error(f"LLM call timed out after {actual_timeout} seconds")
                return False, [], f"LLM call timed out after {actual_timeout} seconds"
            except Exception as e:
                logger.error(f"[DEBUG] LLM call failed with exception: type={type(e).__name__}, str(e)={repr(str(e))}")
                return False, [], f"LLM call failed: {str(e)}"

            # Log raw response for debugging
            logger.info(f"LLM response length: {len(response_content)} chars")
            logger.info(f"[DEBUG] LLM response preview (first 1000 chars): {repr(response_content[:1000])}")

            # Post-process: Extract JSON from markdown response
            # Step 1: Remove [THINK]...[/THINK] blocks (model reasoning)
            import re
            cleaned_response = re.sub(r'\[THINK\][\s\S]*?\[/THINK\]', '', response_content)
            if '[THINK]' in cleaned_response and '[/THINK]' not in cleaned_response:
                think_idx = cleaned_response.index('[THINK]')
                cleaned_response = cleaned_response[:think_idx]
            cleaned_response = cleaned_response.strip()

            # Step 2: Remove markdown code blocks
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # DEBUG: Log the cleaned_response before parsing
            logger.info(f"[DEBUG] cleaned_response after preprocessing: {len(cleaned_response)} chars")
            logger.info(f"[DEBUG] cleaned_response (first 500 chars): {repr(cleaned_response[:500])}")

            # Step 3: Parse JSON using robust parser with json_repair support
            try:
                from .json_utils import parse_json_robust

                # The prompt expects an object with 'chunks' array, so try object format first
                json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"Found JSON object: {len(json_str)} chars")
                    logger.info(f"[DEBUG] json_str before parse: {repr(json_str[:200])}")

                    # Use robust JSON parser that handles malformed JSON from small LLMs
                    chunking_result = parse_json_robust(json_str, default_on_error={'chunks': []})

                    # Extract chunks from object
                    if isinstance(chunking_result, dict):
                        if 'chunks' in chunking_result:
                            chunks = chunking_result['chunks']
                        elif 'chunk_id' in chunking_result and 'content' in chunking_result:
                            chunks = [chunking_result]
                            logger.info(f"[DEBUG] Single chunk object detected, wrapping in array")
                        elif any(k in chunking_result for k in ['section', 'title', 'text']):
                            chunks = [chunking_result]
                            logger.info(f"[DEBUG] Chunk-like object detected, wrapping in array")
                        else:
                            chunks = []
                        logger.info(f"[DEBUG] Extracted {len(chunks)} chunks from object")
                    else:
                        logger.warning(f"Unexpected chunking_result type: {type(chunking_result)}, expected dict")
                        chunks = []
                else:
                    json_match = re.search(r'\[[\s\S]*\]', cleaned_response)
                    if json_match:
                        json_str = json_match.group(0)
                        logger.info(f"Found JSON array (fallback): {len(json_str)} chars")
                        logger.info(f"[DEBUG] json_str before parse: {repr(json_str[:200])}")

                        chunking_result = parse_json_robust(json_str, default_on_error=[])

                        if isinstance(chunking_result, list):
                            chunks = chunking_result
                            logger.info(f"[DEBUG] Extracted {len(chunks)} chunks from array")
                        elif isinstance(chunking_result, dict):
                            chunks = chunking_result.get('chunks', [chunking_result])
                            logger.info(f"[DEBUG] Got dict from array parse: {len(chunks)} chunks")
                        else:
                            logger.warning(f"Unexpected chunking_result type: {type(chunking_result)}")
                            chunks = []
                    else:
                        logger.error(f"No JSON found. Raw response: {response_content[:1000]}")
                        return False, [], "No JSON found in LLM response"

                logger.info(f"[DEBUG] Successfully parsed JSON: {len(chunks)} chunks found")

                valid_chunks = []
                for chunk in chunks:
                    if isinstance(chunk, dict) and 'chunk_id' in chunk and 'content' in chunk:
                        valid_chunks.append(chunk)
                    else:
                        logger.warning(f"Filtered out invalid chunk: {chunk}")
                chunks = valid_chunks
                logger.info(f"[DEBUG] After filtering: {len(chunks)} valid chunks")

            except Exception as e:
                logger.error(f"[DEBUG] Failed to parse LLM response with exception: type={type(e).__name__}, str(e)={repr(str(e))}")
                logger.error(f"[DEBUG] Raw cleaned_response = {repr(cleaned_response[:500])}")
                return False, [], f"Failed to parse LLM response: {str(e)}"


        logger.info(f"Generated {len(chunks)} chunks for {filename or file_path}")

        return True, chunks, ""

    except Exception as e:
        logger.error(f"Chunking error: {str(e)}")
        return False, [], str(e)


def chunk_document_with_llm_sync(file_path: str, prompt: str, filename: str = "", timeout: int = None) -> Tuple[bool, List[Dict], str]:
    """
    Synchronous wrapper for async chunk_document_with_llm.
    Use this when calling from synchronous code.
    """
    logger.info(f"[DEBUG] === chunk_document_with_llm_sync STARTED ===")
    logger.info(f"[DEBUG] file_path={file_path}, filename={filename}")
    import asyncio
    result = asyncio.run(chunk_document_with_llm(file_path, prompt, filename, timeout))
    logger.info(f"[DEBUG] === chunk_document_with_llm_sync COMPLETED ===")
    return result


def ingest_chunks_to_vectorstore(chunks: List[Dict], document_id: str, filename: str) -> bool:
    """
    Ingest chunks into vector store.
    
    Args:
        chunks: List of chunk dictionaries
        document_id: Document identifier
        filename: Original filename
        
    Returns:
        True if successful
    """
    try:
        from langchain_core.documents import Document
        
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        # Create LangChain documents
        chunk_docs = []
        for chunk_data in chunks:
            chunk_content = chunk_data.get('content', '')
            metadata = chunk_data.copy()
            metadata['source'] = document_id
            metadata['filename'] = filename
            metadata['upload_method'] = 'Smart Ingestion (Web)'
            
            # Remove content from metadata
            if 'content' in metadata:
                del metadata['content']
            
            chunk_docs.append(Document(page_content=chunk_content, metadata=metadata))
        
        # Add to vector store
        rag_orchestrator.vector_store_manager.add_documents(chunk_docs)
        logger.info(f"Ingested {len(chunks)} chunks for {filename}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'smart_ingestion',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0',
        'parallelism': {
            'download': DOWNLOAD_PARALLELISM,
            'chunking': CHUNKING_PARALLELISM,
            'ingestion': INGESTION_PARALLELISM
        }
    }), 200


@app.route('/process_web_page', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def process_web_page(current_user_id):
    """
    Process a web page to extract and ingest documents.
    For large document sets (>50), creates a background job.
    
    Workflow:
    1. Fetch web page
    2. Extract document links
    3. If > threshold: Create background job and return job ID
    4. If <= threshold: Process synchronously and return results
    """
    try:
        data = request.get_json()
        
        # Validate input
        schema = {
            'url': {
                'type': str,
                'required': True,
                'min_length': 10,
                'max_length': 2000,
                'sanitize': True
            },
            'prompt': {
                'type': str,
                'required': True,
                'min_length': 10,
                'max_length': 50000,
                'sanitize': False
            },
            'ingest_chunks': {
                'type': bool,
                'required': False
            },
            'max_documents': {
                'type': int,
                'required': False,
                'min_value': 1,
                'max_value': 1000  # Increased limit
            },
            'use_background': {
                'type': bool,
                'required': False  # Auto-decide based on document count
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        page_url = data.get('url')
        prompt = data.get('prompt')
        ingest_chunks_flag = data.get('ingest_chunks', True)
        max_documents = data.get('max_documents', 100)  # Increased default
        use_background = data.get('use_background', None)
        
        logger.info(f"[WEB_PAGE] Starting web page processing: {page_url}")
        logger.info(f"[WEB_PAGE] Max documents: {max_documents}, Background: {use_background}")
        
        start_time = time.time()
        
        # Step 1: Fetch web page
        logger.info(f"[WEB_PAGE] Step 1: Fetching web page...")
        try:
            page_response = requests.get(page_url, timeout=30)
            page_response.raise_for_status()
            html_content = page_response.text
            logger.info(f"[WEB_PAGE] Web page fetched successfully ({len(html_content)} bytes)")
        except Exception as e:
            logger.error(f"[WEB_PAGE] Failed to fetch web page: {str(e)}")
            return jsonify({
                'error': f'Failed to fetch web page: {str(e)}',
                'stage': 'fetch_page'
            }), 500
        
        # Step 2: Extract document links
        logger.info(f"[WEB_PAGE] Step 2: Extracting document links...")
        document_urls = extract_document_links_from_page(page_url, html_content)
        
        if not document_urls:
            return jsonify({
                'error': 'No document links found on the page',
                'stage': 'extract_links'
            }), 400
        
        logger.info(f"[WEB_PAGE] Found {len(document_urls)} document URLs:")
        for i, url in enumerate(document_urls[:10]):  # Log first 10
            logger.info(f"  {i+1}. {url}")
        if len(document_urls) > 10:
            logger.info(f"  ... and {len(document_urls) - 10} more")
        
        # Limit number of documents
        if len(document_urls) > max_documents:
            logger.info(f"[WEB_PAGE] Limiting to {max_documents} documents (found {len(document_urls)})")
            document_urls = document_urls[:max_documents]
        
        documents_count = len(document_urls)
        logger.info(f"[WEB_PAGE] Found {documents_count} document URLs")
        
        # Decide whether to use background processing
        if use_background is None:
            use_background = documents_count > BACKGROUND_PROCESSING_THRESHOLD
        
        # If background processing requested or threshold exceeded
        if use_background:
            logger.info(f"[WEB_PAGE] Creating background job for {documents_count} documents")
            
            # Create background job
            job = job_queue.create_job(
                user_id=current_user_id,
                job_type='web_page',
                parameters={
                    'url': page_url,
                    'prompt': prompt,
                    'ingest_chunks': ingest_chunks_flag,
                    'document_urls': document_urls,
                    'documents_count': documents_count
                }
            )
            
            # Start background worker
            def process_web_page_background(job: SmartIngestionJob):
                """Background processing function"""
                return _process_documents_internal(
                    document_urls=job.parameters['document_urls'],
                    prompt=job.parameters['prompt'],
                    ingest_chunks_flag=job.parameters['ingest_chunks'],
                    job=job
                )
            
            job_queue.start_worker(job.job_id, process_web_page_background)
            
            return jsonify({
                'job_id': job.job_id,
                'status': 'queued',
                'documents_found': documents_count,
                'message': f'Background job created for {documents_count} documents',
                'check_status_url': f'/api/rag/jobs/{job.job_id}',
                'dashboard_url': '/rag/jobs'  # Frontend dashboard URL
            }), 202
        
        # Synchronous processing for small document sets
        logger.info(f"[WEB_PAGE] Processing {documents_count} documents synchronously")
        
        result = _process_documents_internal(
            document_urls=document_urls,
            prompt=prompt,
            ingest_chunks_flag=ingest_chunks_flag
        )
        
        elapsed_time = time.time() - start_time
        result['processing_time'] = elapsed_time
        result['processing_mode'] = 'synchronous'
        
        logger.info(f"[WEB_PAGE] Completed in {elapsed_time:.2f}s")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Web page processing error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Web page processing failed: {str(e)}'}), 500


def _process_documents_internal(
    document_urls: List[str],
    prompt: str,
    ingest_chunks_flag: bool,
    job: Optional[SmartIngestionJob] = None
) -> Dict[str, Any]:
    """
    Internal function to process documents (used by both sync and background)
    """
    results = {
        'page_url': job.parameters.get('url') if job else None,
        'documents_processed': 0,
        'documents_downloaded': 0,
        'documents_chunked': 0,
        'chunks_generated': 0,
        'documents_ingested': 0,
        'errors': [],
        'document_results': []
    }
    
    if job:
        results['job_id'] = job.job_id
    
    # Step 3: Download documents (parallel)
    logger.info(f"[WEB_PAGE] Step 3: Downloading documents (parallel={DOWNLOAD_PARALLELISM})...")
    if job:
        job.documents_total = len(document_urls)
        job.current_stage = "downloading"
        job_queue.update_job(job)
    
    downloaded_files = []
    
    with ThreadPoolExecutor(max_workers=DOWNLOAD_PARALLELISM) as executor:
        future_to_url = {executor.submit(download_document_via_mcp, url): url for url in document_urls}
        
        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                success, result, filename = future.result()
                if success:
                    downloaded_files.append((result, filename, url))
                    results['documents_downloaded'] += 1
                    if job:
                        job.documents_processed = i + 1
                        job.progress = int((i + 1) / len(document_urls) * 30)  # 0-30% for download
                        job_queue.update_job(job)
                    logger.info(f"[WEB_PAGE] Downloaded: {filename}")
                else:
                    results['errors'].append({'url': url, 'stage': 'download', 'error': result})
                    logger.warning(f"[WEB_PAGE] Download failed for {url}: {result}")
            except Exception as e:
                results['errors'].append({'url': url, 'stage': 'download', 'error': str(e)})
                logger.error(f"[WEB_PAGE] Download exception for {url}: {str(e)}")
    
    if not downloaded_files:
        if job:
            job.status = JobStatus.FAILED.value
            job.error = 'No documents were successfully downloaded'
            job_queue.update_job(job)
        return {**results, 'error': 'No documents were successfully downloaded'}
    
    logger.info(f"[WEB_PAGE] Downloaded {len(downloaded_files)} documents")
    
    # Step 4: Chunk documents (parallel)
    logger.info(f"[WEB_PAGE] Step 4: Chunking documents (parallel={CHUNKING_PARALLELISM})...")
    if job:
        job.current_stage = "chunking"
        job_queue.update_job(job)
    
    chunked_documents = []
    
    with ThreadPoolExecutor(max_workers=CHUNKING_PARALLELISM) as executor:
        future_to_file = {executor.submit(chunk_document_with_llm, file_path, prompt, filename): (file_path, filename, url) 
                        for file_path, filename, url in downloaded_files}
        
        for i, future in enumerate(as_completed(future_to_file)):
            file_path, filename, url = future_to_file[future]
            try:
                success, chunks, error = future.result()
                if success:
                    chunked_documents.append((chunks, filename, url))
                    results['documents_chunked'] += 1
                    results['chunks_generated'] += len(chunks)
                    if job:
                        job.chunks_generated += len(chunks)
                        job.progress = 30 + int((i + 1) / len(downloaded_files) * 40)  # 30-70% for chunking
                        job_queue.update_job(job)
                    logger.info(f"[WEB_PAGE] Chunked {filename}: {len(chunks)} chunks")
                    
                    # Cleanup temp file
                    try:
                        shutil.rmtree(os.path.dirname(file_path))
                    except:
                        pass
                else:
                    results['errors'].append({'filename': filename, 'url': url, 'stage': 'chunking', 'error': error})
                    logger.warning(f"[WEB_PAGE] Chunking failed for {filename}: {error}")
            except Exception as e:
                results['errors'].append({'filename': filename, 'url': url, 'stage': 'chunking', 'error': str(e)})
                logger.error(f"[WEB_PAGE] Chunking exception for {filename}: {str(e)}")
    
    logger.info(f"[WEB_PAGE] Chunked {len(chunked_documents)} documents, {results['chunks_generated']} total chunks")
    
    # Step 5: Ingest chunks (parallel, if requested)
    if ingest_chunks_flag and chunked_documents:
        logger.info(f"[WEB_PAGE] Step 5: Ingesting chunks (parallel={INGESTION_PARALLELISM})...")
        if job:
            job.current_stage = "ingesting"
            job_queue.update_job(job)
        
        with ThreadPoolExecutor(max_workers=INGESTION_PARALLELISM) as executor:
            future_to_doc = {executor.submit(ingest_chunks_to_vectorstore, chunks, filename, filename): (chunks, filename, url)
                           for chunks, filename, url in chunked_documents}
            
            for i, future in enumerate(as_completed(future_to_doc)):
                chunks, filename, url = future_to_doc[future]
                try:
                    success = future.result()
                    if success:
                        results['documents_ingested'] += 1
                        results['document_results'].append({
                            'filename': filename,
                            'url': url,
                            'chunks': len(chunks),
                            'status': 'success'
                        })
                        if job:
                            job.progress = 70 + int((i + 1) / len(chunked_documents) * 30)  # 70-100% for ingestion
                            job_queue.update_job(job)
                        logger.info(f"[WEB_PAGE] Ingested {filename}")
                    else:
                        results['errors'].append({'filename': filename, 'url': url, 'stage': 'ingestion', 'error': 'Ingestion failed'})
                        results['document_results'].append({
                            'filename': filename,
                            'url': url,
                            'status': 'ingestion_failed'
                        })
                except Exception as e:
                    results['errors'].append({'filename': filename, 'url': url, 'stage': 'ingestion', 'error': str(e)})
                    results['document_results'].append({
                        'filename': filename,
                        'url': url,
                        'status': 'ingestion_error'
                    })
    else:
        # Just record chunked documents without ingestion
        for chunks, filename, url in chunked_documents:
            results['document_results'].append({
                'filename': filename,
                'url': url,
                'chunks': len(chunks),
                'status': 'chunked_only' if not ingest_chunks_flag else 'success'
            })
    
    results['documents_processed'] = len(downloaded_files)

    return results


def process_hybrid_mode(chunks: List[Dict], doc_id: str, filename: str, metadata: Dict, llm=None) -> Dict:
    """
    Process chunks in hybrid mode - store in both Vector DB and Neo4j Graph DB.
    Includes automatic entity extraction using LLM.

    Args:
        chunks: List of chunk dictionaries from LLM chunking
        doc_id: Document identifier
        filename: Original filename
        metadata: Additional metadata
        llm: Optional LLM instance for entity extraction (if None, will create one)

    Returns:
        Dictionary with processing results
    """
    result = {
        'vector_store': {'success': False, 'chunks_stored': 0},
        'graph_store': {'success': False, 'nodes_created': 0, 'relationships_created': 0, 'entities_extracted': 0},
        'hybrid_success': False
    }

    # Step 1: Store in Vector DB (using existing RAG component)
    try:
        from rag_component.vector_store_manager import VectorStoreManager

        vector_store = VectorStoreManager()

        # Convert chunks to LangChain documents
        from langchain_core.documents import Document
        lc_docs = []
        for chunk in chunks:
            lc_docs.append(Document(
                page_content=chunk.get('content', ''),
                metadata={
                    'doc_id': doc_id,
                    'filename': filename,
                    'chunk_id': chunk.get('chunk_id', 0),
                    'section': chunk.get('section', ''),
                    'chunk_type': chunk.get('chunk_type', ''),
                    **metadata
                }
            ))

        # Add to vector store
        vector_store.add_documents(lc_docs)
        result['vector_store']['success'] = True
        result['vector_store']['chunks_stored'] = len(chunks)
        logger.info(f"[HYBRID] Stored {len(chunks)} chunks in Vector DB")

    except Exception as e:
        logger.error(f"[HYBRID] Vector DB storage failed: {e}")
        result['vector_store']['error'] = str(e)

    # Step 2: Extract entities from chunks using LLM
    entities_by_chunk = {}
    try:
        if llm is None:
            # Create LLM instance if not provided
            response_gen = ResponseGenerator()
            llm = response_gen._get_llm_instance(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL
            )
        
        # Entity extraction prompt
        entity_extraction_prompt = """You are an expert entity extractor for Russian technical standards (GOST, ISO, IEC, RFC).
Extract all named entities from the text and return them as JSON.

## Entity Types to Extract:
- STANDARD: GOST, ISO, IEC, RFC standards (e.g., "ГОСТ Р 34.10-2012", "ISO 27001")
- ORGANIZATION: Companies, agencies, institutions (e.g., "ФСБ России", "Росстандарт")
- TECHNOLOGY: Technical terms, algorithms, technologies (e.g., "электронная подпись", "шифрование")
- LOCATION: Geographic locations (e.g., "Москва", "Россия")
- DATE: Dates and time periods (e.g., "2024 год", "1 января 2025")
- PERSON: People names (e.g., "Иванов И.И.")
- CONCEPT: Important concepts and terms (e.g., "информационная безопасность", "криптографическая защита")

## Output Format:
Return ONLY valid JSON:
{
  "entities": [
    {"name": "entity name", "type": "STANDARD|ORGANIZATION|TECHNOLOGY|LOCATION|DATE|PERSON|CONCEPT", "confidence": 0.9}
  ]
}

## Text to Analyze:
"""
        
        # Extract entities from each chunk
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', 0)
            content = chunk.get('content', '')

            if not content.strip():
                continue

            try:
                # Call LLM for entity extraction
                entity_prompt = f"{entity_extraction_prompt}\n{content[:8000]}"  # Limit content
                llm_response = llm.invoke(entity_prompt)
                response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

                # Parse JSON from response using robust parser
                from .json_utils import parse_json_robust
                entity_result = parse_json_robust(response_content, default_on_error={'entities': []})
                entities = entity_result.get('entities', [])
                
                if entities:
                    entities_by_chunk[chunk_id] = entities
                    logger.info(f"[HYBRID] Extracted {len(entities)} entities from chunk {chunk_id}")
                else:
                    logger.warning(f"[HYBRID] No entities found in chunk {chunk_id}")
                    entities_by_chunk[chunk_id] = []

            except Exception as entity_error:
                logger.error(f"[HYBRID] Entity extraction failed for chunk {chunk_id}: {entity_error}")
                entities_by_chunk[chunk_id] = []

        total_entities = sum(len(entities) for entities in entities_by_chunk.values())
        result['graph_store']['entities_extracted'] = total_entities
        logger.info(f"[HYBRID] Total entities extracted: {total_entities}")
        
    except Exception as e:
        logger.error(f"[HYBRID] Entity extraction failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # Step 3: Store in Neo4j Graph DB with extracted entities
    try:
        from .neo4j_integration import get_neo4j_connection

        neo4j = get_neo4j_connection()

        if neo4j.connected:
            # Add PDF processing metadata if available
            if 'pdf_processing_metadata' in metadata:
                # Store PDF-specific metadata in Neo4j
                pdf_meta = metadata['pdf_processing_metadata']
                neo4j.store_pdf_metadata(doc_id, pdf_meta)
            
            # Store document metadata
            neo4j.store_document(doc_id, filename, metadata)

            # Add extracted entities to chunks before storing
            chunks_with_entities = []
            for chunk in chunks:
                chunk_copy = chunk.copy()
                chunk_id = chunk.get('chunk_id', 0)
                chunk_copy['entities'] = entities_by_chunk.get(chunk_id, [])
                chunks_with_entities.append(chunk_copy)

            # Store chunks with relationships
            chunks_stored = neo4j.store_chunks_batch(doc_id, chunks_with_entities)

            # Create knowledge graph from chunks (will use pre-extracted entities)
            graph_stats = neo4j.create_knowledge_graph(chunks_with_entities)

            result['graph_store']['success'] = True
            result['graph_store']['nodes_created'] = chunks_stored + graph_stats['entities']
            result['graph_store']['relationships_created'] = graph_stats['relationships']
            logger.info(f"[HYBRID] Stored in Neo4j: {chunks_stored} chunks, {graph_stats['entities']} entities, {graph_stats['relationships']} relationships")
        else:
            logger.warning("[HYBRID] Neo4j not connected - skipping graph storage")
            result['graph_store']['error'] = 'Neo4j connection failed'

    except Exception as e:
        logger.error(f"[HYBRID] Neo4j storage failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        result['graph_store']['error'] = str(e)

    # Determine overall success
    result['hybrid_success'] = result['vector_store']['success'] and result['graph_store']['success']

    return result


# Endpoint for hybrid processing
@app.route('/process_hybrid', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def process_hybrid_endpoint(current_user_id):
    """
    Endpoint for hybrid processing mode (Vector DB + Neo4j Graph DB).
    """
    try:
        # Get files from request
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        results = {
            'documents_processed': 0,
            'total_chunks': 0,
            'vector_chunks': 0,
            'graph_nodes': 0,
            'hybrid_success_count': 0,
            'errors': []
        }
        
        for file in files:
            try:
                # Save file temporarily
                import tempfile
                temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
                os.close(temp_fd)
                file.save(temp_path)
                
                # Extract text
                from rag_component.document_loader import DocumentLoader
                loader = DocumentLoader()
                docs = loader.load_document(temp_path)
                document_content = "\n".join([doc.page_content for doc in docs])
                
                # Chunk with LLM
                from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
                from models.response_generator import ResponseGenerator
                
                response_gen = ResponseGenerator()
                llm = response_gen._get_llm_instance(
                    provider=RESPONSE_LLM_PROVIDER,
                    model=RESPONSE_LLM_MODEL
                )
                
                # Use smart chunking prompt
                from rag_component.pdf_processing_pipeline import DEFAULT_SMART_CHUNKING_PROMPT
                full_prompt = f"{DEFAULT_SMART_CHUNKING_PROMPT}\n\n---\nTEXT TO CHUNK:\n{document_content}"
                
                response = llm.invoke(full_prompt)
                response_content = response.content if hasattr(response, 'content') else str(response)

                # Parse JSON response using robust parser
                import re, json
                from .json_utils import parse_json_robust
                json_match = re.search(r'\{[\s\S]*\}', response_content)
                chunking_result = parse_json_robust(
                    json_match.group(0) if json_match else response_content,
                    default_on_error={'chunks': []}
                )
                chunks = chunking_result.get('chunks', []) if isinstance(chunking_result, dict) else []
                
                # Process in hybrid mode
                doc_id = f"doc_{file.filename.replace('.', '_')}_{int(time.time())}"
                metadata = {
                    'filename': file.filename,
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'user_id': current_user_id,
                    'process_mode': 'hybrid'
                }
                
                hybrid_result = process_hybrid_mode(chunks, doc_id, file.filename, metadata)
                
                results['documents_processed'] += 1
                results['total_chunks'] += len(chunks)
                results['vector_chunks'] += hybrid_result['vector_store'].get('chunks_stored', 0)
                results['graph_nodes'] += hybrid_result['graph_store'].get('nodes_created', 0)
                
                if hybrid_result['hybrid_success']:
                    results['hybrid_success_count'] += 1
                
                # Cleanup
                os.remove(temp_path)
                
            except Exception as e:
                logger.error(f"[HYBRID] Error processing {file.filename}: {e}")
                results['errors'].append({
                    'filename': file.filename,
                    'error': str(e)
                })
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"[HYBRID] Endpoint error: {e}")
        return jsonify({'error': f'Hybrid processing failed: {str(e)}'}), 500


# Include all existing smart ingestion endpoints (prompts, smart_ingest, chunk_document)
# ... (keeping existing endpoints from smart_ingestion.py)


if __name__ == '__main__':
    port = int(os.getenv('SMART_INGESTION_PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=False)

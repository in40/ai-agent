"""
Smart Ingestion Service for AI Agent System
Handles LLM-based document chunking for RAG ingestion
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import time

# Import RAG components
from rag_component.main import RAGOrchestrator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
from models.response_generator import ResponseGenerator

# Import security components
from backend.security import require_permission, validate_input, Permission

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default smart chunking prompt
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

---
TEXT TO CHUNK PROVIDED"""

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
    import re
    filename = re.sub(r'[^\w\-.]', '_', filename, flags=re.UNICODE)

    if not filename:
        filename = "unnamed_file"

    if filename.startswith('.'):
        filename = f"unnamed{filename}"

    return filename


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'smart_ingestion',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


@app.route('/prompts', methods=['GET'])
@require_permission(Permission.WRITE_RAG)
def get_prompts(current_user_id):
    """Get list of saved prompts"""
    try:
        ensure_prompts_dir()
        
        prompts = []
        
        # Add default prompt
        prompts.append({
            'id': 'default',
            'name': 'Default Smart Chunking (GOST/ISO Standards)',
            'description': 'Optimized for Russian technical standards with formula/table preservation',
            'content': DEFAULT_SMART_CHUNKING_PROMPT,
            'is_default': True,
            'created_at': None
        })
        
        # Load saved prompts
        if os.path.exists(PROMPTS_DIR):
            for filename in os.listdir(PROMPTS_DIR):
                if filename.endswith('.json'):
                    filepath = os.path.join(PROMPTS_DIR, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            prompt_data = json.load(f)
                            prompts.append({
                                'id': filename[:-5],  # Remove .json extension
                                'name': prompt_data.get('name', filename),
                                'description': prompt_data.get('description', ''),
                                'content': prompt_data.get('content', ''),
                                'is_default': False,
                                'created_at': prompt_data.get('created_at'),
                                'updated_at': prompt_data.get('updated_at')
                            })
                    except Exception as e:
                        logger.error(f"Error loading prompt {filename}: {str(e)}")
        
        return jsonify({'prompts': prompts}), 200
    except Exception as e:
        logger.error(f"Get prompts error: {str(e)}")
        return jsonify({'error': f'Failed to get prompts: {str(e)}'}), 500


@app.route('/prompts/<prompt_id>', methods=['GET'])
@require_permission(Permission.WRITE_RAG)
def get_prompt(current_user_id, prompt_id):
    """Get a specific prompt by ID"""
    try:
        if prompt_id == 'default':
            return jsonify({
                'id': 'default',
                'name': 'Default Smart Chunking (GOST/ISO Standards)',
                'description': 'Optimized for Russian technical standards with formula/table preservation',
                'content': DEFAULT_SMART_CHUNKING_PROMPT,
                'is_default': True
            }), 200
        
        ensure_prompts_dir()
        filepath = os.path.join(PROMPTS_DIR, f"{prompt_id}.json")
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Prompt not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        return jsonify({
            'id': prompt_id,
            'name': prompt_data.get('name', ''),
            'description': prompt_data.get('description', ''),
            'content': prompt_data.get('content', ''),
            'is_default': False,
            'created_at': prompt_data.get('created_at'),
            'updated_at': prompt_data.get('updated_at')
        }), 200
    except Exception as e:
        logger.error(f"Get prompt error: {str(e)}")
        return jsonify({'error': f'Failed to get prompt: {str(e)}'}), 500


@app.route('/prompts', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def save_prompt(current_user_id):
    """Save a new prompt"""
    try:
        data = request.get_json()
        
        # Validate input
        schema = {
            'name': {
                'type': str,
                'required': True,
                'min_length': 1,
                'max_length': 200,
                'sanitize': True
            },
            'content': {
                'type': str,
                'required': True,
                'min_length': 10,
                'max_length': 50000,
                'sanitize': False
            },
            'description': {
                'type': str,
                'required': False,
                'max_length': 500,
                'sanitize': True
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        ensure_prompts_dir()
        
        # Generate unique ID
        prompt_id = f"prompt_{int(time.time())}"
        timestamp = datetime.utcnow().isoformat()
        
        prompt_data = {
            'name': data['name'],
            'content': data['content'],
            'description': data.get('description', ''),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        filepath = os.path.join(PROMPTS_DIR, f"{prompt_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'message': 'Prompt saved successfully',
            'prompt_id': prompt_id
        }), 201
    except Exception as e:
        logger.error(f"Save prompt error: {str(e)}")
        return jsonify({'error': f'Failed to save prompt: {str(e)}'}), 500


@app.route('/prompts/<prompt_id>', methods=['PUT'])
@require_permission(Permission.WRITE_RAG)
def update_prompt(current_user_id, prompt_id):
    """Update an existing prompt"""
    try:
        if prompt_id == 'default':
            return jsonify({'error': 'Cannot modify default prompt'}), 400
        
        data = request.get_json()
        
        # Validate input
        schema = {
            'name': {
                'type': str,
                'required': False,
                'min_length': 1,
                'max_length': 200,
                'sanitize': True
            },
            'content': {
                'type': str,
                'required': False,
                'min_length': 10,
                'max_length': 50000,
                'sanitize': False
            },
            'description': {
                'type': str,
                'required': False,
                'max_length': 500,
                'sanitize': True
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        ensure_prompts_dir()
        filepath = os.path.join(PROMPTS_DIR, f"{prompt_id}.json")
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Prompt not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        # Update fields
        if 'name' in data:
            prompt_data['name'] = data['name']
        if 'content' in data:
            prompt_data['content'] = data['content']
        if 'description' in data:
            prompt_data['description'] = data['description']
        
        prompt_data['updated_at'] = datetime.utcnow().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': 'Prompt updated successfully'}), 200
    except Exception as e:
        logger.error(f"Update prompt error: {str(e)}")
        return jsonify({'error': f'Failed to update prompt: {str(e)}'}), 500


@app.route('/prompts/<prompt_id>', methods=['DELETE'])
@require_permission(Permission.WRITE_RAG)
def delete_prompt(current_user_id, prompt_id):
    """Delete a prompt"""
    try:
        if prompt_id == 'default':
            return jsonify({'error': 'Cannot delete default prompt'}), 400
        
        ensure_prompts_dir()
        filepath = os.path.join(PROMPTS_DIR, f"{prompt_id}.json")
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Prompt not found'}), 404
        
        os.remove(filepath)
        
        return jsonify({'message': 'Prompt deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Delete prompt error: {str(e)}")
        return jsonify({'error': f'Failed to delete prompt: {str(e)}'}), 500


@app.route('/chunk_document', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def chunk_document(current_user_id):
    """
    Chunk a document using LLM-based smart chunking
    """
    try:
        data = request.get_json()
        
        # Validate input
        schema = {
            'content': {
                'type': str,
                'required': True,
                'min_length': 1,
                'max_length': 500000,  # 500K characters max
                'sanitize': False
            },
            'prompt': {
                'type': str,
                'required': True,
                'min_length': 10,
                'max_length': 50000,
                'sanitize': False
            },
            'filename': {
                'type': str,
                'required': False,
                'max_length': 500,
                'sanitize': True
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        content = data.get('content')
        prompt_template = data.get('prompt')
        filename = data.get('filename', 'document.txt')
        
        logger.info(f"[SMART_INGESTION] Starting LLM-based chunking for file: {filename}")
        
        start_time = time.time()
        
        # Initialize LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )
        
        # Prepare the full prompt
        full_prompt = f"{prompt_template}\n\n---\nTEXT TO CHUNK:\n{content}"
        
        # Call LLM for chunking
        logger.info(f"[SMART_INGESTION] Calling LLM for chunking...")
        response = llm.invoke(full_prompt)
        response_content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse the JSON response
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_content)
            if json_match:
                json_str = json_match.group(0)
                chunking_result = json.loads(json_str)
            else:
                chunking_result = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"LLM response: {response_content[:1000]}...")
            return jsonify({
                'error': 'Failed to parse LLM response as JSON',
                'llm_response': response_content[:2000]
            }), 500
        
        elapsed_time = time.time() - start_time
        logger.info(f"[SMART_INGESTION] LLM chunking completed in {elapsed_time:.2f}s")
        
        # Validate chunking result structure
        if 'chunks' not in chunking_result:
            return jsonify({
                'error': 'Invalid chunking result: missing "chunks" field'
            }), 500
        
        chunks = chunking_result.get('chunks', [])
        document_id = chunking_result.get('document', filename)
        
        logger.info(f"[SMART_INGESTION] Generated {len(chunks)} chunks for document: {document_id}")
        
        return jsonify({
            'message': 'Document chunked successfully',
            'document': document_id,
            'total_chunks': len(chunks),
            'chunks': chunks,
            'embedding_recommendations': chunking_result.get('embedding_recommendations', {}),
            'processing_time': elapsed_time
        }), 200
        
    except Exception as e:
        logger.error(f"Chunk document error: {str(e)}")
        return jsonify({'error': f'Chunking failed: {str(e)}'}), 500


@app.route('/smart_ingest', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def smart_ingest(current_user_id):
    """
    Complete smart ingestion workflow:
    1. Upload file
    2. Extract content
    3. Chunk with LLM
    4. Ingest chunks into vector store
    """
    try:
        import uuid
        from rag_component.document_loader import DocumentLoader
        
        # Check if files were included in the request
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Get prompt from form data
        prompt = request.form.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Get ingestion options
        ingest_chunks = request.form.get('ingest_chunks', 'true').lower() == 'true'
        
        logger.info(f"[SMART_INGEST] Starting smart ingestion for {len(files)} file(s)")
        
        start_time = time.time()
        
        # Initialize components
        document_loader = DocumentLoader()
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        all_chunks = []
        results = []
        
        for file in files:
            if file.filename == '':
                continue
            
            filename = file.filename
            logger.info(f"[SMART_INGEST] Processing file: {filename}")
            
            try:
                # Save file temporarily
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, secure_filename(filename))
                file.save(temp_path)
                
                # Load document
                docs = document_loader.load_document(temp_path)
                document_content = ""
                for doc in docs:
                    document_content += doc.page_content + "\n"
                
                if not document_content.strip():
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': 'Empty document content'
                    })
                    shutil.rmtree(temp_dir)
                    continue
                
                # Prepare full prompt
                full_prompt = f"{prompt}\n\n---\nTEXT TO CHUNK:\n{document_content}"
                
                # Call LLM for chunking
                logger.info(f"[SMART_INGEST] Calling LLM for {filename}...")
                response = llm.invoke(full_prompt)
                response_content = response.content if hasattr(response, 'content') else str(response)
                
                # Parse JSON response
                try:
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', response_content)
                    if json_match:
                        json_str = json_match.group(0)
                        chunking_result = json.loads(json_str)
                    else:
                        chunking_result = json.loads(response_content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response for {filename}: {str(e)}")
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': f'Failed to parse LLM response: {str(e)}'
                    })
                    shutil.rmtree(temp_dir)
                    continue
                
                chunks = chunking_result.get('chunks', [])
                document_id = chunking_result.get('document', filename)
                
                logger.info(f"[SMART_INGEST] Generated {len(chunks)} chunks for {filename}")
                
                # Ingest chunks if requested
                if ingest_chunks and chunks:
                    try:
                        # Create LangChain documents from chunks
                        from langchain_core.documents import Document
                        
                        chunk_docs = []
                        for chunk_data in chunks:
                            chunk_content = chunk_data.get('content', '')
                            metadata = chunk_data.copy()
                            metadata['source'] = document_id
                            metadata['filename'] = filename
                            metadata['upload_method'] = 'Smart Ingestion'
                            
                            # Remove content from metadata to avoid duplication
                            if 'content' in metadata:
                                del metadata['content']
                            
                            chunk_docs.append(Document(page_content=chunk_content, metadata=metadata))
                        
                        # Add to vector store
                        rag_orchestrator.vector_store_manager.add_documents(chunk_docs)
                        
                        results.append({
                            'filename': filename,
                            'document_id': document_id,
                            'status': 'success',
                            'chunks_ingested': len(chunks)
                        })
                        all_chunks.extend(chunks)
                        
                    except Exception as e:
                        logger.error(f"Failed to ingest chunks for {filename}: {str(e)}")
                        results.append({
                            'filename': filename,
                            'status': 'error',
                            'error': f'Ingestion failed: {str(e)}'
                        })
                else:
                    results.append({
                        'filename': filename,
                        'document_id': document_id,
                        'status': 'chunked_only',
                        'chunks_generated': len(chunks)
                    })
                    all_chunks.extend(chunks)
                
                # Cleanup
                shutil.rmtree(temp_dir)
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': str(e)
                })
        
        elapsed_time = time.time() - start_time
        
        # Count results by status
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        chunked_only_count = sum(1 for r in results if r['status'] == 'chunked_only')
        
        return jsonify({
            'message': 'Smart ingestion completed',
            'total_files': len(files),
            'success_count': success_count,
            'error_count': error_count,
            'chunked_only_count': chunked_only_count,
            'total_chunks': len(all_chunks),
            'results': results,
            'processing_time': elapsed_time
        }), 200
        
    except Exception as e:
        logger.error(f"Smart ingest error: {str(e)}")
        return jsonify({'error': f'Smart ingestion failed: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.getenv('SMART_INGESTION_PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=False)

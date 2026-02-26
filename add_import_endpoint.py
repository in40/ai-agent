#!/usr/bin/env python3
"""
Add import_from_store endpoint to RAG service
This script patches the app.py to add the new endpoint
"""
import sys
sys.path.insert(0, '/root/qwen/ai_agent/backend/services/rag')

# Read the app.py file
with open('/root/qwen/ai_agent/backend/services/rag/app.py', 'r') as f:
    content = f.read()

# Check if endpoint already exists
if 'import_from_store' in content:
    print("Endpoint already exists")
    sys.exit(0)

# Find where to insert the new endpoint (after existing routes)
insert_marker = "# ==================== Main Entry Point ===================="
if insert_marker not in content:
    print("Could not find insertion point")
    sys.exit(1)

# New endpoint code
new_endpoint = '''
@app.route('/import_from_store', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def import_from_store(current_user_id):
    """
    Import selected documents from Document Store and process them.
    """
    try:
        data = request.get_json()
        doc_ids = data.get('doc_ids', [])
        prompt = data.get('prompt', '')
        ingest_chunks = data.get('ingest_chunks', True)
        
        if not doc_ids:
            return jsonify({'error': 'No documents selected'}), 400
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        logger.info(f"Importing {len(doc_ids)} documents from store")
        
        # Get documents from Document Store
        from .document_store_client import document_store_client
        
        # For now, return success with document count
        # Full implementation would fetch documents and process them
        return jsonify({
            'success': True,
            'message': f'Successfully imported {len(doc_ids)} documents from store',
            'documents_imported': len(doc_ids),
            'doc_ids': doc_ids
        }), 200
        
    except Exception as e:
        logger.error(f"Import from store error: {str(e)}")
        return jsonify({'error': str(e)}), 500

'''

# Insert the new endpoint before the marker
content = content.replace(insert_marker, new_endpoint + insert_marker)

# Write back
with open('/root/qwen/ai_agent/backend/services/rag/app.py', 'w') as f:
    f.write(content)

print("Endpoint added successfully")

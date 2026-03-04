#!/usr/bin/env python3
from models.response_generator import ResponseGenerator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
from rag_component.document_loader import DocumentLoader

# Load actual document
loader = DocumentLoader()
docs = loader.load_document('/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_08795a8215d8_rst_gov_ru:8443/documents/r-1323565.1_881b0329.pdf')

document_content = ""
for doc in docs:
    document_content += doc.page_content + "\n"

print(f"Document content length: {len(document_content)} chars")
print(f"First 500 chars: {document_content[:500]}...")

# Test with prompt
rg = ResponseGenerator()
llm = rg._get_llm_instance(provider=RESPONSE_LLM_PROVIDER, model=RESPONSE_LLM_MODEL)

prompt = f"""Please split the following text into JSON chunks.

Respond with ONLY a JSON array in this format:
[{{"chunk_id": 1, "content": "text", "section": "", "title": ""}}]

Text to chunk:
{document_content[:5000]}

Your JSON response:"""

print(f"\nPrompt length: {len(prompt)} chars")

try:
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, 'content') else response
    print(f"\nResponse length: {len(content)} chars")
    print(f"Response preview: {content[:500]}...")
except Exception as e:
    print(f"Error: {e}")

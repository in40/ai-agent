#!/usr/bin/env python3
"""
Apply enhanced logging to document_loader.py
"""
import re

# Read the file
with open('/root/qwen/ai_agent/rag_component/document_loader.py', 'r') as f:
    content = f.read()

# 1. Add time import
content = content.replace(
    'import base64\n        import io\n        import re',
    'import base64\n        import io\n        import re\n        import time',
    1
)

# 2. Add debug logging for LLM client init
content = content.replace(
    'logger.info(f"Sending PDF to LLM: url={llm_base_url}, model={llm_model}, timeout={timeout}s")',
    '''logger.info(f"Sending PDF to LLM: url={llm_base_url}, model={llm_model}, timeout={timeout}s")
        logger.debug(f"LLM client init: base_url={llm_base_url}, api_key={'***' if api_key else None}")'''
)

# 3. Add image conversion debug logging
content = content.replace(
    'logger.info(f"Converted PDF to {len(images)} images")',
    '''logger.info(f"Converted PDF to {len(images)} images")
            logger.debug(f"Image DPI: 300, format: PNG")'''
)

# 4. Add prompt logging
content = content.replace(
    'user_prompt = "Convert this PDF page to clean markdown. Preserve all mathematical formulas and equations in LaTeX format. Output ONLY the markdown, nothing else."',
    '''user_prompt = "Convert this PDF page to clean markdown. Preserve all mathematical formulas and equations in LaTeX format. Output ONLY the markdown, nothing else."

        # Log prompts
        logger.info(f"LLM extraction prompt (system): {system_prompt[:200]}...")
        logger.info(f"LLM extraction prompt (user): {user_prompt[:200]}...")
        logger.debug(f"LLM extraction prompt (system, full): {system_prompt}")
        logger.debug(f"LLM extraction prompt (user, full): {user_prompt}")'''
)

# 5. Add timing for entire LLM extraction
content = content.replace(
    '# Process all pages and combine into single document',
    '# Time entire LLM extraction\n        llm_total_start = time.time()\n\n        # Process all pages and combine into single document'
)

# 6. Add per-page timing and detailed logging
old_page_loop = '''for page_idx, img in enumerate(images):
            page_num = start_page + page_idx
            logger.info(f"Processing page {page_num}")

            # Convert image to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            # Send to LLM with configurable timeout
            response = client.chat.completions.create('''

new_page_loop = '''for page_idx, img in enumerate(images):
            page_num = start_page + page_idx
            page_start = time.time()
            logger.info(f"Processing page {page_num}")

            # Convert image to base64
            img_start = time.time()
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            img_time = time.time() - img_start
            logger.debug(f"Page {page_num}: Image conversion {img_time:.2f}s ({len(img_base64)} bytes base64)")

            # Send to LLM with configurable timeout
            llm_start = time.time()
            logger.info(f"Page {page_num}: Sending image to LLM (base64 size: {len(img_base64)} bytes)")
            logger.debug(f"Page {page_num}: LLM request: model={llm_model}, max_tokens=32000, timeout={timeout}s")
            
            response = client.chat.completions.create('''

content = content.replace(old_page_loop, new_page_loop)

# 7. Add response logging
content = content.replace(
    'page_markdown = response.choices[0].message.content',
    '''llm_time = time.time() - llm_start
            logger.info(f"Page {page_num}: LLM call {llm_time:.2f}s")

            page_markdown = response.choices[0].message.content

            # Log response metadata
            logger.info(f"Page {page_num}: LLM response: {len(page_markdown)} chars")
            if hasattr(response, 'usage'):
                logger.debug(f"Page {page_num}: LLM response usage: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}, total={response.usage.total_tokens}")
            logger.debug(f"Page {page_num}: LLM response finish_reason: {response.choices[0].finish_reason}")
            logger.debug(f"Page {page_num}: LLM response (first 500 chars): {page_markdown[:500]}...")'''
)

# 8. Add cleanup timing
content = content.replace(
    '# Clean up LLM response - remove markdown code block wrappers\n            page_markdown = self._clean_llm_markdown(page_markdown)',
    '# Clean up LLM response - remove markdown code block wrappers\n            clean_start = time.time()\n            page_markdown = self._clean_llm_markdown(page_markdown)\n            clean_time = time.time() - clean_start\n            logger.debug(f"Page {page_num}: Markdown cleanup {clean_time:.2f}s")'
)

# 9. Add total timing at the end
content = content.replace(
    'logger.info(f"LLM extraction complete: {len(full_markdown)} total chars")',
    'llm_total_time = time.time() - llm_total_start\n        logger.info(f"LLM extraction complete: {len(full_markdown)} total chars in {llm_total_time:.2f}s ({len(full_markdown)/llm_total_time:.0f} chars/sec)")'
)

# Write the file back
with open('/root/qwen/ai_agent/rag_component/document_loader.py', 'w') as f:
    f.write(content)

print("✓ Enhanced logging applied to document_loader.py")

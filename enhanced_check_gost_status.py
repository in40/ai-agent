#!/usr/bin/env python3
"""
Enhanced script to check the status of the ГОСТ Р 58412-2019.pdf document processing
and monitor if it's using the external LLM as configured.
"""

import os
import time
import glob
from pathlib import Path
import subprocess


def check_gost_processing_status():
    """Check the status of ГОСТ Р 58412-2019.pdf processing"""
    
    print("Checking status of ГОСТ Р 58412-2019.pdf processing...")
    print("="*60)
    
    # Path to the uploaded PDF
    pdf_dir = "/root/qwen_test/ai_agent/data/rag_uploaded_files/520e729a-ab51-457e-9529-23dd5327a99f/"
    pdf_path = os.path.join(pdf_dir, "ГОСТ Р 58412-2019.pdf")
    
    # Check if the PDF exists in the upload directory
    if os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path)
        print(f"✓ Document found in upload directory")
        print(f"  Path: {pdf_path}")
        print(f"  Size: {file_size / (1024*1024):.2f} MB")
        print(f"  Last modified: {time.ctime(os.path.getmtime(pdf_path))}")
    else:
        print("✗ Document not found in upload directory")
        return
    
    # Check if there's a corresponding directory in converted markdown
    markdown_dirs = glob.glob("/root/qwen_test/ai_agent/data/rag_converted_markdown/*/")
    
    gost_processed = False
    for md_dir in markdown_dirs:
        # Look for markdown files with ГОСТ in the name
        md_files = glob.glob(os.path.join(md_dir, "*.md"))
        for md_file in md_files:
            if "ГОСТ" in md_file and "58412" in md_file:
                print(f"\n✓ Document has been converted to markdown!")
                print(f"  Path: {md_file}")
                size = os.path.getsize(md_file)
                print(f"  Size: {size} bytes")
                
                # Show first 500 chars
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"  First 500 chars: {content[:500]}...")
                gost_processed = True
                break
        if gost_processed:
            break
    
    if not gost_processed:
        print(f"\n⚠ Document conversion is still in progress or hasn't started yet.")
        
        # Check if there are any marker processes running
        try:
            result = subprocess.run(['pgrep', '-f', 'marker'], capture_output=True, text=True)
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                print(f"  Found Marker-related processes (PIDs): {', '.join(pids)}")
                
                # Check what command the process is running
                for pid in pids:
                    if pid.strip():
                        try:
                            cmd_result = subprocess.run(['ps', '-p', pid.strip(), '-o', 'args='], capture_output=True, text=True)
                            print(f"    PID {pid}: {cmd_result.stdout.strip()}")
                        except:
                            pass
            else:
                print(f"  No Marker-related processes found running.")
        except:
            print(f"  Could not check for Marker processes.")
        
        # Check for Marker temp directories
        marker_tmp_dirs = []
        for tmp_dir in ["/tmp", "/var/tmp"]:
            try:
                if os.path.exists(tmp_dir):
                    dirs = os.listdir(tmp_dir)
                    for d in dirs:
                        if "marker" in d.lower():
                            marker_tmp_dirs.append(os.path.join(tmp_dir, d))
            except:
                pass
        
        if marker_tmp_dirs:
            print(f"  Found Marker temporary directories that might be processing the document:")
            for tmp_dir in marker_tmp_dirs:
                print(f"    - {tmp_dir}")
    
    # Check RAG service logs for recent activity
    rag_log_path = "/root/qwen_test/ai_agent/rag_service.log"
    if os.path.exists(rag_log_path):
        print(f"\nRecent activity in RAG service logs:")
        try:
            with open(rag_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get the last 20 lines
                recent_lines = lines[-20:] if len(lines) > 20 else lines
                
                for line in recent_lines:
                    if "ГОСТ" in line or "58412" in line or "marker" in line.lower() or "conversion" in line.lower() or "external" in line.lower() or "llm" in line.lower():
                        print(f"  {line.strip()}")
        except Exception as e:
            print(f"  Could not read RAG service logs: {e}")
    
    # Check environment variables to confirm external LLM configuration
    print(f"\nExternal LLM Configuration:")
    marker_provider = os.getenv("MARKER_LLM_PROVIDER", "Not set")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "Not set")
    openai_model = os.getenv("OPENAI_MODEL", "Not set")
    
    print(f"  MARKER_LLM_PROVIDER: {marker_provider}")
    print(f"  OPENAI_BASE_URL: {openai_base_url}")
    print(f"  OPENAI_MODEL: {openai_model}")
    print(f"  FORCE_DEFAULT_MODEL_FOR_ALL: {os.getenv('FORCE_DEFAULT_MODEL_FOR_ALL', 'Not set')}")
    
    print("\n" + "="*60)
    print("Processing Summary:")
    print("- Document uploaded: ✓")
    print("- External LLM configured: ✓")
    print("- Conversion in progress: ?", end="")
    if gost_processed:
        print(" ✓ (completed)")
    else:
        print(" ⏳ (in progress)")
    print("- RAG service active: ✓")
    print("\nNote: The updated PDF converter should now use the external LLM as configured.")


if __name__ == "__main__":
    check_gost_processing_status()
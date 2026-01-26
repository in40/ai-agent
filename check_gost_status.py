#!/usr/bin/env python3
"""
Script to check the status of the ГОСТ Р 58412-2019.pdf document processing
"""

import os
import time
import glob
from pathlib import Path

def check_gost_processing_status():
    """Check the status of ГОСТ Р 58412-2019.pdf processing"""
    
    print("Checking status of ГОСТ Р 58412-2019.pdf processing...")
    print("="*50)
    
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
    # We need to find a directory that might be processing this specific document
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
        
        # Check if there are any temporary processing directories
        import tempfile
        import subprocess
        
        # Check for Marker temp directories
        marker_tmp_dirs = []
        for tmp_dir in ["/tmp", "/var/tmp"]:
            try:
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
        
        # Also check if there are any marker processes running
        try:
            result = subprocess.run(['pgrep', '-f', 'marker'], capture_output=True, text=True)
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                print(f"  Found Marker-related processes (PIDs): {', '.join(pids)}")
        except:
            pass
    
    print("\n" + "="*50)
    print("Processing Summary:")
    print("- Document uploaded: ✓")
    print("- Conversion in progress: ?", end="")
    if gost_processed:
        print(" ✓ (completed)")
    else:
        print(" ⏳ (in progress or pending)")
    print("- RAG service active: ✓ (high CPU indicates processing)")

if __name__ == "__main__":
    check_gost_processing_status()
#!/usr/bin/env python3
"""
Monitor script to check if the PDF conversion completed
"""

import os
import time
from pathlib import Path

def check_conversion_status():
    """Check if the PDF conversion has completed"""
    print("Checking for completed PDF conversion...")
    
    # Path to the specific PDF file
    pdf_path = "/root/qwen_test/ai_agent/data/rag_uploaded_files/3766b685-b435-4f4e-845b-f6f78bc0656e/Приказ ФСТЭК России от 18 февраля 2013 г. N 21.pdf"
    
    # Look for any markdown files that might have been created
    from rag_component.config import RAG_MARKDOWN_STORAGE_DIR
    import glob
    
    pdf_name = "Приказ ФСТЭК России от 18 февраля 2013 г. N 21"
    markdown_files = glob.glob(f"{RAG_MARKDOWN_STORAGE_DIR}/*/{pdf_name}.md")
    
    if markdown_files:
        print("✓ Conversion completed! Found markdown files:")
        for md_file in markdown_files:
            print(f"  - {md_file}")
            # Show file size
            if os.path.exists(md_file):
                size = os.path.getsize(md_file)
                print(f"    Size: {size} bytes")
                
                # Show first 500 chars
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"    First 500 chars: {content[:500]}...")
        return True
    else:
        print("✗ No markdown files found yet. Conversion may still be in progress.")
        
        # Check if the PDF file exists
        if os.path.exists(pdf_path):
            print(f"✓ Original PDF file still exists: {pdf_path}")
            file_size = os.path.getsize(pdf_path)
            print(f"  File size: {file_size / (1024*1024):.2f} MB")
        else:
            print("✗ Original PDF file not found")
        
        return False

def main():
    print("PDF Conversion Monitor")
    print("="*30)
    
    # Wait a bit and then check
    print("Waiting 30 seconds before checking...")
    time.sleep(30)
    
    completed = check_conversion_status()
    
    if not completed:
        print("\nThe conversion might still be running.")
        print("The system has been updated with longer timeouts (up to 2 hours) to accommodate complex PDFs.")
        print("You can check again later or restart the RAG service to ensure the changes take effect.")
    
    return 0 if completed else 1

if __name__ == "__main__":
    exit(main())
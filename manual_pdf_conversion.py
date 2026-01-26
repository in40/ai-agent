#!/usr/bin/env python3
"""
Manual conversion script to test the specific PDF file and measure processing time
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def manual_convert_pdf():
    """Manually convert the specific PDF file and measure processing time"""
    print("Starting manual conversion of 'Приказ ФСТЭК России от 18 февраля 2013 г. N 21.pdf'...")

    # Path to the specific PDF file
    pdf_path = "/root/qwen_test/ai_agent/data/rag_uploaded_files/3766b685-b435-4f4e-845b-f6f78bc0656e/Приказ ФСТЭК России от 18 февраля 2013 г. N 21.pdf"

    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return False

    print(f"Found PDF file: {pdf_path}")

    # Get file size
    file_size = os.path.getsize(pdf_path)
    print(f"File size: {file_size / (1024*1024):.2f} MB")

    try:
        from rag_component.pdf_converter import PDFToMarkdownConverter

        # Initialize the converter
        converter = PDFToMarkdownConverter()
        print("✓ PDFToMarkdownConverter initialized successfully")

        # Record start time
        start_time = time.time()
        print(f"Starting conversion at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Convert with a much longer timeout (30 minutes)
        markdown_content = converter.convert_pdf_to_markdown(pdf_path, timeout_seconds=1800)

        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        print(f"Conversion completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")

        if markdown_content:
            print(f"✓ PDF converted successfully. Content length: {len(markdown_content)} characters")

            # Save the markdown content to a file
            from rag_component.config import RAG_MARKDOWN_STORAGE_DIR
            import uuid

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

            print(f"✓ Created markdown file: {markdown_file_path}")

            # Show first 500 characters of content
            print(f"First 500 characters of content: {markdown_content[:500]}...")

            return True
        else:
            print("✗ PDF conversion returned empty content")
            return False

    except Exception as e:
        print(f"✗ Error during PDF conversion: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_existing_markdown():
    """Check if a markdown file already exists for this PDF"""
    print("\nChecking for existing markdown files...")
    
    # Look for any markdown files that might correspond to this PDF
    from rag_component.config import RAG_MARKDOWN_STORAGE_DIR
    import glob
    
    pdf_name = "Приказ ФСТЭК России от 18 февраля 2013 г. N 21"
    markdown_files = glob.glob(f"{RAG_MARKDOWN_STORAGE_DIR}/*/{pdf_name}.md")
    
    if markdown_files:
        print(f"Found existing markdown files:")
        for md_file in markdown_files:
            print(f"  - {md_file}")
            # Show file size
            if os.path.exists(md_file):
                size = os.path.getsize(md_file)
                print(f"    Size: {size} bytes")
    else:
        print("No existing markdown files found for this PDF.")

def main():
    print("Manual PDF Conversion Test")
    print("="*50)
    
    # Check for existing markdown files first
    check_existing_markdown()
    
    # Run the manual conversion
    success = manual_convert_pdf()
    
    if success:
        print("\n✓ Manual conversion completed successfully!")
        return 0
    else:
        print("\n✗ Manual conversion failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
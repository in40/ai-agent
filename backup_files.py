#!/usr/bin/env python3
"""
Backup script for PDF and MD files from document store.
Creates a timestamped backup directory and copies all files.
"""
import os
import shutil
from datetime import datetime

# Source and destination paths
DOC_STORE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"
BACKUP_BASE = "/root/qwen/ai_agent/backup"

# Create timestamped backup directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = os.path.join(BACKUP_BASE, f"backup_{timestamp}")
os.makedirs(backup_dir, exist_ok=True)

print("=" * 70)
print("DOCUMENT STORE BACKUP")
print("=" * 70)
print(f"Source: {DOC_STORE_PATH}")
print(f"Destination: {backup_dir}")
print()

# Count and copy files
pdf_count = 0
md_count = 0
total_size = 0

for filename in os.listdir(DOC_STORE_PATH):
    src_path = os.path.join(DOC_STORE_PATH, filename)
    dst_path = os.path.join(backup_dir, filename)
    
    if filename.endswith('.pdf'):
        shutil.copy2(src_path, dst_path)
        pdf_count += 1
        total_size += os.path.getsize(src_path)
        print(f"  [PDF] {filename}")
    elif filename.endswith('.md'):
        shutil.copy2(src_path, dst_path)
        md_count += 1
        total_size += os.path.getsize(src_path)
        print(f"  [MD]  {filename}")

print()
print("=" * 70)
print("BACKUP SUMMARY")
print("=" * 70)
print(f"PDF files backed up: {pdf_count}")
print(f"MD files backed up:  {md_count}")
print(f"Total files:         {pdf_count + md_count}")
print(f"Total size:          {total_size / 1024 / 1024:.2f} MB")
print(f"Backup location:     {backup_dir}")
print("=" * 70)

# Create manifest file
manifest_path = os.path.join(backup_dir, "BACKUP_MANIFEST.txt")
with open(manifest_path, 'w') as f:
    f.write(f"Backup Manifest\n")
    f.write(f"=" * 60 + "\n")
    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    f.write(f"Source: {DOC_STORE_PATH}\n")
    f.write(f"PDF files: {pdf_count}\n")
    f.write(f"MD files: {md_count}\n")
    f.write(f"Total size: {total_size / 1024 / 1024:.2f} MB\n")
    f.write(f"=" * 60 + "\n\n")
    f.write("Files:\n")
    f.write("-" * 60 + "\n")
    for filename in sorted(os.listdir(backup_dir)):
        if filename != "BACKUP_MANIFEST.txt":
            filepath = os.path.join(backup_dir, filename)
            size = os.path.getsize(filepath)
            f.write(f"  {filename} ({size:,} bytes)\n")

print(f"\nManifest saved to: {manifest_path}")

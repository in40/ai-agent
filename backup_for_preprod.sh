#!/bin/bash
#
# Pre-Production Backup Script
# Moves PDF files from downloads and document_store to backup location
# Creates recovery manifest for each moved file
#
# Usage: ./backup_for_preprod.sh
#

set -e

BACKUP_BASE="/root/qwen/ai_agent/preprod_backup_$(date +%Y%m%d_%H%M%S)"
DOWNLOADS_DIR="/root/qwen/ai_agent/downloads"
DOCUMENT_STORE_DIR="/root/qwen/ai_agent/backend/data/document_store"
DOCSTORE_MCP_DIR="/root/qwen/ai_agent/document-store-mcp-server/data/ingested"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Pre-Production Backup Script                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Backup location: $BACKUP_BASE"
echo ""

# Create backup directory structure
mkdir -p "$BACKUP_BASE/downloads"
mkdir -p "$BACKUP_BASE/document_store"
mkdir -p "$BACKUP_BASE/document_store_mcp"
mkdir -p "$BACKUP_BASE/manifests"

# Initialize manifest
MANIFEST_FILE="$BACKUP_BASE/BACKUP_MANIFEST.txt"
RECOVERY_SCRIPT="$BACKUP_BASE/RECOVER_FILES.sh"

cat > "$MANIFEST_FILE" << EOF
═══════════════════════════════════════════════════════════════
PRE-PRODUCTION BACKUP MANIFEST
═══════════════════════════════════════════════════════════════
Backup Date: $(date '+%Y-%m-%d %H:%M:%S')
Backup Location: $BACKUP_BASE
Created By: $(whoami)
Host: $(hostname)

PURPOSE:
This backup was created before running pre-production tests.
Files were moved (not copied) to preserve disk space.

TO RECOVER:
Run the recovery script: bash $RECOVERY_SCRIPT

OR manually move files back from:
  Downloads:      $BACKUP_BASE/downloads/
  Document Store: $BACKUP_BASE/document_store/

═══════════════════════════════════════════════════════════════
BACKED UP FILES:
═══════════════════════════════════════════════════════════════

EOF

cat > "$RECOVERY_SCRIPT" << 'RECOVERY_HEADER'
#!/bin/bash
#
# Recovery Script for Pre-Production Backup
# This script moves files back to their original locations
#

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         File Recovery Script                                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Confirm recovery
read -p "This will move files back to their original locations. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled."
    exit 0
fi

echo ""
echo "Starting recovery..."
echo ""

RECOVERY_HEADER

# Counter for files
DOWNLOADS_COUNT=0
DOCSTORE_COUNT=0
TOTAL_SIZE=0

# Function to backup and create manifest
backup_file() {
    local source_file="$1"
    local backup_dir="$2"
    local category="$3"
    
    if [ -f "$source_file" ]; then
        local filename=$(basename "$source_file")
        local filesize=$(stat -c%s "$source_file" 2>/dev/null || echo "0")
        local filesize_human=$(du -h "$source_file" 2>/dev/null | cut -f1)
        local md5sum=$(md5sum "$source_file" 2>/dev/null | cut -d' ' -f1)
        local mtime=$(stat -c%y "$source_file" 2>/dev/null | cut -d'.' -f1)
        
        # Move file to backup
        mv "$source_file" "$backup_dir/"
        
        # Create individual manifest for this file
        local manifest_name="${filename}.manifest"
        cat > "$BACKUP_BASE/manifests/$manifest_name" << EOF
File: $filename
Original Path: $source_file
Backup Path: $backup_dir/$filename
Size: $filesize_human ($filesize bytes)
MD5: $md5sum
Modified: $mtime
Backup Date: $(date '+%Y-%m-%d %H:%M:%S')
Category: $category
EOF
        
        # Add to main manifest
        echo "[$category] $filename" >> "$MANIFEST_FILE"
        echo "  Original: $source_file" >> "$MANIFEST_FILE"
        echo "  Backup:   $backup_dir/$filename" >> "$MANIFEST_FILE"
        echo "  Size:     $filesize_human" >> "$MANIFEST_FILE"
        echo "  MD5:      $md5sum" >> "$MANIFEST_FILE"
        echo "" >> "$MANIFEST_FILE"
        
        # Add to recovery script
        echo "if [ -f \"\$SCRIPT_DIR/downloads/$filename\" ]; then" >> "$RECOVERY_SCRIPT"
        echo "    echo \"Restoring: $filename\"" >> "$RECOVERY_SCRIPT"
        echo "    mv \"\$SCRIPT_DIR/downloads/$filename\" \"$source_file\"" >> "$RECOVERY_SCRIPT"
        echo "fi" >> "$RECOVERY_SCRIPT"
        echo "" >> "$RECOVERY_SCRIPT"
        
        TOTAL_SIZE=$((TOTAL_SIZE + filesize))
        
        if [ "$category" = "Downloads" ]; then
            DOWNLOADS_COUNT=$((DOWNLOADS_COUNT + 1))
        else
            DOCSTORE_COUNT=$((DOCSTORE_COUNT + 1))
        fi
        
        echo "  ✓ $filename ($filesize_human)"
    fi
}

# Backup Downloads
echo "📥 Backing up Downloads..."
echo ""
for pdf in "$DOWNLOADS_DIR"/*.pdf; do
    if [ -f "$pdf" ]; then
        backup_file "$pdf" "$BACKUP_BASE/downloads" "Downloads"
    fi
done

# Backup Document Store (if exists)
if [ -d "$DOCUMENT_STORE_DIR" ]; then
    echo ""
    echo "📚 Backing up Document Store..."
    echo ""
    for pdf in "$DOCUMENT_STORE_DIR"/*.pdf; do
        if [ -f "$pdf" ]; then
            backup_file "$pdf" "$BACKUP_BASE/document_store" "Document Store"
        fi
    done
fi

# Backup Document Store MCP Server (if exists)
if [ -d "$DOCSTORE_MCP_DIR" ]; then
    echo ""
    echo "🗄️  Backing up Document Store MCP Server..."
    echo ""
    # Find all PDFs recursively in the ingested directory
    while IFS= read -r -d '' pdf; do
        backup_file "$pdf" "$BACKUP_BASE/document_store_mcp" "Document Store MCP"
    done < <(find "$DOCSTORE_MCP_DIR" -name "*.pdf" -type f -print0 2>/dev/null)
fi

# Finalize manifest
cat >> "$MANIFEST_FILE" << EOF

═══════════════════════════════════════════════════════════════
SUMMARY:
═══════════════════════════════════════════════════════════════
Downloads backed up:     $DOWNLOADS_COUNT files
Document Store backed up: $DOCSTORE_COUNT files
Total files:             $((DOWNLOADS_COUNT + DOCSTORE_COUNT))
Total size:              $(numfmt --to=iec-i --suffix=B $TOTAL_SIZE 2>/dev/null || echo "$TOTAL_SIZE bytes")

Backup completed: $(date '+%Y-%m-%d %H:%M:%S')
═══════════════════════════════════════════════════════════════
EOF

# Finalize recovery script
cat >> "$RECOVERY_SCRIPT" << 'RECOVERY_FOOTER'

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Recovery complete!"
echo "═══════════════════════════════════════════════════════════════"
RECOVERY_FOOTER

chmod +x "$RECOVERY_SCRIPT"

# Print summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "BACKUP COMPLETE"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Summary:"
echo "   Downloads backed up:     $DOWNLOADS_COUNT files"
echo "   Document Store backed up: $DOCSTORE_COUNT files"
echo "   Total files:             $((DOWNLOADS_COUNT + DOCSTORE_COUNT))"
echo "   Total size:              $(numfmt --to=iec-i --suffix=B $TOTAL_SIZE 2>/dev/null || echo "$TOTAL_SIZE bytes")"
echo ""
echo "📁 Backup location: $BACKUP_BASE"
echo ""
echo "📄 Files created:"
echo "   - BACKUP_MANIFEST.txt  (full manifest)"
echo "   - RECOVER_FILES.sh     (recovery script)"
echo "   - manifests/*.manifest (individual file manifests)"
echo ""
echo "🔄 To recover files:"
echo "   bash $RECOVERY_SCRIPT"
echo ""
echo "═══════════════════════════════════════════════════════════════"

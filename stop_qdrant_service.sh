#!/bin/bash

# Script to stop Qdrant service and optionally revert to previous vector store configuration
# This script handles stopping the Qdrant container and can restore previous settings

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
BACKUP_ENV_PATTERN="$SCRIPT_DIR/.env.backup.*"

echo "Stopping Qdrant service for AI Agent..."
echo "Project directory: $SCRIPT_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$@" > /dev/null 2>&1
}

# Function to stop Qdrant service
stop_qdrant() {
    echo "Stopping Qdrant service with Docker Compose..."
    
    cd "$SCRIPT_DIR"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        echo "Error: docker-compose.yml not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Check if Qdrant container is running
    if docker ps | grep -q qdrant; then
        # Stop and remove the Qdrant service
        docker-compose down
        
        # Wait a moment for the service to stop
        sleep 5
        
        # Verify the container is stopped
        if ! docker ps | grep -q qdrant; then
            echo "✓ Qdrant service stopped successfully!"
        else
            echo "⚠ Qdrant service may still be running"
        fi
    else
        echo "ℹ Qdrant service was not running"
    fi
}

# Function to list available backup files
list_backups() {
    echo "Available backup files:"
    local backups=($BACKUP_ENV_PATTERN)
    if [ ${#backups[@]} -gt 0 ] && [ -e "${backups[0]}" ]; then
        for backup in "${backups[@]}"; do
            if [ -e "$backup" ]; then
                local timestamp=$(basename "$backup" | sed 's/.env.backup.//')
                echo "  - $backup (created: ${timestamp})"
            fi
        done
    else
        echo "  No backup files found"
    fi
}

# Function to restore previous environment configuration
restore_previous_config() {
    echo "Restoring previous vector store configuration..."
    
    local backups=($BACKUP_ENV_PATTERN)
    local latest_backup=""
    
    # Find the most recent backup
    if [ ${#backups[@]} -gt 0 ]; then
        # Sort backups by modification time to get the most recent one
        latest_backup=$(ls -t $BACKUP_ENV_PATTERN 2>/dev/null | head -n1)
    fi
    
    if [ -n "$latest_backup" ] && [ -e "$latest_backup" ]; then
        echo "Found backup file: $latest_backup"
        
        # Ask user if they want to restore the backup
        read -p "Do you want to restore the backup configuration? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Restoring configuration from $latest_backup..."
            cp "$latest_backup" "$ENV_FILE"
            echo "✓ Previous configuration restored"
        else
            echo "Skipping configuration restoration"
        fi
    else
        # If no backup exists, ask if they want to remove Qdrant settings
        echo "No backup configuration found."
        read -p "Do you want to remove Qdrant-specific settings from .env? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -f "$ENV_FILE" ]; then
                # Remove or comment out Qdrant-specific settings
                sed -i.bak '/^RAG_VECTOR_STORE_TYPE=qdrant$/d' "$ENV_FILE"
                sed -i.bak '/^RAG_QDRANT_URL=/d' "$ENV_FILE"
                sed -i.bak '/^RAG_QDRANT_API_KEY=/d' "$ENV_FILE"
                
                # If RAG_VECTOR_STORE_TYPE was commented out or removed, ensure it's set to default (chroma)
                if ! grep -q "^RAG_VECTOR_STORE_TYPE=" "$ENV_FILE"; then
                    echo "# Default vector store configuration" >> "$ENV_FILE"
                    echo "RAG_VECTOR_STORE_TYPE=chroma" >> "$ENV_FILE"
                    echo "Added default RAG_VECTOR_STORE_TYPE=chroma to .env"
                fi
                
                # Clean up temporary backup files
                rm -f "$ENV_FILE.bak"
                
                echo "✓ Qdrant-specific settings removed from .env"
            else
                echo "ℹ .env file does not exist, nothing to modify"
            fi
        fi
    fi
}

# Function to check Qdrant status
check_qdrant_status() {
    echo "Checking Qdrant service status..."
    
    if docker ps | grep -q qdrant; then
        echo "⚠ Qdrant service is still running"
        echo "Container details:"
        docker ps --filter "name=qdrant" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    elif docker ps -a | grep -q qdrant; then
        echo "ℹ Qdrant container exists but is not running"
        echo "Container details:"
        docker ps -a --filter "name=qdrant" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    else
        echo "✓ Qdrant container does not exist"
    fi
}

# Function to clean up Qdrant volumes (optional)
cleanup_volumes() {
    read -p "Do you want to remove Qdrant data volumes? (This will delete all stored vectors!) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing Qdrant data volumes..."
        docker volume prune -f --filter "label=com.docker.compose.service=qdrant" 2>/dev/null || true
        echo "✓ Qdrant data volumes cleaned up"
    else
        echo "Keeping Qdrant data volumes"
    fi
}

# Main execution
main() {
    echo "==========================================="
    echo "Qdrant Shutdown for AI Agent"
    echo "==========================================="
    
    # Check current status
    check_qdrant_status
    
    # Stop Qdrant service
    stop_qdrant
    
    # Ask if user wants to restore previous configuration
    echo ""
    list_backups
    echo ""
    
    read -p "Do you want to restore previous vector store configuration? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Skipping configuration restoration"
    else
        restore_previous_config
    fi
    
    # Ask if user wants to clean up volumes
    echo ""
    read -p "Do you want to clean up Qdrant data volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_volumes
    fi
    
    echo ""
    echo "==========================================="
    echo "Qdrant Shutdown Complete!"
    echo "==========================================="
    echo ""
    echo "Current status:"
    check_qdrant_status
    echo ""
    echo "Next steps:"
    echo "1. Qdrant service has been stopped"
    echo "2. Configuration changes have been reverted as requested"
    echo "3. Restart your AI Agent services to apply any configuration changes"
    echo ""
    echo "To start Qdrant again: ./start_qdrant_full_setup.sh"
    echo "==========================================="
}

# Run the main function
main "$@"
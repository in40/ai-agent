#!/bin/bash

# Comprehensive script to start Qdrant service and configure the AI agent to use it
# This script handles Docker installation, Qdrant startup, and environment configuration

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

echo "Setting up Qdrant vector database for AI Agent..."
echo "Project directory: $SCRIPT_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$@" > /dev/null 2>&1
}

# Function to run docker compose command (handles both old and new syntax)
run_docker_compose() {
    if command_exists docker-compose; then
        docker-compose "$@"
    elif docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    else
        echo "Error: Neither docker-compose nor docker compose is available"
        exit 1
    fi
}

# Function to install Docker if not present
install_docker() {
    echo "Checking for Docker installation..."

    if command_exists docker; then
        echo "✓ Docker is already installed"
        return 0
    fi

    echo "Docker not found. Installing Docker..."

    # Detect OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VERSION_ID=$VERSION_ID
        VERSION_CODENAME=$VERSION_CODENAME
    else
        echo "✗ Cannot detect OS. Please install Docker manually."
        exit 1
    fi

    # Install Docker based on OS
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # For Debian 13 (Trixie) and other Debian-based systems
        echo "Detected Debian-based system: $OS $VERSION_ID ($VERSION_CODENAME)"

        # Update package index
        apt-get update

        # Install required packages
        apt-get install -y ca-certificates curl gnupg lsb-release

        # Add Docker's official GPG key
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg

        # Determine the codename for Debian 13 (trixie) or fallback to automatic detection
        if [ "$VERSION_CODENAME" = "trixie" ]; then
            # For Debian 13 (trixie), use the specific codename
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
              trixie stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        else
            # For other versions, use the detected codename
            echo \
              "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
              $(. /etc/os-release && echo $VERSION_CODENAME) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        fi

        # Update package index again after adding Docker repo
        apt-get update

        # Install Docker packages
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

        # Start and enable Docker service
        systemctl start docker
        systemctl enable docker
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        systemctl start docker
        systemctl enable docker
    else
        echo "Unsupported OS. Please install Docker manually."
        exit 1
    fi

    # Add current user to docker group to avoid needing sudo
    usermod -aG docker ${USER:-$(whoami)} || true

    echo "✓ Docker installed successfully"
}

# Function to install Docker Compose if not present
install_docker_compose() {
    echo "Checking for Docker Compose installation..."

    if command_exists docker-compose || (docker --help | grep -q "compose"); then
        echo "✓ Docker Compose is already installed"
        return 0
    fi

    echo "Docker Compose not found. Installing Docker Compose plugin..."

    # For newer Docker installations, Compose is usually a plugin
    if command_exists docker; then
        # Try to install compose plugin for Debian 13
        apt-get install -y docker-compose-plugin 2>/dev/null || {
            echo "Could not install docker-compose-plugin via package manager"
            echo "Trying alternative installation method..."

            # Alternative: Install as standalone binary
            DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
            mkdir -p $DOCKER_CONFIG/cli-plugins
            curl -SL https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m) -o $DOCKER_CONFIG/cli-plugins/docker-compose
            chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
        }
    fi

    if command_exists docker-compose || (docker --help | grep -q "compose"); then
        echo "✓ Docker Compose installed successfully"
    else
        echo "✗ Failed to install Docker Compose"
        exit 1
    fi
}

# Function to check if Docker daemon is running
check_docker_running() {
    if ! docker info &> /dev/null; then
        echo "Docker daemon is not running. Starting Docker..."
        systemctl start docker || sudo systemctl start docker
        sleep 5  # Give Docker some time to start
    fi
    
    if ! docker info &> /dev/null; then
        echo "✗ Docker daemon is still not running. Please start Docker manually."
        exit 1
    fi
    
    echo "✓ Docker daemon is running"
}

# Function to start Qdrant service
start_qdrant() {
    echo "Starting Qdrant service with Docker Compose..."
    
    cd "$SCRIPT_DIR"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        echo "Error: docker-compose.yml not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Start Qdrant service
    run_docker_compose up -d qdrant
    
    # Wait a moment for the service to start
    sleep 10
    
    # Check if the Qdrant container is running
    if docker ps | grep -q qdrant; then
        echo "✓ Qdrant service started successfully!"
        echo "Qdrant is now running on:"
        echo "  - REST API: http://localhost:6333"
        echo "  - gRPC: http://localhost:6334"

        # Show the logs for a few seconds to verify it's running properly
        echo ""
        echo "Recent Qdrant logs:"
        docker logs qdrant --tail 10
    else
        echo "✗ Failed to start Qdrant service"
        echo "Check the Docker Compose configuration or logs for errors:"
        run_docker_compose logs qdrant
        exit 1
    fi
}

# Function to update environment to use Qdrant
configure_qdrant_in_env() {
    echo "Configuring AI Agent to use Qdrant..."
    
    # Backup existing .env file if it exists
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Backed up existing .env file"
    fi
    
    # Update or add the RAG_VECTOR_STORE_TYPE setting
    if [ -f "$ENV_FILE" ]; then
        # If the file exists, update the setting if it's present
        if grep -q "^RAG_VECTOR_STORE_TYPE=" "$ENV_FILE"; then
            sed -i 's/^RAG_VECTOR_STORE_TYPE=.*/RAG_VECTOR_STORE_TYPE=qdrant/' "$ENV_FILE"
            echo "Updated RAG_VECTOR_STORE_TYPE to qdrant in .env"
        else
            # Append the setting if it doesn't exist
            echo "RAG_VECTOR_STORE_TYPE=qdrant" >> "$ENV_FILE"
            echo "Added RAG_VECTOR_STORE_TYPE=qdrant to .env"
        fi
    else
        # Create a new .env file with the setting
        echo "# Vector store configuration" > "$ENV_FILE"
        echo "RAG_VECTOR_STORE_TYPE=qdrant" >> "$ENV_FILE"
        echo "Created .env file with RAG_VECTOR_STORE_TYPE=qdrant"
    fi
    
    # Also ensure Qdrant-specific settings are in place
    if ! grep -q "^RAG_QDRANT_URL=" "$ENV_FILE"; then
        echo "RAG_QDRANT_URL=http://localhost:6333" >> "$ENV_FILE"
        echo "Added RAG_QDRANT_URL to .env"
    fi
    
    if ! grep -q "^RAG_QDRANT_API_KEY=" "$ENV_FILE"; then
        echo "RAG_QDRANT_API_KEY=" >> "$ENV_FILE"
        echo "Added RAG_QDRANT_API_KEY to .env (empty by default)"
    fi
    
    echo "✓ AI Agent configured to use Qdrant"
}

# Function to verify Qdrant connectivity
verify_qdrant_connectivity() {
    echo "Verifying Qdrant connectivity..."
    
    # Wait a bit more for Qdrant to be fully ready
    sleep 10
    
    # Check if we can reach the Qdrant health endpoint
    if curl -sf http://localhost:6333/health > /dev/null 2>&1; then
        echo "✓ Qdrant is accessible at http://localhost:6333"
        
        # Print version info
        VERSION_INFO=$(curl -s http://localhost:6333/version)
        echo "Qdrant version info: $VERSION_INFO"
    else
        echo "! Warning: Could not reach Qdrant at http://localhost:6333"
        echo "  This might be normal if Qdrant is still starting up."
        echo "  Please wait a few more seconds and try accessing Qdrant."
    fi
}

# Main execution
main() {
    echo "==========================================="
    echo "Qdrant Setup for AI Agent"
    echo "==========================================="
    
    # Install Docker if needed
    install_docker
    
    # Install Docker Compose if needed
    install_docker_compose
    
    # Check if Docker daemon is running
    check_docker_running
    
    # Start Qdrant service
    start_qdrant
    
    # Configure environment to use Qdrant
    configure_qdrant_in_env
    
    # Verify connectivity
    verify_qdrant_connectivity
    
    echo ""
    echo "==========================================="
    echo "Qdrant Setup Complete!"
    echo "==========================================="
    echo ""
    echo "Next steps:"
    echo "1. The Qdrant service is now running in the background"
    echo "2. Your AI Agent is configured to use Qdrant as the vector store"
    echo "3. Restart your AI Agent services to apply the changes"
    echo ""
    echo "To stop Qdrant: docker-compose down"
    echo "To restart Qdrant: docker-compose up -d qdrant"
    echo "To check status: docker-compose ps"
    echo ""
    echo "For troubleshooting, check: docker-compose logs qdrant"
    echo "==========================================="
}

# Run the main function
main "$@"

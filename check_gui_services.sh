#!/bin/bash
# Script to check the status of LangGraph Editor GUI services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Checking status of LangGraph Editor GUI services...${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to get PID of process using a port
get_pid_by_port() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null
}

# Function to get process name by PID
get_process_name_by_pid() {
    local pid=$1
    ps -p $pid -o comm= 2>/dev/null || echo "Unknown"
}

# Check each service
services=(
    "3000:React Editor"
    "5001:Workflow API"
    "8000:LangGraph Studio"
    "8501:Streamlit App"
)

running_count=0
total_services=${#services[@]}

echo -e "${GREEN}Service Status:${NC}"
for service in "${services[@]}"; do
    port=${service%:*}
    name=${service#*:}
    
    if check_port $port; then
        pid=$(get_pid_by_port $port)
        process_name=$(get_process_name_by_pid $pid)
        echo -e "  ${GREEN}✓ $name${NC} - Port $port (PID: $pid, Process: $process_name)"
        ((running_count++))
    else
        echo -e "  ${RED}✗ $name${NC} - Port $port (Not running)"
    fi
done

echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  Total services: $total_services"
echo "  Running: $running_count"
echo "  Stopped: $((total_services - running_count))"

if [ $running_count -eq $total_services ]; then
    echo -e "${GREEN}All services are running.${NC}"
elif [ $running_count -eq 0 ]; then
    echo -e "${RED}No services are running.${NC}"
else
    echo -e "${YELLOW}Some services are running.${NC}"
fi

echo -e "${GREEN}"
echo "==================================================================="
echo "Status check completed."
echo "==================================================================="
echo -e "${NC}"
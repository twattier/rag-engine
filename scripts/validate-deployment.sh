#!/bin/bash
#
# RAG Engine Deployment Validation Script
#
# This script validates that RAG Engine can be deployed successfully
# by checking prerequisites, starting services, and verifying health.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
NEO4J_BROWSER_URL="${NEO4J_BROWSER_URL:-http://localhost:7474}"
MAX_WAIT_TIME=120  # seconds
CHECK_INTERVAL=5   # seconds

# Function to print colored messages
print_info() { echo -e "${BLUE}ℹ ${NC}$1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_header() { echo -e "\n${BLUE}$1${NC}\n$(printf '=%.0s' {1..60})"; }

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check port availability
is_port_available() {
    local port=$1
    if command_exists lsof; then
        ! lsof -i :"$port" >/dev/null 2>&1
    elif command_exists netstat; then
        ! netstat -tuln | grep ":$port " >/dev/null 2>&1
    else
        # Fallback: try to connect
        ! timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$port" 2>/dev/null
    fi
}

# Function to wait for service health
wait_for_health() {
    local service_name=$1
    local health_url=$2
    local max_wait=$3

    print_info "Waiting for $service_name to be healthy (max ${max_wait}s)..."

    elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if curl -s -f "$health_url" > /dev/null 2>&1; then
            print_success "$service_name is healthy"
            return 0
        fi
        sleep $CHECK_INTERVAL
        elapsed=$((elapsed + CHECK_INTERVAL))
        printf "."
    done

    echo ""
    print_error "$service_name failed to become healthy within ${max_wait}s"
    return 1
}

# Main validation flow
main() {
    print_header "RAG Engine Deployment Validation"

    # Step 1: Check prerequisites
    print_header "Step 1: Checking Prerequisites"

    # Check Docker
    if ! command_exists docker; then
        print_error "Docker is not installed"
        print_info "Install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker installed (version: $DOCKER_VERSION)"

    # Check Docker Compose
    if ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose V2 is not available"
        print_info "Install Docker Compose V2: https://docs.docker.com/compose/install/"
        exit 1
    fi
    COMPOSE_VERSION=$(docker compose version --short)
    print_success "Docker Compose V2 installed (version: $COMPOSE_VERSION)"

    # Check Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        print_info "Start Docker Desktop or run: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker daemon is running"

    # Check available ports
    print_info "Checking required ports..."

    PORTS_TO_CHECK="7474 7687 8000"
    PORTS_IN_USE=""

    for port in $PORTS_TO_CHECK; do
        if ! is_port_available "$port"; then
            PORTS_IN_USE="$PORTS_IN_USE $port"
        fi
    done

    if [ -n "$PORTS_IN_USE" ]; then
        print_warning "Ports in use:$PORTS_IN_USE"
        print_info "You can change ports in .env file to avoid conflicts"
        print_info "See docs/deployment-guide.md for instructions"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "All required ports are available"
    fi

    # Check system resources
    print_info "Checking system resources..."

    if command_exists free; then
        TOTAL_RAM_GB=$(free -g | awk '/^Mem:/ {print $2}')
        if [ "$TOTAL_RAM_GB" -lt 8 ]; then
            print_warning "System has only ${TOTAL_RAM_GB}GB RAM (8GB minimum, 16GB recommended)"
        else
            print_success "System has ${TOTAL_RAM_GB}GB RAM"
        fi
    fi

    # Step 2: Check configuration
    print_header "Step 2: Checking Configuration"

    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_info "Creating .env from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env file created"
            print_warning "IMPORTANT: Edit .env to set your passwords and API keys"
        else
            print_error ".env.example not found. Cannot create .env file."
            exit 1
        fi
    else
        print_success ".env file exists"
    fi

    # Check for default passwords
    if grep -q "neo4j/password" .env 2>/dev/null || grep -q "change-me" .env 2>/dev/null; then
        print_warning "Found default passwords in .env file"
        print_info "SECURITY: Change default passwords before production deployment"
    fi

    # Step 3: Start services
    print_header "Step 3: Starting Services"

    print_info "Running: docker compose up -d"

    if docker compose up -d; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        print_info "Check logs with: docker compose logs"
        exit 1
    fi

    # Step 4: Wait for services to be healthy
    print_header "Step 4: Waiting for Services to be Healthy"

    # Wait for API service
    if ! wait_for_health "API Service" "${API_URL}/health" $MAX_WAIT_TIME; then
        print_error "API service health check failed"
        print_info "Check logs: docker compose logs api"
        exit 1
    fi

    # Wait for Neo4j Browser
    if ! wait_for_health "Neo4j Browser" "${NEO4J_BROWSER_URL}" $MAX_WAIT_TIME; then
        print_error "Neo4j Browser health check failed"
        print_info "Check logs: docker compose logs neo4j"
        exit 1
    fi

    # Step 5: Verify endpoints
    print_header "Step 5: Verifying Endpoints"

    # Check API health endpoint
    print_info "Testing API health endpoint..."
    health_response=$(curl -s "${API_URL}/health")
    if echo "$health_response" | grep -q '"status".*"healthy"'; then
        print_success "API health check passed"
    else
        print_error "API health check failed"
        echo "Response: $health_response"
        exit 1
    fi

    # Check API docs
    print_info "Testing API documentation..."
    if curl -s -f "${API_URL}/docs" > /dev/null; then
        print_success "API documentation accessible"
    else
        print_warning "API documentation may not be accessible"
    fi

    # Check OpenAPI schema
    print_info "Testing OpenAPI schema..."
    if curl -s -f "${API_URL}/openapi.json" > /dev/null; then
        print_success "OpenAPI schema accessible"
    else
        print_warning "OpenAPI schema may not be accessible"
    fi

    # Step 6: Summary
    print_header "Deployment Validation Summary"

    echo ""
    print_success "RAG Engine deployed successfully!"
    echo ""
    echo "Access points:"
    echo "  - API Documentation: ${API_URL}/docs"
    echo "  - API Health Check:  ${API_URL}/health"
    echo "  - Neo4j Browser:     ${NEO4J_BROWSER_URL}"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:         docker compose logs -f"
    echo "  - Stop services:     docker compose down"
    echo "  - Restart services:  docker compose restart"
    echo ""
    print_info "See docs/deployment-guide.md for full documentation"
    echo ""
}

# Handle script interruption
trap 'echo ""; print_warning "Validation interrupted"; exit 130' INT

# Run main function
main

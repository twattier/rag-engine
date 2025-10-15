#!/bin/bash
# API health check test script for RAG Engine

set -e

API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT=30
INTERVAL=2

echo "Testing RAG Engine API at ${API_URL}..."

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3

    echo -n "Testing ${description}... "

    response=$(curl -s -w "\n%{http_code}" "${API_URL}${endpoint}")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -eq "$expected_status" ]; then
        echo "✓ PASS (HTTP $http_code)"
        echo "  Response: $body"
        return 0
    else
        echo "✗ FAIL (HTTP $http_code, expected $expected_status)"
        echo "  Response: $body"
        return 1
    fi
}

# Wait for API to be ready
echo "Waiting for API to be ready (timeout: ${TIMEOUT}s)..."
elapsed=0
while [ $elapsed -lt $TIMEOUT ]; do
    if curl -s -f "${API_URL}/health" > /dev/null 2>&1; then
        echo "✓ API is ready"
        break
    fi
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
    echo "  Waiting... (${elapsed}s / ${TIMEOUT}s)"
done

if [ $elapsed -ge $TIMEOUT ]; then
    echo "✗ Timeout waiting for API to be ready"
    exit 1
fi

# Run tests
echo ""
echo "Running API tests..."
echo "===================="

test_endpoint "/" 200 "Root endpoint"
echo ""

test_endpoint "/health" 200 "Health check endpoint"
echo ""

test_endpoint "/docs" 200 "Swagger UI documentation"
echo ""

test_endpoint "/openapi.json" 200 "OpenAPI schema"
echo ""

# Test health check response structure and values
echo -n "Validating health check response structure and values... "
health_response=$(curl -s "${API_URL}/health")

# Check required fields exist
if echo "$health_response" | grep -q '"status"' && \
   echo "$health_response" | grep -q '"service"' && \
   echo "$health_response" | grep -q '"version"' && \
   echo "$health_response" | grep -q '"timestamp"'; then

    # Validate specific field values
    if echo "$health_response" | grep -q '"status":\s*"healthy"' && \
       echo "$health_response" | grep -q '"service":\s*"rag-engine-api"' && \
       echo "$health_response" | grep -q '"version":\s*"0.1.0"'; then
        echo "✓ PASS"
        echo "  Response contains required fields with correct values"
        echo "  - status: healthy"
        echo "  - service: rag-engine-api"
        echo "  - version: 0.1.0"
        echo "  - timestamp: present"
    else
        echo "✗ FAIL"
        echo "  Fields present but values incorrect"
        echo "  Response: $health_response"
        exit 1
    fi
else
    echo "✗ FAIL"
    echo "  Missing required fields in response"
    echo "  Response: $health_response"
    exit 1
fi

echo ""
echo "===================="
echo "✅ All API health tests passed!"
echo ""
echo "API is ready at: ${API_URL}"
echo "  - Swagger UI: ${API_URL}/docs"
echo "  - ReDoc: ${API_URL}/redoc"
echo "  - Health Check: ${API_URL}/health"

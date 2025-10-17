#!/bin/bash
#
# Test Data Cleanup Script for RAG Engine
#
# This script provides flexible cleanup options for test data accumulated
# during development and testing. Supports granular control over what gets
# deleted (database documents, filesystem files, or both).
#
# Usage:
#   # Clear database only (default)
#   ./scripts/clear-test-data.sh
#
#   # Clear both database and filesystem
#   ./scripts/clear-test-data.sh --all
#
#   # Clear only filesystem (keep database)
#   ./scripts/clear-test-data.sh --files-only
#
#   # Force cleanup without confirmation
#   ./scripts/clear-test-data.sh --all --force
#
# Exit Codes:
#   0 - Cleanup successful
#   1 - User cancelled
#   2 - Error occurred

set -e

# ============ Load Environment Variables ============

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Load .env file if it exists
if [ -f "$ENV_FILE" ]; then
    set -a  # Automatically export all variables
    source "$ENV_FILE"
    set +a  # Stop auto-exporting

    # Convert relative config paths to absolute paths (for local development)
    if [[ "$ENTITY_TYPES_CONFIG_PATH" != /* ]]; then
        export ENTITY_TYPES_CONFIG_PATH="$PROJECT_ROOT/$ENTITY_TYPES_CONFIG_PATH"
    fi
    if [[ "$METADATA_SCHEMA_PATH" != /* ]]; then
        export METADATA_SCHEMA_PATH="$PROJECT_ROOT/$METADATA_SCHEMA_PATH"
    fi
fi

# ============ Configuration ============

API_URL="${API_URL:-http://localhost:9100}"
API_KEY="${API_KEY:-test-key-12345}"
CV_DATA_DIR="${CV_DATA_DIR:-$PROJECT_ROOT/tests/fixtures/sample-data/cv-pdfs}"

# Flags
MODE="db-only"  # Default mode
FORCE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============ Argument Parsing ============

while [[ $# -gt 0 ]]; do
  case $1 in
    --all)
      MODE="all"
      shift
      ;;
    --db-only)
      MODE="db-only"
      shift
      ;;
    --files-only)
      MODE="files-only"
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --db-only         Clear only database data (default)"
      echo "  --files-only      Clear only filesystem PDF files"
      echo "  --all             Clear both database and filesystem data"
      echo "  --force           Skip confirmation prompt"
      echo "  --help, -h        Show this help message"
      echo ""
      echo "Environment Variables:"
      echo "  API_URL           API base URL (default: http://localhost:9000)"
      echo "  API_KEY           API key for authentication (default: test-key-12345)"
      echo "  CV_DATA_DIR       CV samples directory (default: tests/fixtures/sample-data/cv-pdfs)"
      echo ""
      echo "Examples:"
      echo "  $0                                # Clear database only (with prompt)"
      echo "  $0 --all                          # Clear everything (with prompt)"
      echo "  $0 --files-only --force           # Clear files only (no prompt)"
      exit 0
      ;;
    *)
      echo -e "${RED}✗${NC} Unknown option: $1"
      echo "Use --help for usage information"
      exit 2
      ;;
  esac
done

# ============ Helper Functions ============

log_info() {
  echo -e "${BLUE}➜${NC} $1"
}

log_success() {
  echo -e "${GREEN}✓${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

# ============ Count Resources ============

DOC_COUNT=0
FILE_COUNT=0

if [[ "$MODE" == "db-only" || "$MODE" == "all" ]]; then
  log_info "Counting documents in database..."

  # Try to get document count from API
  DOCS_RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/v1/documents?limit=1000" 2>/dev/null || echo "{}")

  if command -v jq > /dev/null 2>&1; then
    DOC_COUNT=$(echo "$DOCS_RESPONSE" | jq -r '.total // .documents | length // 0' 2>/dev/null || echo "0")
  else
    # Fallback without jq - count documentId occurrences
    DOC_COUNT=$(echo "$DOCS_RESPONSE" | grep -o '"documentId"' | wc -l)
  fi

  if [[ "$DOC_COUNT" =~ ^[0-9]+$ ]]; then
    echo "  Found: $DOC_COUNT documents"
  else
    log_warning "Could not determine document count (API may be unavailable)"
    DOC_COUNT=0
  fi
fi

if [[ "$MODE" == "files-only" || "$MODE" == "all" ]]; then
  log_info "Counting PDF files in filesystem..."

  if [[ -d "$CV_DATA_DIR" ]]; then
    FILE_COUNT=$(find "$CV_DATA_DIR" -name "*.pdf" 2>/dev/null | wc -l)
    echo "  Found: $FILE_COUNT PDF files in $CV_DATA_DIR"
  else
    log_warning "CV data directory not found: $CV_DATA_DIR"
    FILE_COUNT=0
  fi
fi

echo ""

# ============ Confirmation Prompt ============

if [[ "$FORCE" == false ]]; then
  echo "============================================================"
  echo "CLEANUP CONFIRMATION"
  echo "============================================================"
  echo ""
  echo "About to delete:"

  if [[ "$MODE" != "files-only" ]]; then
    echo -e "  ${YELLOW}•${NC} $DOC_COUNT documents from Neo4j (via API)"
  fi

  if [[ "$MODE" != "db-only" ]]; then
    echo -e "  ${YELLOW}•${NC} $FILE_COUNT PDF files from $CV_DATA_DIR"
  fi

  echo ""
  echo -e "${YELLOW}⚠ This action cannot be undone!${NC}"
  echo ""

  read -p "Continue? [y/N] " -n 1 -r
  echo ""

  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Cleanup cancelled by user"
    exit 1
  fi

  echo ""
fi

# ============ Execute Cleanup ============

DELETED_DOCS=0
DELETED_FILES=0

echo "============================================================"
echo "EXECUTING CLEANUP"
echo "============================================================"
echo ""

# ============ Database Cleanup ============

if [[ "$MODE" == "db-only" || "$MODE" == "all" ]]; then
  log_info "Cleaning database documents..."

  # Get all document IDs
  DOCS_RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/api/v1/documents?limit=1000" 2>/dev/null || echo "{}")

  if command -v jq > /dev/null 2>&1; then
    DOC_IDS=$(echo "$DOCS_RESPONSE" | jq -r '.documents[]?.id // .documents[]?.documentId // empty' 2>/dev/null)
  else
    # Fallback without jq - extract IDs with grep
    DOC_IDS=$(echo "$DOCS_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    if [[ -z "$DOC_IDS" ]]; then
      DOC_IDS=$(echo "$DOCS_RESPONSE" | grep -o '"documentId":"[^"]*"' | cut -d'"' -f4)
    fi
  fi

  if [[ -n "$DOC_IDS" ]]; then
    for doc_id in $DOC_IDS; do
      DELETE_RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X DELETE "$API_URL/api/v1/documents/$doc_id" \
        -H "X-API-Key: $API_KEY" \
        2>/dev/null || echo "ERROR\n500")

      HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -1)

      if [[ "$HTTP_CODE" == "204" || "$HTTP_CODE" == "200" ]]; then
        ((DELETED_DOCS++))
        echo -e "  ${GREEN}✓${NC} Deleted document: $doc_id"
      else
        log_warning "Failed to delete document $doc_id (HTTP $HTTP_CODE)"
      fi
    done

    log_success "Deleted $DELETED_DOCS documents from Neo4j"
  else
    log_info "No documents found to delete"
  fi

  echo ""
fi

# ============ Filesystem Cleanup ============

if [[ "$MODE" == "files-only" || "$MODE" == "all" ]]; then
  log_info "Cleaning filesystem PDF files..."

  if [[ -d "$CV_DATA_DIR" ]]; then
    # Find and delete PDF files
    while IFS= read -r -d '' pdf_file; do
      rm -f "$pdf_file"
      ((DELETED_FILES++))
      echo -e "  ${GREEN}✓${NC} Deleted file: $(basename "$pdf_file")"
    done < <(find "$CV_DATA_DIR" -name "*.pdf" -print0 2>/dev/null)

    if [[ $DELETED_FILES -gt 0 ]]; then
      log_success "Deleted $DELETED_FILES PDF files from filesystem"
    else
      log_info "No PDF files found to delete"
    fi
  else
    log_warning "CV data directory not found: $CV_DATA_DIR"
  fi

  echo ""
fi

# ============ Cleanup Summary ============

echo "============================================================"
echo -e "${GREEN}✓ CLEANUP COMPLETE${NC}"
echo "============================================================"
echo ""

if [[ "$MODE" != "files-only" ]]; then
  echo "  Database: Deleted $DELETED_DOCS documents from Neo4j"
fi

if [[ "$MODE" != "db-only" ]]; then
  echo "  Filesystem: Deleted $DELETED_FILES PDF files"
fi

echo ""

if [[ $DELETED_DOCS -eq 0 && $DELETED_FILES -eq 0 ]]; then
  log_info "No data was found to delete"
fi

exit 0

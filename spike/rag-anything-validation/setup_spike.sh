#!/bin/bash
# RAG-Anything Spike Setup Script
# Story 0.1: Environment setup for validation testing

set -e  # Exit on error

echo "======================================="
echo "RAG-Anything Validation Spike Setup"
echo "Story 0.1: Technical Validation"
echo "======================================="
echo ""

# Check Python version
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "Found Python $PYTHON_VERSION"

if [ "$PYTHON_VERSION" != "3.10" ] && [ "$PYTHON_VERSION" != "3.11" ]; then
    echo "⚠ Warning: RAG-Anything officially supports Python 3.10"
    echo "  Current version: $PYTHON_VERSION may have compatibility issues"
fi

# Install system dependencies
echo ""
echo "Step 2: Installing system dependencies..."
echo "Required packages: poppler-utils, tesseract-ocr, libreoffice"

if command -v apt-get &> /dev/null; then
    echo "Debian/Ubuntu system detected"
    echo "Run: sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-eng libreoffice python3-venv"
elif command -v yum &> /dev/null; then
    echo "CentOS/RHEL system detected"
    echo "Run: sudo yum install -y poppler-utils tesseract tesseract-langpack-eng libreoffice"
elif command -v brew &> /dev/null; then
    echo "macOS system detected"
    echo "Run: brew install poppler tesseract libreoffice"
fi

# Check if system dependencies are installed
echo ""
echo "Checking system dependencies..."
command -v pdftotext >/dev/null 2>&1 && echo "✓ poppler-utils installed" || echo "✗ poppler-utils missing"
command -v tesseract >/dev/null 2>&1 && echo "✓ tesseract-ocr installed" || echo "✗ tesseract-ocr missing"
command -v soffice >/dev/null 2>&1 && echo "✓ libreoffice installed" || echo "✗ libreoffice missing (needed for DOCX/PPTX)"

# Create virtual environment
echo ""
echo "Step 3: Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install Python packages
echo ""
echo "Step 4: Installing Python dependencies..."
source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "Step 5: Generating sample documents..."
python create_samples.py

echo ""
echo "======================================"
echo "✓ Setup Complete!"
echo "======================================"
echo ""
echo "To run the spike tests:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Run format validation: python test_all_formats.py"
echo "  3. Run benchmarks: python benchmark_parsing.py"
echo "  4. Run error tests: python test_error_handling.py"
echo ""
echo "Results will be saved to: outputs/"

# Spike: RAG-Anything Validation Environment
# Python 3.11 base matching project tech stack

FROM python:3.11-slim

# Install system dependencies for RAG-Anything and MinerU
# Note: LibreOffice excluded initially for faster builds (add if needed for Office docs)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /spike

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy spike scripts and samples
COPY . .

# Set environment to non-interactive for safety
ENV DEBIAN_FRONTEND=noninteractive

CMD ["python", "test_all_formats.py"]

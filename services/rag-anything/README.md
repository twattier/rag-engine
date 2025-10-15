# RAG-Anything Document Processing Service

Multi-format document parsing service powered by RAG-Anything/MinerU.

## Purpose

Handles document ingestion for:
- PDF files (text and OCR)
- Microsoft Office documents (Word, Excel, PowerPoint)
- Markdown and HTML
- Code files
- Images (via OCR)

## Features

- High-fidelity table extraction
- Mathematical equation recognition
- Multi-column layout handling
- Image and diagram extraction
- OCR for scanned documents

## Configuration

See `.env.example` for configuration variables:
- `DEFAULT_PARSE_METHOD`: auto, ocr, or txt
- `MAX_FILE_SIZE_MB`: Maximum upload size
- `OCR_LANGUAGE`: OCR language (default: eng)

## Development

```bash
# Run locally (from repository root)
cd services/rag-anything
pip install -r requirements.txt
python -m app.main

# Run in Docker
docker-compose up rag-anything
```

# RAG-Anything Validation Spike

**Story**: 0.1 - RAG-Anything Technical Validation Spike
**Purpose**: Validate RAG-Anything library compatibility with 6 required document formats

## Directory Structure

```
spike/rag-anything-validation/
├── Dockerfile                   # Spike environment (Python 3.11 + dependencies)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── create_samples.py            # Generate sample documents
├── download_samples.sh          # Download real-world documents (optional)
├── test_all_formats.py          # Main format validation script
├── benchmark_parsing.py         # Performance benchmarking script
├── test_error_handling.py       # Malformed document testing
├── samples/                     # Sample documents (all climate change domain)
│   ├── climate-abstract.txt
│   ├── climate-report.md
│   ├── climate-data.csv
│   ├── climate-research-paper.pdf
│   ├── climate-mitigation-strategies.docx
│   └── climate-science-presentation.pptx
└── outputs/                     # Test results and parsed outputs
    ├── format_validation_results.json
    ├── performance_benchmarks.json
    └── error_handling_results.json
```

## Required Formats (6 total)

1. **PDF** (text-based) - Research papers with tables and equations
2. **PDF** (scanned) - Image-based requiring OCR
3. **Plain Text (.txt)** - Simple text documents
4. **Markdown (.md)** - Structured documents with headings
5. **Microsoft Word (.docx)** - Documents with tables and images
6. **Microsoft PowerPoint (.pptx)** - Presentations with slides and charts
7. **CSV (.csv)** - Tabular data

## Sample Document Domain

All samples use **Climate Change Science** as the domain to enable:
- Coherent knowledge graph visualization in future testing
- Realistic entity extraction validation
- Domain-specific terminology testing

## Running the Spike

### Build Docker Environment

```bash
docker build -t rag-anything-spike:latest .
```

### Generate Sample Documents

```bash
docker run --rm -v $(pwd)/samples:/spike/samples rag-anything-spike:latest python create_samples.py
```

### Run Format Validation

```bash
docker run --rm \
  -v $(pwd)/samples:/spike/samples \
  -v $(pwd)/outputs:/spike/outputs \
  rag-anything-spike:latest \
  python test_all_formats.py
```

### Run Performance Benchmarks

```bash
docker run --rm \
  -v $(pwd)/samples:/spike/samples \
  -v $(pwd)/outputs:/spike/outputs \
  rag-anything-spike:latest \
  python benchmark_parsing.py
```

### Run Error Handling Tests

```bash
docker run --rm \
  -v $(pwd)/samples:/spike/samples \
  -v $(pwd)/outputs:/spike/outputs \
  rag-anything-spike:latest \
  python test_error_handling.py
```

## Expected Outputs

### Success Criteria
- ✓ At least 5/6 formats parse successfully
- ✓ Performance acceptable (<10 seconds for 10-page PDF)
- ✓ Error messages actionable (not cryptic stack traces)
- ✓ PowerPoint slide structure preserved

### Failure Criteria
- ✗ Critical formats fail (PDF, DOCX, or MD)
- ✗ Performance unacceptable (>60 seconds for 10-page PDF)
- ✗ Library crashes or requires complex workarounds

## Deliverable

Spike report: `docs/architecture/rag-anything-spike-report.md`

Includes:
- Executive summary with go/no-go recommendation
- Format support matrix
- JSON output structure examples
- Performance benchmarks
- Known limitations and workarounds
- Fallback parser recommendations
- Integration guidance for Epic 2 Story 2.1

## Notes

- Spike is time-boxed to 2 days (16 hours)
- Docker provides isolation (no venv needed)
- Malformed document tests run in isolated container for security
- All system dependencies (poppler-utils, tesseract-ocr, LibreOffice) included

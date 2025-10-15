# Testing Strategy

## Testing Pyramid

```text
        E2E Tests (Playwright/Selenium)
        /                              \
       Integration Tests (pytest + httpx)
      /                                  \
     Backend Unit Tests (pytest + mocks)
```

**Testing Philosophy:**
- **70% Unit Tests**: Fast, isolated, mock external dependencies
- **20% Integration Tests**: API routes + database interactions
- **10% E2E Tests**: Full workflow tests (ingest → query → verify)

---

## Test Organization

### Backend Tests

```text
services/api/tests/
├── conftest.py                  # Pytest fixtures (test DB, client)
├── unit/
│   ├── test_document_service.py # Service layer unit tests
│   ├── test_query_service.py
│   └── test_validators.py       # Pydantic validation tests
├── integration/
│   ├── test_document_routes.py  # API endpoint tests
│   ├── test_query_routes.py
│   └── test_graph_routes.py
└── e2e/
    └── test_full_workflow.py    # End-to-end scenarios

services/lightrag/tests/
├── test_lightrag_service.py     # LightRAG wrapper tests
└── test_storage_adapters.py     # Neo4j adapter tests

services/rag-anything/tests/
├── test_mineru_parser.py        # Document parsing tests
├── test_image_processor.py      # Image captioning tests
└── test_table_processor.py      # Table extraction tests
```

---

### E2E Tests (Conceptual - Multi-Service)

```text
tests/e2e/
├── conftest.py                  # Docker Compose fixtures
├── test_ingest_query_flow.py   # Full RAG workflow
├── test_document_deletion.py   # Deletion consistency
└── test_metadata_filtering.py  # Metadata query tests
```

---

## Test Examples

### Backend API Test

```python
# services/api/tests/integration/test_document_routes.py

import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_ingest_document_success(
    async_client: AsyncClient,
    sample_pdf_file: bytes
):
    """Test successful document ingestion."""
    files = {"file": ("test.pdf", sample_pdf_file, "application/pdf")}
    data = {"metadata": '{"author": "Test Author"}'}

    response = await async_client.post(
        "/documents/ingest",
        files=files,
        data=data
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    assert "docId" in result
    assert result["status"] in ["pending", "processing", "indexed"]
    assert result["metadata"]["author"] == "Test Author"


@pytest.mark.asyncio
async def test_ingest_invalid_file_type(async_client: AsyncClient):
    """Test rejection of unsupported file types."""
    files = {"file": ("test.exe", b"fake executable", "application/x-msdownload")}

    response = await async_client.post(
        "/documents/ingest",
        files=files
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error = response.json()
    assert "error" in error
    assert "unsupported" in error["error"]["message"].lower()


@pytest.mark.asyncio
async def test_query_hybrid_mode(async_client: AsyncClient, indexed_document_id: str):
    """Test hybrid query mode returns valid results."""
    request = {
        "query": "What are the main findings?",
        "mode": "hybrid",
        "top_k": 10
    }

    response = await async_client.post("/query", json=request)

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "response" in result
    assert isinstance(result["contextChunks"], list)
    assert isinstance(result["entities"], list)
    assert result["latencyMs"] > 0
```

---

### Backend Unit Test

```python
# services/api/tests/unit/test_document_service.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.api.services.document_service import DocumentService

@pytest.mark.asyncio
async def test_ingest_document_creates_doc_id():
    """Test that document ingestion generates doc_id if not provided."""
    mock_lightrag = AsyncMock()
    mock_raganything = AsyncMock()

    # Mock RAG-Anything parsing response
    mock_raganything.process_document.return_value = [
        {"type": "text", "text": "Sample content", "page_idx": 0}
    ]

    # Mock LightRAG insertion
    mock_lightrag.insert_content_list.return_value = {
        "doc_id": "generated-doc-id",
        "chunk_count": 5,
        "entity_count": 3
    }

    service = DocumentService(
        lightrag_service=mock_lightrag,
        raganything_service=mock_raganything
    )

    # Simulate file upload (no doc_id provided)
    mock_file = MagicMock()
    mock_file.filename = "test.pdf"

    result = await service.ingest_document(
        file=mock_file,
        metadata={"author": "Test"},
        doc_id=None,  # Let service generate ID
        parse_method="auto"
    )

    assert result.doc_id == "generated-doc-id"
    assert result.status == "indexed"
    assert result.chunk_count == 5
    assert result.entity_count == 3

    # Verify RAG-Anything was called
    mock_raganything.process_document.assert_called_once()

    # Verify LightRAG was called with content list
    mock_lightrag.insert_content_list.assert_called_once()
```

---

### E2E Test (Full Workflow)

```python
# tests/e2e/test_full_workflow.py

import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_rag_workflow(async_client: AsyncClient, sample_pdf: bytes):
    """
    Test complete RAG workflow:
    1. Ingest document
    2. Wait for processing
    3. Query document
    4. Verify results
    5. Delete document
    """
    # Step 1: Ingest document
    files = {"file": ("research_paper.pdf", sample_pdf, "application/pdf")}
    data = {"metadata": '{"topic": "RAG", "year": "2025"}'}

    ingest_response = await async_client.post(
        "/documents/ingest",
        files=files,
        data=data
    )
    assert ingest_response.status_code == 202
    doc_id = ingest_response.json()["docId"]

    # Step 2: Wait for processing (poll status)
    max_retries = 30
    for _ in range(max_retries):
        status_response = await async_client.get(f"/documents/{doc_id}")
        status = status_response.json()["status"]

        if status == "indexed":
            break
        elif status == "failed":
            pytest.fail("Document processing failed")

        await asyncio.sleep(2)
    else:
        pytest.fail("Document processing timeout")

    # Step 3: Query document
    query_response = await async_client.post(
        "/query",
        json={
            "query": "What is RAG?",
            "mode": "hybrid",
            "metadata_filters": {"topic": "RAG"}
        }
    )
    assert query_response.status_code == 200
    query_result = query_response.json()

    # Step 4: Verify results
    assert "RAG" in query_result["response"] or "retrieval" in query_result["response"].lower()
    assert len(query_result["contextChunks"]) > 0
    assert len(query_result["entities"]) > 0

    # Step 5: Delete document
    delete_response = await async_client.delete(f"/documents/{doc_id}")
    assert delete_response.status_code == 204

    # Verify deletion
    verify_response = await async_client.get(f"/documents/{doc_id}")
    assert verify_response.status_code == 404
```

**Fixture Example:**

```python
# tests/e2e/conftest.py

import pytest
import subprocess
import time
from httpx import AsyncClient

@pytest.fixture(scope="session", autouse=True)
def docker_compose_services():
    """Start Docker Compose services for E2E tests."""
    # Start services
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "up", "-d"],
        check=True
    )

    # Wait for health check
    time.sleep(10)

    # Health check
    import httpx
    for _ in range(30):
        try:
            response = httpx.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                break
        except httpx.RequestError:
            pass
        time.sleep(2)
    else:
        raise RuntimeError("Services failed to start")

    yield

    # Teardown
    subprocess.run(
        ["docker", "compose", "down", "-v"],
        check=True
    )


@pytest.fixture
async def async_client() -> AsyncClient:
    """Async HTTP client for API requests."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def sample_pdf() -> bytes:
    """Load sample PDF for testing."""
    with open("tests/fixtures/sample.pdf", "rb") as f:
        return f.read()
```

---

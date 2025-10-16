# Batch Document Ingestion

This document describes how to use the batch document ingestion API to upload multiple documents in a single operation.

## Overview

The batch ingestion feature allows you to efficiently populate large knowledge bases by uploading multiple documents at once. Documents are processed asynchronously in the background, and you can track progress using a batch ID.

## API Endpoints

### POST /api/v1/documents/ingest/batch

Start a batch ingestion operation.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Rate Limit:** 10 requests per minute per API key
- **Batch Limit:** Maximum 100 files per batch

**Request Parameters:**
- `files` (required): Multiple document files
- `metadata_mapping` (optional): CSV or JSON file mapping filenames to metadata

**Supported File Formats:**
- PDF (.pdf)
- Text (.txt, .md)
- Microsoft Office (.docx, .pptx)
- CSV (.csv)

**Response (202 Accepted):**
```json
{
  "batchId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "totalDocuments": 50,
  "status": "in_progress",
  "message": "Batch ingestion started. Use batch_id to check status"
}
```

**Error Responses:**
- `400 BATCH_TOO_LARGE`: More than 100 files uploaded
- `401 UNAUTHORIZED`: Missing or invalid API key
- `422 INVALID_METADATA_MAPPING`: Metadata mapping file is malformed
- `429 RATE_LIMIT_EXCEEDED`: Too many requests

### GET /api/v1/documents/ingest/batch/{batch_id}/status

Get the current status of a batch ingestion operation.

**Response (200 OK - In Progress):**
```json
{
  "batchId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "totalDocuments": 50,
  "processedCount": 25,
  "failedCount": 2,
  "status": "in_progress",
  "failedDocuments": [
    {
      "filename": "corrupted.pdf",
      "error": "Failed to parse PDF: File is corrupted"
    }
  ]
}
```

**Response (200 OK - Completed):**
```json
{
  "batchId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "totalDocuments": 50,
  "processedCount": 48,
  "failedCount": 2,
  "status": "completed",
  "completedAt": "2025-10-16T14:35:00Z",
  "processingTimeSeconds": 120.5,
  "failedDocuments": [
    {
      "filename": "corrupted.pdf",
      "error": "Failed to parse PDF: File is corrupted"
    }
  ]
}
```

**Status Values:**
- `in_progress`: Batch is currently being processed
- `completed`: All documents processed successfully
- `partial_failure`: Some documents failed, but at least one succeeded
- `failed`: All documents failed

**Error Responses:**
- `404 BATCH_NOT_FOUND`: Batch ID not found

## Metadata Mapping

You can optionally provide a metadata mapping file to associate custom metadata with each document in the batch.

### CSV Format

CSV file with a header row. The `filename` column is required.

**Example (metadata-mapping.csv):**
```csv
filename,author,department,date_created,tags,category
doc1.pdf,John Doe,Engineering,2025-10-16,"technical,api",specification
doc2.docx,Jane Smith,Marketing,2025-10-15,"marketing,campaign",report
doc3.txt,Bob Johnson,HR,2025-10-14,"hr,policy",manual
```

**Notes:**
- `filename` column is required and must match uploaded file names exactly
- `tags` field: Use comma-separated values (will be converted to array)
- Missing files in mapping: Will use empty metadata
- Extra files not in mapping: Will use empty metadata

### JSON Format

JSON object with filenames as keys.

**Example (metadata-mapping.json):**
```json
{
  "doc1.pdf": {
    "author": "John Doe",
    "department": "Engineering",
    "date_created": "2025-10-16",
    "tags": ["technical", "api"],
    "category": "specification"
  },
  "doc2.docx": {
    "author": "Jane Smith",
    "department": "Marketing",
    "date_created": "2025-10-15",
    "tags": ["marketing", "campaign"],
    "category": "report"
  },
  "doc3.txt": {
    "author": "Bob Johnson",
    "department": "HR",
    "date_created": "2025-10-14",
    "tags": ["hr", "policy"],
    "category": "manual"
  }
}
```

## Usage Examples

### Example 1: Basic Batch Upload (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ingest/batch" \
  -H "Authorization: Bearer your-api-key" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.docx" \
  -F "files=@doc3.txt"
```

### Example 2: Batch Upload with CSV Metadata (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ingest/batch" \
  -H "Authorization: Bearer your-api-key" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.docx" \
  -F "files=@doc3.txt" \
  -F "metadata_mapping=@metadata-mapping.csv"
```

### Example 3: Check Batch Status (curl)

```bash
curl -X GET "http://localhost:8000/api/v1/documents/ingest/batch/7c9e6679-7425-40de-944b-e07fc1f90ae7/status" \
  -H "Authorization: Bearer your-api-key"
```

### Example 4: Python Client

```python
import httpx
import asyncio

async def batch_upload_documents():
    """Upload documents in batch with metadata mapping."""

    # Prepare files
    files = [
        ("files", open("doc1.pdf", "rb")),
        ("files", open("doc2.docx", "rb")),
        ("files", open("doc3.txt", "rb")),
        ("metadata_mapping", open("metadata-mapping.csv", "rb")),
    ]

    # Start batch ingestion
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/documents/ingest/batch",
            headers={"Authorization": "Bearer your-api-key"},
            files=files,
        )

        batch_data = response.json()
        batch_id = batch_data["batchId"]
        print(f"Batch started: {batch_id}")

        # Poll for completion
        while True:
            status_response = await client.get(
                f"http://localhost:8000/api/v1/documents/ingest/batch/{batch_id}/status",
                headers={"Authorization": "Bearer your-api-key"},
            )

            status_data = status_response.json()
            print(f"Progress: {status_data['processedCount']}/{status_data['totalDocuments']}")

            if status_data["status"] in ["completed", "partial_failure", "failed"]:
                print(f"Batch finished: {status_data['status']}")
                print(f"Processed: {status_data['processedCount']}, Failed: {status_data['failedCount']}")

                if status_data["failedDocuments"]:
                    print("Failed documents:")
                    for failed in status_data["failedDocuments"]:
                        print(f"  - {failed['filename']}: {failed['error']}")

                break

            await asyncio.sleep(2)

# Run
asyncio.run(batch_upload_documents())
```

## Performance Considerations

### Processing Speed

- **Target Throughput:** >10 documents per minute
- **Sequential Processing:** Documents are processed one at a time to limit memory usage
- **Async Operations:** Background processing doesn't block API responses

### Memory Management

- **Memory Limit:** Maximum 5GB concurrent processing per batch
- **Streaming Uploads:** Files are streamed to disk, not loaded into memory
- **Sequential Processing:** Only one document processed at a time per batch

### Best Practices

1. **Batch Size:**
   - Optimal: 10-50 documents per batch
   - Maximum: 100 documents per batch
   - For larger datasets, split into multiple batches

2. **File Sizes:**
   - Keep individual files under 50MB
   - Mix of small and large files is fine (sequential processing)

3. **Status Polling:**
   - Poll every 2-5 seconds for status updates
   - Implement exponential backoff for long-running batches

4. **Error Handling:**
   - Partial failures are normal (e.g., corrupted files)
   - Check `failedDocuments` list for specific error messages
   - Retry failed documents individually if needed

## Troubleshooting

### Batch Too Large Error

**Error:** `BATCH_TOO_LARGE: Batch exceeds maximum size of 100 files`

**Solution:** Split your batch into multiple smaller batches (max 100 files each).

### Invalid Metadata Mapping

**Error:** `INVALID_METADATA_MAPPING: Failed to parse CSV metadata mapping`

**Solutions:**
- Ensure CSV has `filename` column as first column
- Check for valid CSV format (proper commas, no extra quotes)
- Verify JSON is valid (use a JSON validator)
- Ensure filenames in mapping match uploaded files exactly

### Batch Not Found

**Error:** `BATCH_NOT_FOUND: Batch {batch_id} not found`

**Solutions:**
- Verify the batch_id is correct (must be valid UUID)
- Check if batch was recently started (may take a moment to initialize)
- Note: Batch status is stored in-memory (lost on server restart in MVP)

### Partial Failure Status

**Status:** `partial_failure: Some documents failed, but at least one succeeded`

**Action:**
1. Check `failedDocuments` array in status response
2. Review error messages for each failed document
3. Fix issues (e.g., corrupted files, invalid metadata)
4. Retry failed documents individually using single document ingestion API

### High Failure Rate

**Problem:** Most documents in batch are failing

**Common Causes:**
- Unsupported file formats (check supported formats list)
- Corrupted or malformed files
- Invalid metadata that fails schema validation
- RAG-Anything service is down or unreachable

**Debugging Steps:**
1. Try single document ingestion first to isolate the issue
2. Check logs for detailed error messages
3. Verify RAG-Anything service is running (`docker ps`)
4. Test with known-good sample files

## Monitoring

### Structured Logs

All batch operations are logged with the following fields:

- `batch_id`: Batch UUID for tracking
- `total_documents`: Total number of documents in batch
- `processed_count`: Number of successfully processed documents
- `failed_count`: Number of failed documents
- `duration_seconds`: Total processing time

**Log Events:**
- `batch_ingestion_started`: Batch processing initiated
- `batch_document_processed`: Individual document completed
- `batch_document_processing_failed`: Individual document failed
- `batch_processing_completed`: Batch finished (all documents processed)

### Metrics

Key metrics to monitor:

- **Throughput:** Documents processed per minute
- **Success Rate:** `processed_count / total_documents`
- **Average Batch Time:** Time to process full batch
- **Failure Rate:** `failed_count / total_documents`

## Limitations (MVP)

1. **In-Memory Status Storage:**
   - Batch status is stored in-memory
   - Status lost on server restart
   - Upgrade to Redis planned for Epic 5

2. **No Batch Cancellation:**
   - Cannot cancel a running batch
   - Must wait for completion or server restart

3. **No Priority Queue:**
   - Batches processed in order received
   - No way to prioritize urgent batches

4. **No Progress Webhooks:**
   - Must poll for status updates
   - Webhook notifications planned for future epic

## Future Enhancements (Epic 5+)

- Redis-backed status storage (persistent across restarts)
- Batch cancellation API
- Progress webhooks (callback URLs)
- Priority queue for urgent batches
- Parallel processing (multiple documents simultaneously)
- Estimated completion time calculation

# Metadata Schema Migration Guide

## Overview

The RAG Engine supports dynamic updates to metadata schemas with automatic backward compatibility validation and document reindexing. This allows you to adapt your knowledge base to evolving organizational needs without redeployment.

## When to Use Metadata Schema Updates

Use schema migration when you need to:

- **Add new metadata fields** to capture additional document attributes
- **Make fields optional** that were previously required (with defaults)
- **Update field descriptions** or default values
- **Remove optional fields** that are no longer needed

## Backward Compatibility Requirements

All schema updates must maintain backward compatibility. The system enforces these rules:

### ✅ Allowed Changes

1. **Add optional fields**
   ```yaml
   # NEW FIELD - OK
   - field_name: priority
     type: integer
     required: false
     default: 3
   ```

2. **Add optional fields with defaults**
   ```yaml
   - field_name: category
     type: string
     required: false
     default: "General"
   ```

3. **Remove optional fields**
   - Any field with `required: false` can be safely removed

4. **Update field descriptions**
   - Description changes don't affect data validation

5. **Update default values**
   - Only affects new documents (existing documents retain their values)

### ❌ Breaking Changes (Rejected)

1. **Remove required fields**
   ```yaml
   # ERROR: Cannot remove required field 'author'
   ```

2. **Change field types**
   ```yaml
   # ERROR: Cannot change type from 'string' to 'integer'
   ```

3. **Add required fields without defaults**
   ```yaml
   # ERROR: New required field must have default value
   - field_name: owner
     type: string
     required: true  # ❌ No default provided
   ```

## Reindexing Workflow

When you add new fields with defaults, you must reindex existing documents to apply the defaults.

### Option 1: Deferred Reindexing (Recommended)

1. Update the schema (API marks it as "pending reindex")
2. Trigger reindexing manually when ready
3. Monitor progress via status endpoint

```bash
# Step 1: Update schema
curl -X PUT http://localhost:8000/api/v1/config/metadata-schema \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @new-schema.json

# Step 2: Trigger reindexing
curl -X POST http://localhost:8000/api/v1/documents/reindex \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"filters": {"status": "indexed"}}'

# Step 3: Check status
curl http://localhost:8000/api/v1/documents/reindex/{job_id}/status
```

### Option 2: Filtered Reindexing

Reindex specific documents based on criteria:

```json
{
  "filters": {
    "document_ids": ["doc-uuid-1", "doc-uuid-2"],
    "ingestion_date_from": "2025-10-01",
    "ingestion_date_to": "2025-10-16",
    "metadata": {
      "department": "engineering"
    }
  }
}
```

## Performance Considerations

### Reindexing Performance

- **Small batches (<1000 docs):** ~1-2 seconds
- **Medium batches (1K-10K docs):** ~10-30 seconds
- **Large batches (10K+ docs):** ~1-5 minutes

**Best Practices:**

1. **Off-peak hours:** Schedule large reindexes during low-traffic periods
2. **Filtered reindexing:** Reindex only affected documents when possible
3. **Monitor progress:** Use status endpoint to track completion
4. **Idempotent:** Safe to run multiple times (no duplicate updates)

### Database Impact

- Reindexing performs **metadata-only updates** (no content re-parsing)
- Uses **parameterized queries** for safety
- **Read-light:** Minimal Neo4j read load
- **Write-moderate:** One update per document

## Common Schema Evolution Examples

### Example 1: Add Priority Field

**Before:**
```yaml
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Document author"
```

**After:**
```yaml
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Document author"

  - field_name: priority
    type: integer
    required: false
    default: 3
    description: "Document priority (1-5)"
```

**Result:** All existing documents get `priority: 3` after reindexing.

### Example 2: Add Tags with Empty Default

```yaml
- field_name: tags
  type: tags  # List of strings
  required: false
  default: []
  description: "Document tags for categorization"
```

### Example 3: Make Field Optional

**Before:**
```yaml
- field_name: department
  type: string
  required: true
  description: "Department name"
```

**After:**
```yaml
- field_name: department
  type: string
  required: false  # Now optional
  default: "General"
  description: "Department name"
```

## Troubleshooting

### "Schema update rejected: Breaking changes detected"

**Cause:** Your schema update violates backward compatibility rules.

**Solution:** Review the `incompatibilities` field in the error response and modify your schema to follow allowed changes only.

### "Reindex job {job_id} not found"

**Cause:** Job ID is invalid or expired (jobs retained for 24 hours).

**Solution:** Check job ID or trigger a new reindex operation.

### Documents missing new fields after reindex

**Cause:** Reindex job may have failed or is still in progress.

**Solution:**
1. Check reindex job status
2. Review `failed_documents` for errors
3. Re-run reindex if needed (idempotent)

### Slow reindexing performance

**Cause:** Large document count or database load.

**Solution:**
1. Use filtered reindexing to process smaller batches
2. Schedule during off-peak hours
3. Check Neo4j performance metrics

## API Reference

### Update Metadata Schema

```http
PUT /api/v1/config/metadata-schema
Content-Type: application/json
X-API-Key: your-api-key

{
  "metadata_fields": [...]
}
```

**Response (200 OK):**
```json
{
  "message": "Metadata schema updated successfully",
  "schema_version": "2.0",
  "changes_detected": true,
  "reindex_required": true,
  "reindex_status": "pending",
  "added_fields": ["priority"],
  "removed_fields": [],
  "modified_fields": []
}
```

### Trigger Reindexing

```http
POST /api/v1/documents/reindex
Content-Type: application/json
X-API-Key: your-api-key

{
  "filters": {
    "status": "indexed"
  }
}
```

**Response (202 Accepted):**
```json
{
  "reindex_job_id": "uuid",
  "total_documents": 150,
  "status": "in_progress",
  "message": "Reindexing started. Use reindex_job_id to check status"
}
```

### Check Reindex Status

```http
GET /api/v1/documents/reindex/{job_id}/status
```

**Response (200 OK):**
```json
{
  "reindex_job_id": "uuid",
  "total_documents": 150,
  "processed_count": 148,
  "failed_count": 2,
  "status": "completed",
  "completed_at": "2025-10-16T14:45:00Z",
  "processing_time_seconds": 120.5,
  "failed_documents": [
    {
      "document_id": "uuid",
      "error": "Error message"
    }
  ]
}
```

## Audit Trail

All schema changes are logged to structured logs with:

- **Timestamp:** When the change occurred
- **User:** API key that made the change (truncated for security)
- **Changes:** Added, removed, and modified fields
- **Schema versions:** Old and new version identifiers

View audit logs in your logging system (e.g., CloudWatch, Datadog).

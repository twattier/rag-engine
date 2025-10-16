# Technical Debt - Story 2.7: Schema Migration

**Story:** 2.7 - Implement Metadata Schema Migration and Reindexing
**Gate Decision:** PASS_WITH_CONCERNS
**Date Identified:** 2025-10-17
**Reviewed By:** Quinn (Test Architect)

## Summary

Story 2.7 passed QA review with a **PASS_WITH_CONCERNS** gate. All acceptance criteria are fully met with excellent code quality. The identified technical debt items are future enhancements for scalability and maintainability, not blocking issues.

**Quality Score:** 85/100

## Technical Debt Items

### 1. Schema Versioning (LOW Priority)

**Issue:** Schema versioning is hardcoded as "2.0" instead of using semantic versioning.

**Location:** [services/api/app/routers/config.py:290](../services/api/app/routers/config.py#L290)

**Impact:**
- Manual tracking required for schema version history
- No automated version detection or increment
- Difficult to track schema evolution over time

**Recommendation:**
Implement semantic versioning with auto-increment:
- Track schema version in metadata file or database
- Auto-increment version on schema changes (MAJOR.MINOR.PATCH)
- Include version in schema change audit log

**Effort:** 2-3 hours

**Suggested Implementation:**
```python
# Add to shared/models/metadata.py
class MetadataSchema(BaseModel):
    version: str = Field(default="1.0.0", description="Schema version (semver)")
    metadata_fields: List[MetadataFieldDefinition]

    def increment_version(self, change_type: str) -> str:
        """Increment version based on change type (major/minor/patch)."""
        major, minor, patch = map(int, self.version.split("."))
        if change_type == "breaking":
            return f"{major + 1}.0.0"
        elif change_type == "feature":
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"
```

---

### 2. In-Memory Job Storage (MEDIUM Priority)

**Issue:** Reindex job status stored in-memory prevents horizontal scaling and loses state on restart.

**Location:** [services/api/app/services/reindex_service.py:71](../services/api/app/services/reindex_service.py#L71)

**Impact:**
- Job status lost when API service restarts
- Cannot scale horizontally with multiple API instances
- No persistent audit trail of reindex operations

**Recommendation:**
Migrate to Redis or Neo4j for persistent job storage:
- Store job status in Redis with TTL (e.g., 24 hours)
- Or store in Neo4j as JobStatus nodes
- Enable horizontal scaling with shared job state

**Effort:** 4-6 hours

**Suggested Implementation:**
```python
# services/api/app/services/reindex_service.py
import redis.asyncio as redis
from typing import Optional

class ReindexService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def save_job_status(self, job_id: UUID, status: ReindexStatus):
        """Save job status to Redis with 24-hour TTL."""
        key = f"reindex:job:{job_id}"
        await self.redis.setex(
            key,
            86400,  # 24 hours
            status.model_dump_json()
        )

    async def get_reindex_status(self, job_id: UUID) -> Optional[ReindexStatus]:
        """Get job status from Redis."""
        key = f"reindex:job:{job_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return ReindexStatus.model_validate_json(data)
```

---

### 3. Missing Unit Tests (LOW Priority)

**Issue:** schema_validator.py lacks dedicated unit tests; validation logic tested only via integration tests.

**Location:** [shared/services/schema_validator.py](../shared/services/schema_validator.py)

**Impact:**
- Validation edge cases may not be thoroughly tested
- Integration tests are slower than unit tests
- Harder to isolate validation logic bugs

**Recommendation:**
Add unit tests for each validation rule:
- Test removed required fields detection
- Test field type change detection
- Test new required fields without defaults
- Test edge cases (empty schemas, identical schemas, etc.)

**Effort:** 2-3 hours

**Suggested Test File:**
```python
# shared/tests/test_schema_validator.py
import pytest
from shared.services.schema_validator import validate_schema_compatibility
from shared.models.metadata import MetadataSchema, MetadataFieldDefinition

def test_detect_removed_required_field():
    """Test detection of removed required field."""
    old_schema = MetadataSchema(metadata_fields=[
        MetadataFieldDefinition(field_name="author", type="string", required=True)
    ])
    new_schema = MetadataSchema(metadata_fields=[])

    incompatibilities = validate_schema_compatibility(old_schema, new_schema)

    assert len(incompatibilities) == 1
    assert incompatibilities[0].field == "author"
    assert "Cannot remove required field" in incompatibilities[0].issue

def test_detect_field_type_change():
    """Test detection of field type change."""
    old_schema = MetadataSchema(metadata_fields=[
        MetadataFieldDefinition(field_name="count", type="integer", required=False)
    ])
    new_schema = MetadataSchema(metadata_fields=[
        MetadataFieldDefinition(field_name="count", type="string", required=False)
    ])

    incompatibilities = validate_schema_compatibility(old_schema, new_schema)

    assert len(incompatibilities) == 1
    assert "type" in incompatibilities[0].issue.lower()
```

---

### 4. Sequential Document Processing (LOW Priority)

**Issue:** Reindex service processes documents sequentially, limiting throughput for large batches.

**Location:** [services/api/app/services/reindex_service.py:116-186](../services/api/app/services/reindex_service.py#L116)

**Impact:**
- Suboptimal performance for large document sets (10K+ documents)
- Longer reindex times during schema migrations
- Underutilizes available system resources

**Recommendation:**
Implement batch processing with configurable concurrency:
- Process documents in batches (e.g., 100 at a time)
- Use asyncio.gather() for concurrent processing
- Add configuration for max concurrent operations

**Effort:** 3-4 hours

**Suggested Implementation:**
```python
# services/api/app/services/reindex_service.py
import asyncio
from typing import List

class ReindexService:
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent

    async def _process_reindex_batch(
        self,
        session: Any,
        documents: List[Dict[str, Any]],
        new_schema: MetadataSchema,
        job_status: ReindexStatus
    ):
        """Process a batch of documents concurrently."""
        async def process_one(doc: Dict[str, Any]):
            try:
                metadata = doc.get("metadata", {})

                # Apply new schema defaults
                for field_def in new_schema.metadata_fields:
                    if field_def.field_name not in metadata and field_def.default is not None:
                        metadata[field_def.field_name] = field_def.default

                validated_metadata = new_schema.validate_metadata(metadata)

                await update_document_metadata(
                    session=session,
                    document_id=doc["document_id"],
                    metadata=validated_metadata,
                )

                job_status.processed_count += 1
            except Exception as e:
                job_status.failed_count += 1
                job_status.failed_documents.append(
                    FailedDocument(document_id=doc["document_id"], error=str(e))
                )

        # Process batch with concurrency limit
        await asyncio.gather(*[process_one(doc) for doc in documents])

    async def _process_reindex(
        self,
        session: Any,
        job_id: UUID,
        documents: List[Dict[str, Any]],
        new_schema: MetadataSchema,
    ):
        """Process reindexing in batches."""
        job_status = self.jobs[job_id]

        # Split into batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            await self._process_reindex_batch(session, batch, new_schema, job_status)
```

---

### 5. Concurrent Reindexing Test Coverage (LOW Priority)

**Issue:** No integration test for concurrent reindexing jobs.

**Location:** [services/api/tests/integration/test_schema_migration.py](../services/api/tests/integration/test_schema_migration.py)

**Impact:**
- Potential race conditions not tested
- Job storage isolation not verified
- Concurrent access patterns not validated

**Recommendation:**
Add integration test for concurrent reindexing:
- Start multiple reindex jobs simultaneously
- Verify job IDs are unique
- Confirm status tracking is isolated per job
- Validate no cross-job interference

**Effort:** 2-3 hours

**Suggested Test:**
```python
@pytest.mark.asyncio
async def test_concurrent_reindex_jobs(async_client: AsyncClient):
    """Test multiple concurrent reindex jobs."""
    # Start 3 reindex jobs concurrently
    job_ids = []
    for i in range(3):
        response = await async_client.post(
            "/api/v1/documents/reindex",
            json={"filters": {"status": "indexed"}},
            headers={"Authorization": "Bearer test-api-key"},
        )
        assert response.status_code == 202
        job_ids.append(response.json()["reindexJobId"])

    # Verify all job IDs are unique
    assert len(set(job_ids)) == 3

    # Check each job independently
    for job_id in job_ids:
        status_resp = await async_client.get(
            f"/api/v1/documents/reindex/{job_id}/status"
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["reindexJobId"] == job_id
```

---

## Prioritization

**High Priority (Before Next Production Release):**
- None - all items are future enhancements

**Medium Priority (Next Sprint):**
- In-memory job storage migration to Redis

**Low Priority (Backlog):**
- Schema versioning implementation
- Unit tests for schema_validator.py
- Sequential processing optimization
- Concurrent reindexing test coverage

## Related Issues

- Story 2.7 quality gate: [docs/qa/gates/2.7-schema-migration.yml](gates/2.7-schema-migration.yml)
- Story file: [docs/stories/2.7.schema-migration.md](../stories/2.7.schema-migration.md)

---

**Last Updated:** 2025-10-17
**Created By:** Quinn (Test Architect)

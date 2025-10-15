# Epic 2: Multi-Format Document Ingestion Pipeline

**Status:** Draft
**Epic Goal:** Integrate RAG-Anything for parsing multiple document formats (PDF, Markdown, HTML, Word, code files) with custom metadata support, batch ingestion capabilities, and schema migration. By the end of this epic, users can ingest documents through REST API endpoints, specify custom metadata fields, and verify successful ingestion through Neo4j.

---

## Stories in this Epic

### Story 2.1: Integrate RAG-Anything Library and Create Document Parsing Service
**As a** developer,
**I want** a containerized RAG-Anything parsing service that accepts documents and extracts structured content,
**so that** I can process multiple document formats consistently.

[Details in Story File: 2.1.integrate-rag-anything.md]

---

### Story 2.2: Implement Metadata Schema Definition and Validation
**As a** knowledge base administrator,
**I want** to define custom metadata fields for my documents,
**so that** I can filter and organize documents by domain-specific attributes.

[Details in Story File: 2.2.metadata-schema.md]

---

### Story 2.3: Create Document Ingestion API Endpoint with Metadata Support
**As a** RAG Engine user,
**I want** to upload documents via REST API with custom metadata,
**so that** I can populate my knowledge base programmatically.

[Details in Story File: 2.3.ingestion-api.md]

---

### Story 2.4: Implement Batch Document Ingestion and Progress Tracking
**As a** knowledge base administrator,
**I want** to upload multiple documents in a single batch operation,
**so that** I can efficiently populate large knowledge bases.

[Details in Story File: 2.4.batch-ingestion.md]

---

### Story 2.5: Create Entity Type Configuration and Pre-Ingestion Setup
**As a** domain specialist,
**I want** to specify expected entity types for my knowledge domain,
**so that** LightRAG extracts relevant entities during graph construction.

[Details in Story File: 2.5.entity-types.md]

---

### Story 2.6: Implement Document Management API (List, Retrieve, Delete)
**As a** RAG Engine user,
**I want** to list, retrieve details, and delete ingested documents,
**so that** I can manage my knowledge base content.

[Details in Story File: 2.6.document-management.md]

---

### Story 2.7: Implement Metadata Schema Migration and Reindexing
**As a** knowledge base administrator,
**I want** to update my metadata schema and reindex existing documents,
**so that** I can adapt the knowledge base to evolving organizational needs without redeployment.

[Details in Story File: 2.7.schema-migration.md]

---

## Epic Dependencies

**Depends On:**
- Epic 1: Foundation & Core Infrastructure (Neo4j, API service, logging)

**Blocks:**
- Epic 3: Graph-Based Retrieval & Knowledge Graph Construction (requires ingested documents)

---

## Epic Acceptance Criteria

1. ✅ RAG-Anything service integrated and parsing PDF, Markdown, HTML, Word, code files
2. ✅ Metadata schema configurable via `config/metadata-schema.yaml`
3. ✅ Document ingestion API endpoint `POST /api/v1/documents/ingest` functional
4. ✅ Batch ingestion API endpoint `POST /api/v1/documents/ingest/batch` handles 100+ files
5. ✅ Entity types configurable via `config/entity-types.yaml`
6. ✅ Document management API endpoints (list, retrieve, delete) operational
7. ✅ Metadata schema migration workflow tested with backward compatibility
8. ✅ Integration tests verify end-to-end document ingestion with metadata

---

## Technical Notes

### Key Technologies
- RAG-Anything Python library (latest)
- MinerU 2.0+ for document parsing
- Pydantic V2 for metadata validation
- FastAPI async endpoints for non-blocking ingestion
- Neo4j for storing document metadata and parsed content

### API Endpoints Created
- `POST /api/v1/documents/ingest` - Single document upload
- `POST /api/v1/documents/ingest/batch` - Batch document upload
- `GET /api/v1/documents/ingest/batch/{batch_id}/status` - Batch progress
- `GET /api/v1/documents` - List documents (with filters)
- `GET /api/v1/documents/{doc_id}` - Document details
- `DELETE /api/v1/documents/{doc_id}` - Delete document
- `GET /api/v1/config/entity-types` - Get entity types
- `POST /api/v1/config/entity-types` - Add entity type
- `PUT /api/v1/config/metadata-schema` - Update schema
- `POST /api/v1/documents/reindex` - Trigger reindexing

### Configuration Files
- `config/metadata-schema.yaml` - Custom metadata fields definition
- `config/entity-types.yaml` - Expected entity types for domain

### Critical Files Created
- `/services/rag-anything-integration/service.py` - RAG-Anything wrapper
- `/services/api/routers/documents.py` - Document API routes
- `/shared/models/metadata.py` - Pydantic metadata models
- `/shared/models/entity_types.py` - Entity type models

---

## Epic Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RAG-Anything parsing failures | Medium | High | Robust error handling, format validation, user documentation |
| Large file uploads (>50MB) | Medium | Medium | File size limits, streaming uploads, documentation |
| Metadata schema conflicts | Low | Medium | Backward compatibility validation, migration testing |
| Batch ingestion performance | Medium | Medium | Async processing, progress tracking, partial success support |

---

## Epic Definition of Done

- [ ] All 7 stories completed with acceptance criteria met
- [ ] Integration tests pass for all document formats (PDF, Markdown, HTML, Word, code)
- [ ] Metadata validation working with custom schemas
- [ ] Batch ingestion handles 100+ documents successfully
- [ ] Schema migration tested with backward compatibility
- [ ] API documentation updated with all endpoints
- [ ] Error handling comprehensive (file size, unsupported formats, validation errors)
- [ ] Demo: Ingest 10 documents → verify in Neo4j → delete → confirm cleanup

---

## Epic Metrics

- **Estimated Story Points:** 28 (based on 7 stories, ~4 points each)
- **Estimated Duration:** 2-3 weeks for solo developer
- **Key Performance Indicators:**
  - Document parsing success rate: >95%
  - Batch ingestion throughput: >10 documents/minute
  - Metadata validation error rate: <5%
  - API response time: <500ms for single ingestion (async accepted)

---

**Change Log:**

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-15 | 1.0 | Epic created from PRD | Sarah (PO Agent) |

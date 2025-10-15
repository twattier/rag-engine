# Epic 2: Multi-Format Document Ingestion Pipeline

**Epic Goal:** Integrate RAG-Anything for parsing multiple document formats (PDF, Markdown, HTML, Word, code files) with custom metadata support, batch ingestion capabilities, and schema migration. By the end of this epic, users can ingest documents through REST API endpoints, specify custom metadata fields, and verify successful ingestion through Neo4j.

## Story 2.1: Integrate RAG-Anything Library and Create Document Parsing Service

**As a** developer,
**I want** a containerized RAG-Anything parsing service that accepts documents and extracts structured content,
**so that** I can process multiple document formats consistently.

### Acceptance Criteria

1. `services/rag-anything-integration/` contains RAG-Anything integration service with FastAPI endpoints
2. Service exposes endpoint `POST /parse` accepting document upload with multipart/form-data
3. Supported formats: PDF, Markdown (.md), HTML, Microsoft Word (.doc, .docx), Python (.py), JavaScript (.js), TypeScript (.ts), Java (.java), plain text (.txt)
4. Parse endpoint returns structured JSON with extracted content: text blocks, images (as base64 or references), tables, equations
5. Service runs in Docker container with RAG-Anything dependencies installed
6. `docker-compose.yml` includes `rag-anything-integration` service configuration
7. Integration tests verify parsing of sample documents for each supported format
8. Error handling for unsupported formats returns 400 with clear error message

## Story 2.2: Implement Metadata Schema Definition and Validation

**As a** knowledge base administrator,
**I want** to define custom metadata fields for my documents,
**so that** I can filter and organize documents by domain-specific attributes.

### Acceptance Criteria

1. `shared/models/metadata.py` defines Pydantic models for metadata schema configuration
2. Schema supports field types: string, integer, date, boolean, tags (list of strings)
3. Schema definition file `config/metadata-schema.yaml` allows users to define custom fields with: field name, type, required/optional, default value, description
4. Example schema includes common fields: author, department, date_created, tags, project_name, category
5. API validates document metadata against schema on ingestion, returning 422 for invalid metadata
6. `.env.example` includes `METADATA_SCHEMA_PATH` configuration variable
7. Documentation in `docs/metadata-configuration.md` explains schema definition with examples

## Story 2.3: Create Document Ingestion API Endpoint with Metadata Support

**As a** RAG Engine user,
**I want** to upload documents via REST API with custom metadata,
**so that** I can populate my knowledge base programmatically.

### Acceptance Criteria

1. API service exposes `POST /api/v1/documents/ingest` endpoint accepting:
   - Document file (multipart/form-data)
   - Metadata JSON object (validated against schema)
   - Optional: expected_entity_types (list of domain-specific entity types)
2. Endpoint orchestrates: RAG-Anything parsing → store raw parsed content → queue for LightRAG processing (Epic 3 dependency)
3. Response includes: document_id (UUID), ingestion_status ("parsing", "queued"), metadata confirmation
4. Parsed document content stored in Neo4j as temporary nodes pending graph construction
5. API handles file size limits (configurable, default 50MB) and returns 413 for oversized files
6. Rate limiting implemented (configurable, default 10 requests/minute per API key)
7. OpenAPI documentation updated with ingestion endpoint specification and examples
8. Integration test successfully ingests sample PDF with metadata

## Story 2.4: Implement Batch Document Ingestion and Progress Tracking

**As a** knowledge base administrator,
**I want** to upload multiple documents in a single batch operation,
**so that** I can efficiently populate large knowledge bases.

### Acceptance Criteria

1. API endpoint `POST /api/v1/documents/ingest/batch` accepts:
   - Multiple document files (multipart/form-data, max 100 files per batch)
   - Optional: CSV/JSON file mapping filenames to metadata
2. Batch ingestion processes documents asynchronously, returning batch_id immediately
3. Endpoint `GET /api/v1/documents/ingest/batch/{batch_id}/status` returns:
   - total_documents, processed_count, failed_count, status ("in_progress", "completed", "partial_failure")
   - List of failed documents with error messages
4. Failed document ingestion doesn't block entire batch—partial success supported
5. Background task queue (using Python asyncio or simple queue) manages batch processing
6. Batch ingestion logs progress to structured logs for monitoring
7. Documentation in `docs/batch-ingestion.md` with CSV metadata format examples
8. Integration test verifies batch ingestion of 10 documents with mixed metadata

## Story 2.5: Create Entity Type Configuration and Pre-Ingestion Setup

**As a** domain specialist,
**I want** to specify expected entity types for my knowledge domain,
**so that** LightRAG extracts relevant entities during graph construction.

### Acceptance Criteria

1. Configuration file `config/entity-types.yaml` allows defining custom entity types with: type_name, description, examples
2. Default entity types provided: person, organization, concept, product, location, technology, event, document
3. Entity types configuration loaded at service startup and accessible via API
4. API endpoint `GET /api/v1/config/entity-types` returns currently configured entity types
5. API endpoint `POST /api/v1/config/entity-types` allows adding new entity types (persisted to config file)
6. Entity types passed to LightRAG during graph construction (Epic 3 integration point)
7. `.env.example` includes `ENTITY_TYPES_CONFIG_PATH` variable
8. Documentation in `docs/entity-configuration.md` with domain-specific examples (legal, medical, technical documentation)

## Story 2.6: Implement Document Management API (List, Retrieve, Delete)

**As a** RAG Engine user,
**I want** to list, retrieve details, and delete ingested documents,
**so that** I can manage my knowledge base content.

### Acceptance Criteria

1. API endpoint `GET /api/v1/documents` returns paginated list of documents with: document_id, filename, metadata, ingestion_date, status, size
2. Query parameters support filtering: metadata fields (e.g., `?department=engineering`), date ranges, status
3. API endpoint `GET /api/v1/documents/{document_id}` returns full document details including parsed content preview
4. API endpoint `DELETE /api/v1/documents/{document_id}` removes document and associated graph nodes/relationships from Neo4j
5. Delete operation is idempotent—deleting non-existent document returns 204 (no error)
6. Document listing supports pagination with `limit` and `offset` parameters (default limit: 50, max: 500)
7. Neo4j queries optimized with indexes on document_id and metadata fields
8. Integration tests verify list filtering, document retrieval, and deletion workflows

## Story 2.7: Implement Metadata Schema Migration and Reindexing

**As a** knowledge base administrator,
**I want** to update my metadata schema and reindex existing documents,
**so that** I can adapt the knowledge base to evolving organizational needs without redeployment.

### Acceptance Criteria

1. API endpoint `PUT /api/v1/config/metadata-schema` accepts updated metadata schema YAML/JSON and persists to `config/metadata-schema.yaml`

2. Schema validation ensures backward compatibility:
   - New fields must be optional or have defaults
   - Existing required fields cannot be removed
   - Field type changes rejected (breaking change)

3. Schema update triggers reindexing workflow:
   - Option 1 (immediate): Automatically reindex all documents in background
   - Option 2 (deferred): Mark schema as "pending reindex," user triggers manually

4. API endpoint `POST /api/v1/documents/reindex` triggers reindexing:
   - Accepts optional filters (document IDs, date ranges, metadata criteria)
   - Returns reindex_job_id for progress tracking
   - Reindexing updates document metadata fields without re-parsing content

5. API endpoint `GET /api/v1/documents/reindex/{job_id}/status` returns:
   - total_documents, processed_count, failed_count, status ("in_progress", "completed", "failed")
   - Estimated time remaining

6. Existing documents with missing new optional fields use schema defaults

7. Schema changes logged with timestamp, user, and change description to audit log

8. Documentation in `docs/schema-migration.md` explains:
   - When to use metadata schema updates
   - Backward compatibility requirements
   - Reindexing workflow and performance considerations
   - Examples of common schema evolutions

---
